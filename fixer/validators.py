import os
import sys
import re


URL_REGEX = re.compile(
    r'^(?:http)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


def convert_to_abs_path(path):
    if not path:
        return None

    if not os.path.dirname(path):
        path = os.path.join(os.getcwd(), path)
    return os.path.abspath(path)


def check_db_file_exist(opt):
    if not os.path.isfile(opt['<DATABASE-FILE>']):
        print('<DATABASE-FILE> does not exist.', file=sys.stderr)
        sys.exit(1)


def check_db_file_can_create(opt):
    dir_path = os.path.dirname(opt['<DATABASE-FILE>'])
    if not os.access(dir_path, os.W_OK):
        print(
            f"Can't create '{opt['<DATABASE-FILE>']}'. "
            'The directory does not exist or does not have write permission.',
            file=sys.stderr
        )
        sys.exit(1)


def check_csv_file_exist(opt):
    if not os.path.isfile(opt['<CSV-FILE>']):
        print('<CSV-FILE> does not exist.', file=sys.stderr)
        sys.exit(1)


def check_jwt_file_exist(opt):
    if not os.path.isfile(opt['<JWT-FILE>']):
        print('<JWT-FILE> does not exist.', file=sys.stderr)
        sys.exit(1)


def check_process_num(opt):
    try:
        int(opt['--process'])
    except Exception as e:
        print('--process must be numeric.', file=sys.stderr)
        sys.exit(1)


def check_create_appuser_num(opt):
    try:
        int(opt['--create-appuser-num'])
    except Exception as e:
        print('--create-appuser-num must be numeric.', file=sys.stderr)
        sys.exit(1)


def check_box_user_id(opt):
    try:
        int(opt['<BOX-USER-ID>'])
    except Exception as e:
        print('<BOX-USER-ID> must be numeric.', file=sys.stderr)
        sys.exit(1)


def check_box_folder_id(opt):
    try:
        int(opt['<BOX-FOLDER-ID>'])
    except Exception as e:
        print('<BOX-FOLDER-ID> must be numeric.', file=sys.stderr)
        sys.exit(1)


def check_port_num(opt):
    try:
        int(opt['--port'])
    except Exception as e:
        print('--port must be numeric.', file=sys.stderr)
        sys.exit(1)


def check_box_file_url(opt):
    result = re.match(URL_REGEX, opt["--box-file-url"])
    if not result:
        print("--box-file-url must be URL.", file=sys.stderr)
        sys.exit(1)


def check_cert_and_private_key(opt):
    if not all([opt["--cert"], opt["--private-key"]]):
        return

    if not os.path.isfile(opt['--cert']):
        print("--cert file does not exist.", file=sys.stderr)
        sys.exit(1)


    if not os.path.isfile(opt['--private-key']):
        print("--private-key file does not exist.", file=sys.stderr)
        sys.exit(1)


def validate_option(opt):
    check_funcs = {
        'initialize-db': [check_db_file_can_create],
        'import-csv': [check_db_file_exist, check_csv_file_exist],
        'initialize-service-account-directory': [check_db_file_exist, check_jwt_file_exist, ],
        'create-appuser': [check_db_file_exist, check_jwt_file_exist, check_create_appuser_num, ],
        'delete-appuser': [check_db_file_exist, check_jwt_file_exist, check_box_user_id, ],
        'show-appuser-list': [check_db_file_exist],
        'show-service-account-info': [check_jwt_file_exist],
        'fix': [check_db_file_exist, check_jwt_file_exist, check_box_folder_id, check_process_num, ],
        'collaborate-and-put-csv': [check_db_file_exist, check_jwt_file_exist, check_box_folder_id, check_process_num, check_box_file_url],
        'start-webserver': [check_jwt_file_exist, check_cert_and_private_key, check_port_num],
        'emergency-remove-collaborations': [check_jwt_file_exist, check_box_folder_id],
    }

    for key in ("<DATABASE-FILE>", "<CSV-FILE>", "<JWT-FILE>", "--cert", "--private-key"):
        if path := opt[key]:
            opt[key] = convert_to_abs_path(opt[key])

    for key in check_funcs.keys():
        if not opt[key]:
            continue
        [f(opt) for f in check_funcs[key]]
        break
