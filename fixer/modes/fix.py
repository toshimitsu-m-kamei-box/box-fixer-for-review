import logging
import queue
import random
import signal
import sys
import time
import uuid
import warnings
from datetime import datetime
from multiprocessing import Manager, Process

import consts
import utils
from boxsdk.exception import BoxAPIException
from boxsdk.object.collaboration import CollaborationRole
from dateutil.relativedelta import relativedelta
from loguru import logger


def true_gen(system_status):
    # It exists for unit testing. See test_fix.py, etc. for details.
    while True:
        yield True

# -----------------------------------------------------------------------------


def put_log(log_queue, msg, level=logging.INFO):
    log_queue.put({'msg': msg, 'level': level})


def log_operation(data):
    log_func = consts.LOGGER_FUNCS[data['level']]
    log_func(data['msg'])


def log_process_func(system_status, log_queue):
    import sys
    logger.remove()
    logger.add('./logs/fixer.log',
               format='{time} {level} {message}', rotation="24h")
    logger.add(sys.stdout, format='{time} {level} {message}')

    signal.signal(signal.SIGINT, signal.SIG_IGN)

    wg = true_gen(system_status)
    while wg.__next__():
        time.sleep(consts.PROCESS_BASIC_WAIT_TIME)
        if system_status.value == consts.SystemStatus.AFTER_SHUTDOWN_DB.value:
            break
        try:
            data = log_queue.get_nowait()
            log_operation(data)
        except queue.Empty as e:
            pass

    time.sleep(3)
    while not log_queue.empty():
        data = log_queue.get_nowait()
        log_operation(data)

# -----------------------------------------------------------------------------


def get_appuser_access_token_operation(opt,
                                       log_queue,
                                       appuser_list,
                                       access_token_dict,
                                       access_token_dict_lock):
    with access_token_dict_lock:
        def _get_and_store_fresh_appuser_access_token(box_user_id):
            access_token = utils.get_appuesr_token(opt, box_user_id)
            access_token_dict[access_token] = {
                "retrieve_datetime": datetime.now(),
                "box_user_id": box_user_id,
            }
            return access_token

        if len(access_token_dict) <= 0:
            put_log(
                log_queue, f'Obtain access tokens for all Appusers for initial startup.', level=logging.INFO)
            for appuser in appuser_list:
                _ = _get_and_store_fresh_appuser_access_token(
                    appuser["box_user_id"])
                put_log(
                    log_queue, f"{appuser['login']}'s access token has been obtained.", level=logging.INFO)

        access_token = random.choice([t for t in access_token_dict.keys()])
        if datetime.now() > access_token_dict[access_token]["retrieve_datetime"] + \
                relativedelta(seconds=consts.NEXT_REFRESH_ACCESS_TOKEN_SEC):
            box_user_id = access_token_dict[access_token]["box_user_id"]
            del (access_token_dict[access_token])
            access_token = _get_and_store_fresh_appuser_access_token(
                box_user_id)
            put_log(
                log_queue, f'Appuser({box_user_id}) access token is about to expire. A new one will be issued.', level=logging.INFO)

    return access_token, access_token_dict[access_token]["box_user_id"]

# -----------------------------------------------------------------------------


def put_db_command(db_queue, table_name, command, args=[], kwargs={}):
    db_queue.put({"table_name": table_name, "command": command,
                 "args": args, "kwargs": kwargs})


def db_operation(db, data, log_queue):
    try:
        db_func = getattr(db[data['table_name']], data['command'])
        db_args = data.get('args', list())
        db_kwargs = data.get('kwargs', dict())

        db.begin()
        result = db_func(*db_args, **db_kwargs)
        db.commit()
        return result

    except Exception as err:
        put_log(log_queue, f'Database operation error: {err}', logging.ERROR)


def db_process_func(system_status, opt, db_queue, log_queue):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    db = utils.get_db(opt)
    wg = true_gen(system_status)

    while wg.__next__():

        if system_status.value == consts.SystemStatus.PREPARE.value:
            time.sleep(consts.PROCESS_BASIC_WAIT_TIME)
            continue

        if system_status.value == consts.SystemStatus.AFTER_SHUTDOWN_FIXER_PROCESS.value:
            break

        try:
            data = db_queue.get_nowait()
            db_operation(db, data, log_queue)

        except queue.Empty as e:
            pass

    utils.close_db(db)


def change_working_status(db_queue, fix_id, working_status):
    data = {
        "id": fix_id,
        "working_status": working_status.value,
        "updated_at": datetime.now(),
    }

    put_db_command(db_queue, consts.FIX_LIST_TABLENAME,
                   "update", args=[data, ["id"]])


def change_working_status_to_complete(
        db_queue, fix_id, copy_folder_id, copy_folder_name, copy_file_id):
    data = {
        "id": fix_id,
        "working_status": consts.WorkingStatus.COMPLETE.value,
        "copy_folder_id": copy_folder_id,
        "copy_folder_name": copy_folder_name,
        "copy_file_id": copy_file_id,
        "updated_at": datetime.now(),
    }
    put_db_command(db_queue, consts.FIX_LIST_TABLENAME,
                   "update", args=[data, ["id"]])


def create_root_directory_cache(
        process_num, log_queue, root_folder, directory_cache):
    put_log(
        log_queue, f"[Process-{process_num}] build directory cache", logging.INFO)
    for folder in root_folder.get_items():
        directory_cache[folder.name] = {
            "folder_id": folder.id, "child_folders": dict()}
    put_log(
        log_queue, f"[Process-{process_num}] build directory cache complete.", logging.INFO)


def get_or_create_upload_user_folder(
        process_num, log_queue, client, upload_user_email, root_folder, directory_cache):
    target_user_cache = directory_cache.get(upload_user_email, dict())
    upload_user_folder = None

    if folder_id := target_user_cache.get("folder_id", None):
        upload_user_folder = client.folder(folder_id)
    else:
        for folder in root_folder.get_folders(
                fields=["id", "name", "type"]).get_items():
            if folder.type == "folder" and folder.name == upload_user_email:
                upload_user_folder = folder
                directory_cache[upload_user_email] = {
                    "folder_id": folder.id, "child_folders": dict()}
                break

    if not upload_user_folder:
        put_log(
            log_queue, f"[Process-{process_num}] upload_user_folder '{upload_user_email}' not found in root folder. Creating...", logging.DEBUG)
        try:
            upload_user_folder = root_folder.create_subfolder(
                upload_user_email)
            directory_cache[upload_user_email] = {
                "folder_id": folder.id,
                "child_folders": dict(),
            }

        except Exception as e:
            put_log(
                log_queue, f"[Process-{process_num}] Can't create '{upload_user_email}' upload_user_folder in root folder!: {e}", logging.ERROR)
            raise e

    return upload_user_folder


def get_or_create_owner_folder_in_upload_user_folder(
        process_num, log_queue, client, upload_user_folder, upload_user_email, folder_owner_email, directory_cache):
    target_user_cache = directory_cache.get(upload_user_email, dict())
    owner_folder_in_upload_user_folder = None

    if folder_id := target_user_cache.get(
            "child_folders", {}).get(folder_owner_email):
        owner_folder_in_upload_user_folder = client.folder(folder_id)
    else:
        for folder in upload_user_folder.get_items(
                fields=["id", "name", "type"]):
            if folder.type == "folder" and folder.name == folder_owner_email:
                owner_folder_in_upload_user_folder = folder
                directory_cache[upload_user_email]["child_folders"][folder_owner_email] = folder.id

    if not owner_folder_in_upload_user_folder:
        put_log(
            log_queue, f"[Process-{process_num}] {upload_user_email}'s owner_folder_in_upload_user_folder ({folder_owner_email}) not found. creating...", logging.INFO)
        try:
            owner_folder_in_upload_user_folder = upload_user_folder.create_subfolder(
                folder_owner_email)
            directory_cache[upload_user_email][folder_owner_email] = owner_folder_in_upload_user_folder.id

        except Exception as e:
            raise Exception(
                f"[Process-{process_num}] Can't create '{folder_owner_email}' owner_folder_in_upload_user_folder!: {e}")

    return owner_folder_in_upload_user_folder


def fixer_process_func(original_process_num,
                       opt,
                       system_status,
                       db_queue,
                       log_queue,
                       fix_queue,
                       appuser_list,
                       directory_cache,
                       directory_cache_lock,
                       access_token_dict,
                       access_token_dict_lock):
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    wg = true_gen(system_status)
    while wg.__next__():
        time.sleep(consts.PROCESS_BASIC_WAIT_TIME)

        process_num = f"{original_process_num} UID: {uuid.uuid4().hex[0:8]}"

        if system_status.value == consts.SystemStatus.PREPARE.value:
            time.sleep(consts.PROCESS_BASIC_WAIT_TIME)
            continue

        if fix_queue.empty():
            put_log(
                log_queue, f'[Process-{process_num}] Fix queue is empty. exit...', logging.INFO)
            break

        if system_status.value == consts.SystemStatus.SHUTDOWN_START.value:
            put_log(
                log_queue, f'[Process-{process_num}] End of working!', logging.INFO)
            break

        client = None
        try:
            access_token, app_user_id = get_appuser_access_token_operation(
                opt, log_queue, appuser_list, access_token_dict, access_token_dict_lock)
            client = utils.get_client_with_access_token(access_token)

        except Exception as e:
            put_log(
                log_queue, f"[Process-{process_num}] Can't create box client!: {e}", logging.ERROR)
            continue

        fix_data = None
        try:
            fix_data = fix_queue.get_nowait()
        except queue.Empty:
            continue

        # get upload_user folder & owner folder in upload_user folder
        """
        {
            "test1@example.com": {
                "folder_id": xxxxx,
                "child_folders": {
                    "owner@example.com": yyyyy
                }
            }
        }
        """

        # get folders
        root_folder = client.folder(opt["<BOX-FOLDER-ID>"])
        upload_user_folder = None
        owner_folder_in_upload_user_folder = None

        upload_user_email = fix_data["uploader_email"]
        folder_owner_email = fix_data["login"]
        folder_owner_id = fix_data["user_id"]
        restored_file_id = fix_data["restored_file_id"]
        file_name = fix_data["file_name"]

        with directory_cache_lock:
            if len(directory_cache) == 0:
                try:
                    create_root_directory_cache(
                        process_num, log_queue, root_folder, directory_cache)
                except Exception as e:
                    continue

            try:
                upload_user_folder = get_or_create_upload_user_folder(
                    process_num, log_queue, client, upload_user_email, root_folder, directory_cache)

                if upload_user_folder:
                    put_log(
                        log_queue, f"[Process-{process_num}]👍 upload_user_folder '{upload_user_email}' found. folder ID: {upload_user_folder.object_id}", logging.DEBUG)
                else:
                    raise Exception(
                        f"[Process-{process_num}]💀 Can't get or create upload_user_folder '{upload_user_email}'")
            except Exception as e:
                put_log(log_queue, str(e), logging.ERROR)
                continue

            try:
                owner_folder_in_upload_user_folder = get_or_create_owner_folder_in_upload_user_folder(
                    process_num, log_queue, client, upload_user_folder, upload_user_email, folder_owner_email, directory_cache)

                if owner_folder_in_upload_user_folder:
                    put_log(
                        log_queue, f"[Process-{process_num}]👍 owner_folder_in_upload_user_folder {folder_owner_email} found in {upload_user_email}. Folder ID: {owner_folder_in_upload_user_folder.id}", logging.DEBUG)
                else:
                    raise Exception(
                        f"[Process-{process_num}]💀 Can't get or create owner_folder_in_upload_user_folder {folder_owner_email} in {upload_user_email}")

            except Exception as e:
                put_log(log_queue, str(e), logging.ERROR)
                continue

        collaboration = None
        target_file = None

        # File exist in the box?
        success_flg = False
        for i in range(1, consts.FIX_PROCESS_RETRY_COUNT + 1):
            try:
                service_client = utils.get_client(opt)
                managed_user = service_client.user(folder_owner_id).get()
                app_user = service_client.user(app_user_id).get()
                target_file = service_client.as_user(
                    managed_user).file(restored_file_id)
                collaboration = target_file.collaborate(
                    app_user, CollaborationRole.EDITOR)
                success_flg = True
                put_log(
                    log_queue,
                    f"[Process-{process_num}]👍 Create appuser collaborator to {file_name}({restored_file_id})",
                    logging.DEBUG
                )

                break

            except Exception as e:
                if isinstance(e, BoxAPIException) and hasattr(
                        e, "code") and e.code == "user_already_collaborator":
                    success_flg = True
                    break

                put_log(
                    log_queue,
                    f"[Process-{process_num}]⚠️ Can't create appuser collaborator to {file_name}({restored_file_id}). Retry({i})! Error: {e}",
                    logging.WARNING
                )
                time.sleep(consts.FIX_PROCESS_WAIT_FOR_COLLABORATE_TIME * i)

        if not success_flg:
            put_log(
                log_queue,
                f"[Process-{process_num}]💀 Can't create appuser collaboration. Gave up this work",
                logging.CRITICAL
            )
            change_working_status(
                db_queue, fix_data["id"], consts.WorkingStatus.CAN_NOT_ADD_COLLABORATION)
            continue

        # Copy to owner_folder_in_puload_user_folder
        success_flg = False
        copied_file = None
        for i in range(1, consts.FIX_PROCESS_RETRY_COUNT + 1):
            try:
                # copy from appuser_client
                copied_file = client.file(restored_file_id).copy(
                    parent_folder=owner_folder_in_upload_user_folder)
                success_flg = True
                put_log(
                    log_queue,
                    f"[Process-{process_num}]👍 Copy to {file_name}({restored_file_id}) to owner_folder_in_upload_user_folder({owner_folder_in_upload_user_folder.id}).",
                    logging.DEBUG
                )
                break

            except Exception as e:
                if isinstance(e, BoxAPIException) and hasattr(
                        e, "status") and e.status == 409:
                    copied_file = client.file(
                        e.context_info["conflicts"]["id"]).get()

                    success_flg = True
                    break

                put_log(
                    log_queue,
                    f"[Process-{process_num}]⚠️ Can't copy to {file_name}({restored_file_id}) to owner_folder_in_upload_user_folder({owner_folder_in_upload_user_folder.id}) Retry({i})! Error: {e}",
                    logging.WARNING
                )
                time.sleep(consts.FIX_PROCESS_WAIT_FOR_COLLABORATE_TIME * i)
                continue

        if not success_flg:
            put_log(
                log_queue,
                f"[Process-{process_num}]💀 Can't copy to {file_name}({restored_file_id}) to owner_folder_in_upload_user_folder({owner_folder_in_upload_user_folder.id}). Gave up this work.",
                logging.CRITICAL
            )
            change_working_status(
                db_queue, fix_data["id"], consts.WorkingStatus.CAN_NOT_COPY)
            continue

        # Remove Collaboration
        appuesr_id_list = [appuser["box_user_id"] for appuser in appuser_list]
        success_flg = False

        for i in range(1, consts.FIX_PROCESS_RETRY_COUNT + 1):
            try:
                for c in service_client.as_user(managed_user).file(
                        restored_file_id).get_collaborations():
                    if c.response_object["accessible_by"]["id"] in appuesr_id_list:
                        c.delete()

                success_flg = True
                put_log(
                    log_queue,
                    f"[Process-{process_num}]👍 Remove collaboration from {file_name}({restored_file_id}.",
                    logging.DEBUG
                )
                break
            except Exception as e:
                put_log(
                    log_queue,
                    f"[Process-{process_num}]⚠️ Can't remove collaboration from {file_name}({restored_file_id}. Retry({i})!. Error: {e}",
                    logging.WARNING
                )
                time.sleep(consts.FIX_PROCESS_WAIT_FOR_COLLABORATE_TIME * i)
                continue

        if not success_flg:
            put_log(
                log_queue,
                f"[Process-{process_num}]💀 Can't remove collaboration from {file_name}({restored_file_id}. Gave up this work",
                logging.WARNING
            )
            change_working_status(
                db_queue, fix_data["id"], consts.WorkingStatus.CAN_NOT_REMOVE_COLLABORATION)
            continue

        change_working_status_to_complete(
            db_queue, fix_data["id"], owner_folder_in_upload_user_folder.id, folder_owner_email, copied_file.id)
        put_log(
            log_queue,
            f"[Process-{process_num}]🎉 File copy and remove collaboratoin complete!! {file_name}({restored_file_id} copy to {upload_user_email}'s {folder_owner_email} folder!)",
            logging.INFO,
        )


def main(opt):
    def _core(manager):
        fixer_process_list = list()
        log_queue = manager.Queue()
        db_queue = manager.Queue()
        fix_queue = manager.Queue()
        directory_cache = manager.dict()
        directory_cache_lock = manager.Lock()

        system_status = manager.Value('i', consts.SystemStatus.PREPARE.value)

        access_token_dict = manager.dict()
        access_token_dict_lock = manager.Lock()
        appuser_list = manager.list()

        def shutdown_handler(signo, frame):
            if system_status.value == consts.SystemStatus.WORKING.value:
                system_status.value = consts.SystemStatus.SHUTDOWN_START.value
                put_log(log_queue, 'Shutdown start..', logging.INFO)

        # Set Signal Handling
        signal.signal(signal.SIGINT, shutdown_handler)

        # Get Working queue & appuser_list
        db = utils.get_db(opt)

        for appuser in db[consts.APP_USER_TABLENAME].all():
            appuser_list.append(appuser)

        for fix_data in db[consts.FIX_LIST_TABLENAME].find(
                working_status={"!=": consts.WorkingStatus.COMPLETE.value}):
            fix_queue.put(fix_data)

        utils.close_db(db)

        # Prepare and start Log process & DB process
        log_process = Process(target=log_process_func,
                              args=(system_status, log_queue,))
        db_process = Process(target=db_process_func, args=(
            system_status, opt, db_queue, log_queue,))
        log_process.start()
        db_process.start()

        # Prepare and start fixer process
        fixer_process_func_args = [
            opt,
            system_status,
            db_queue,
            log_queue,
            fix_queue,
            appuser_list,
            directory_cache,
            directory_cache_lock,
            access_token_dict,
            access_token_dict_lock
        ]
        for i in range(1, int(opt['--process']) + 1):
            fixer_process = Process(
                target=fixer_process_func, args=(i, *fixer_process_func_args))
            fixer_process_list.append(fixer_process)
            fixer_process.start()

        time.sleep(consts.SHUTDOWN_BASIC_WAIT_TIME)
        system_status.value = consts.SystemStatus.WORKING.value
        put_log(log_queue, "Fixer Process start.")

        for fixer_process in fixer_process_list:
            fixer_process.join()

        put_log(log_queue, 'Shutdown of the fixer process is complete.')
        time.sleep(consts.SHUTDOWN_BASIC_WAIT_TIME)
        system_status.value = consts.SystemStatus.AFTER_SHUTDOWN_FIXER_PROCESS.value

        db_process.join()
        put_log(log_queue, 'Shutdown of the DB process is complete.')
        time.sleep(consts.SHUTDOWN_BASIC_WAIT_TIME)
        system_status.value = consts.SystemStatus.AFTER_SHUTDOWN_DB.value

        log_process.join()
        logger.info('Shutdown of the log process is complete.')
        time.sleep(consts.SHUTDOWN_BASIC_WAIT_TIME)
        system_status.value = consts.SystemStatus.AFTER_SHUTDOWN_LOG.value

        logger.info('All Process Shutdown complete. Now Halting.')
        time.sleep(consts.SHUTDOWN_BASIC_WAIT_TIME)
        system_status.value = consts.SystemStatus.HALT.value

    # Has service account root folder?
    warnings.simplefilter('ignore')
    servlice_client = utils.get_client(opt)

    try:
        servlice_client.folder(opt["<BOX-FOLDER-ID>"]).get()
    except Exception as e:
        print("Target Boxfolder does not exist. Exit", file=sys.stderr)
        sys.exit(1)

    with Manager() as manager:
        _core(manager)
