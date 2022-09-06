import sys
import time
from itertools import repeat
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Manager, Pool, get_logger

import consts
import utils


def remove_collaboration(args):
    folder_id, access_token = args[0], args[1]
    service_client = utils.get_client_with_access_token(access_token)
    collaboration_list = None
    success_flg = False

    for i in range(1, consts.EMERGENCY_REMOVE_COLLABORATION_RETRY_COUNT + 1):
        try:
            collaboration_list = service_client.folder(
                folder_id).get_collaborations()
            success_flg = True
            break
        except Exception as e:
            pass

    if not success_flg:
        print(
            f"💀 Failed to get collaboration list. Folder ID: {folder_id}", file=sys.stdout)
        time.sleep(consts.EMERGENCY_REMOVE_COLLABORATION_BASIC_WAIT_TIME * i)
        return

    can_not_remove_collaboration_list = list()
    for c in collaboration_list:
        for i in range(
                1, consts.EMERGENCY_REMOVE_COLLABORATION_RETRY_COUNT + 1):
            try:
                c.delete()
                break
            except BaseException:
                pass
        if not success_flg:
            can_not_remove_collaboration_list.append(c)

    if can_not_remove_collaboration_list:
        print(
            f"💀 Failed to remove all collaboration. Folder ID: {folder_id}", file=sys.stdout)
        return

    print(
        f"🎉 Collaboration remove success. Folder ID: {folder_id}", file=sys.stdout)


def main(opt):
    access_token = utils.get_auth(opt).authenticate_instance()
    service_client = utils.get_client(opt)

    folder_id_list = list()
    try:
        for item in service_client.folder(opt["<BOX-FOLDER-ID>"]).get_items():
            if not item.type == "folder":
                continue
            folder_id_list.append(item.id)
    except Exception as e:
        print(f"💀 Failed to acquire folder contents. exit..", file=sys.stdout)
        sys.exit(1)

    with Pool(processes=1) as p:
        p.map(remove_collaboration, zip(folder_id_list, repeat(access_token)))
