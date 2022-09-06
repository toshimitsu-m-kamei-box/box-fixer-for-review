import sys
import uuid
from datetime import datetime

import consts
import utils
import sys


def main(opt):
    service_client = utils.get_client(opt)
    db = utils.get_db(opt)
    error_flg = False

    for i in range(int(opt["--create-appuser-num"])):
        try:
            appuser = service_client.create_user(
                name=f"Box fixer-{uuid.uuid4().hex[0:8]}")
            insert_appuser_to_appuser_table(db, appuser)
        except Exception as e:
            print(f'Error: {e}', file=sys.stderr)
            error_flg = True

    if error_flg:
        sys.exit(1)


def insert_appuser_to_appuser_table(db, appuser):
    table = db.get_table(consts.APP_USER_TABLENAME, primary_id="box_user_id")
    table.insert({
        'box_user_id': appuser.id,
        'name': appuser.name,
        'login': appuser.login,
        'created_at': datetime.now()
    })
