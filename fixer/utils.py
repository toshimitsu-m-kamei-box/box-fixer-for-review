import sys

import dataset
from boxsdk import Client, JWTAuth, OAuth2

import consts


def get_db(opt):
    return dataset.connect(
        f"sqlite:///{opt['<DATABASE-FILE>']}",
    )


def close_db(db):
    db.executable.invalidate()
    db.executable.engine.dispose()
    db.close()


def check_db_table_and_column(db):
    success_flg = True
    for table_name, definition in consts.TABLE_SCHEMAS.items():
        for column_name, column_definition in definition['columns'].items():
            if not db[table_name].has_column(column_name):
                success_flg = False
                print(
                    f"Error: {table_name} table does not have '{column_name}' column.", file=sys.stderr)

    return success_flg


def check_csv_headers(csv_data):
    success_flg = True
    for column_name in consts.TABLE_SCHEMAS[consts.FIX_LIST_TABLENAME]["columns"].keys(
    ):
        if not csv_data.get(
                column_name, False) and column_name in consts.REQUIRED_CSV_COLUMNS:
            success_flg = False
            print(
                f"Error: incorrect csv data: {column_name} does not exist.", file=sys.stderr)

    return success_flg


def get_client_with_access_token(access_token):
    return Client(OAuth2(client_id="", client_secret="",
                  access_token=access_token))


def get_auth(opt, box_user=None):
    auth = JWTAuth.from_settings_file(opt["<JWT-FILE>"], user=box_user)
    return auth


def get_client(opt, box_user=None):
    return Client(get_auth(opt, box_user=box_user))


def get_appuesr_token(opt, box_user_id):
    sa_client = get_client(opt)
    appuser = sa_client.user(box_user_id).get()
    auth = get_auth(opt, box_user=appuser)
    return auth.authenticate_app_user()
