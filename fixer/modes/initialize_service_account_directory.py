import sys
from datetime import datetime

import consts
import utils
from boxsdk.object.collaboration import CollaborationRole


def main(opt):
    try:
        db = utils.get_db(opt)
        if not utils.check_db_table_and_column(db):
            raise Exception()
    except Exception as e:
        print(f"Can't open or incorrect <DATABASE-FILE>. {e}", file=sys.stdout)
        sys.exit(1)

    service_client = utils.get_client(opt)
    service_account = service_client.user().get()
    service_account.update_info(data={"space_amount": -1})

    folder_owner_list = [
        o for o in db[consts.FIX_LIST_TABLENAME].distinct('login', 'user_id')]

    uploader_user_list = [
        u for u in db[consts.FIX_LIST_TABLENAME].distinct('upload_user_id', 'uploader_email')]

    # Create Service Account Folder
    root_folder = service_client.folder(0).create_subfolder(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(
        f"Service Account root folder created! folder ID: {root_folder.id}", file=sys.stdout)

    # create uploader_user_folders:
    for uploader_user in uploader_user_list:
        root_folder.create_subfolder(uploader_user["uploader_email"])

    print(f"Uploader users folder created.", file=sys.stdout)

    # Add appusers
    for appuser_data in db[consts.APP_USER_TABLENAME].all():
        appuser = service_client.user(appuser_data["box_user_id"])
        root_folder.collaborate(appuser, CollaborationRole.EDITOR)

    print(f"Service account folder initialize complete", file=sys.stdout)
