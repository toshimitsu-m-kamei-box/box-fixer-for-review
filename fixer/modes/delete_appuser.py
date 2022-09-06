import sys

import consts
import utils


class AppUserNotFound(Exception):
    ...


def main(opt):
    box_user_id = opt["<BOX-USER-ID>"]
    try:
        delete_appuser_from_appuser_table(opt, box_user_id)
    except Exception as e:
        print(f'Not found {box_user_id} in database.', file=sys.stderr)
        sys.exit(1)

    try:
        delete_appuser_from_box(opt, box_user_id)
    except Exception as e:
        print(e)
        print(
            f'An error occurred while deleting a user from the Box: {e}', file=sys.stderr)
        sys.exit(1)


def delete_appuser_from_appuser_table(opt, box_user_id):
    db = utils.get_db(opt)
    table = db[consts.APP_USER_TABLENAME]
    user = table.find_one(box_user_id=box_user_id)

    if not user:
        raise AppUserNotFound()

    table.delete(box_user_id=box_user_id)
    utils.close_db(db)


def delete_appuser_from_box(opt, box_user_id):
    service_client = utils.get_client(opt)
    service_client.user(box_user_id).delete()
