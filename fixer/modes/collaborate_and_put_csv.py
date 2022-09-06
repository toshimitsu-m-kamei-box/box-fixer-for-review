import csv
import io
import sys
from urllib.parse import urljoin

import consts
import utils
from boxsdk.exception import BoxAPIException
from boxsdk.object.collaboration import CollaborationRole
from loguru import logger


CSV_SETTINGS = {
    'delimiter': ',',
    'doublequote': True,
    'lineterminator': '\r\n',
    'quotechar': '"',
    'skipinitialspace': True,
    'quoting': csv.QUOTE_MINIMAL,
    'strict': True
}


CSV_FIELD_NAMES = [
    "file_id",
    "original_file_id",
    "original_folder_name",
    "original_folder_path",
    "folder_name",
    "file_name",
    "file_url",
]


def main(opt):
    logger.add('./logs/collaborate_and_put_csv.log',
               format='{time} {level} {message}', rotation="24h")
    logger.add(sys.stdout, format='{time} {level} {message}')

    service_client = utils.get_client(opt)
    db = utils.get_db(opt)

    user_folder_cache = dict()
    for item in service_client.folder(opt["<BOX-FOLDER-ID>"]).get_items():
        if item.type != "folder":
            continue
        user_folder_cache[item.name] = {"folder_id": item.id}

    for folder_and_uploader_email_name, folder in user_folder_cache.items():
        # Upload CSV
        target_folder_id = user_folder_cache[folder_and_uploader_email_name]["folder_id"]

        if not opt["--skip-put-csv"]:
            with io.StringIO() as fh:
                writer = csv.DictWriter(
                    fh, fieldnames=CSV_FIELD_NAMES, **CSV_SETTINGS)
                writer.writeheader()
                for data in db[consts.FIX_LIST_TABLENAME].find(
                        uploader_email=folder_and_uploader_email_name):

                    csv_data = {
                        "file_id": data["copy_file_id"],
                        "original_file_id": data["original_file_id"],
                        "original_folder_path": data["original_path_names"],
                        "original_folder_name": data["original_folder_name"],
                        "folder_name": data["copy_folder_name"],
                        "file_name": data["file_name"],
                        "file_url": urljoin(opt["--box-file-url"], str(data["copy_file_id"]))
                    }
                    writer.writerow(csv_data)

                success_flg = False
                for i in range(1, 10 + 1):
                    exist_file_id = None

                    try:
                        service_client.folder(
                            target_folder_id).upload_stream(fh, "ファイルリスト.csv")
                        logger.info(
                            f"⬆ Upload csv file to {folder_and_uploader_email_name}.")
                        success_flg = True
                        break

                    except Exception as e:
                        if hasattr(e, "context_info"):
                            exist_file_id = e.context_info["conflicts"]["id"]
                        else:
                            logger.error(
                                f"⚠ Can't upload csv file to {folder_and_uploader_email_name}. Retry({i}) Error: {e}")
                            continue

                    try:
                        service_client.file(
                            exist_file_id).update_contents_with_stream(fh)
                        logger.info(
                            f"⬆ Update csv file to {folder_and_uploader_email_name}.")
                        success_flg = True
                        break

                    except Exception as e:
                        logger.error(
                            f"⚠ Can't content update csv file to {folder_and_uploader_email_name}. Retry({i}) Error: {e}")
                        continue

                if not success_flg:
                    logger.critical(
                        f"💀 Can't content upload/update csv file to {folder_and_uploader_email_name}. ")
                    continue

        if not opt["--skip-collaboration"]:
            # Collaborate to uploader_user
            success_flg = False
            for i in range(1, 10 + 1):
                try:
                    service_client.folder(target_folder_id).collaborate_with_login(
                        folder_and_uploader_email_name, CollaborationRole.VIEWER)
                    success_flg = True
                    break

                except Exception as e:
                    if isinstance(e, BoxAPIException) and hasattr(
                            e, "code") and e.code == "user_already_collaborator":
                        success_flg = True
                        break
                    logger.error(
                        f"⚠ Can't collaborate {folder_and_uploader_email_name} user folder. Retry({i}) Error: {e}")
                    continue

            if not success_flg:
                logger.critical(
                    f"💀 Can't content upload/update csv file to {folder_and_uploader_email_name} user foder. ")
                continue
            else:
                logger.info(
                    f"🤝 Collaborate '{folder_and_uploader_email_name}'user to {folder_and_uploader_email_name} user foder!")
