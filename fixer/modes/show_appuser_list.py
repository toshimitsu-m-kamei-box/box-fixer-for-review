import sys

import consts
import utils
from tabulate import tabulate
import uuid


def main(opt):
    db = utils.get_db(opt)
    user_list = list()
    for user in db[consts.APP_USER_TABLENAME].all():
        user_list.append(user)

    if not user_list:
        print("No appuser found.", file=sys.stdout)
        sys.exit(0)

    print(
        tabulate(user_list, headers="keys", tablefmt="fancy_grid",
                 stralign='center', numalign='left'),
        file=sys.stdout
    )
    sys.exit(0)
