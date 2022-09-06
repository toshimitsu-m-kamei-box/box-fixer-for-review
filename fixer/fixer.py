#!/usr/bin/env python
# encoding: utf-8

"""Fixer
  Box Fixer

Usage:
  fixer initialize-db  <DATABASE-FILE> [-o|--optcheck-only] [-h|--help]
  fixer import-csv <DATABASE-FILE> <CSV-FILE> [-o|--optcheck-only] [-h|--help]
  fixer create-appuser <DATABASE-FILE> <JWT-FILE> [--create-appuser-num=<CREATE-APPUSER-NUM>] [-o|--optcheck-only] [-h|--help]
  fixer delete-appuser <DATABASE-FILE> <JWT-FILE> <BOX-USER-ID> [-o|--optcheck-only] [-h|--help]
  fixer initialize-service-account-directory <DATABASE-FILE> <JWT-FILE> [-o|--optcheck-only] [-h|--help]
  fixer show-appuser-list <DATABASE-FILE>[-o|--optcheck-only] [-h|--help]
  fixer show-service-account-info <JWT-FILE> [-o|--optcheck-only] [-h|--help]
  fixer fix <DATABASE-FILE> <JWT-FILE> <BOX-FOLDER-ID> [--process=<PROCESS-NUM>] [--box-file-url=<BOX-URL>] [-o|--optcheck-only] [-h|--help]
  fixer collaborate-and-put-csv <DATABASE-FILE> <JWT-FILE> <BOX-FOLDER-ID> [--skip-collaboration] [--skip-put-csv][-o|--optcheck-only][-h --help]
  fixer start-webserver <JWT-FILE> [--cert=<CERT-FILE>] [--private-key=<PRIVATE-KEY-FILE>] [--port=<PORT-NUM>] [-o|--optcheck-only] [-h|--help]
  fixer emergency-remove-collaborations <JWT-FILE> <BOX-FOLDER-ID> [-o|--optcheck-only][-h --help]


Options:
  CSV                                                 CSV File
  JWT-File                                            JWT File
  <DATABASE-FILE>                                     DATABASE File
  <BOX-USER-ID>                                       BOX-USER-ID
  <AUTHORIZATION-URL>                                 AUTHORIZATION-URL [default: http://localhost]
  --create-appuser-num=<CREATE-APPUSER-NUM            Create App User Number [default: 1]
  --box-file-url=<BOX-FILE-URL>                       Base box file url [default: https://app.box.com/file/]
  --process=<PROCESS-NUM>                             Number of Process [default: 1]
  --skip-collaboration                                Skip Collaborate to uploader_user
  --skip-put-csv                                      Skip Upload CSV
  --port=<PORT-NUM>                                   Web server port [default: 8080]
  -o, --optcheck-only                                 Only option check
  -h, --help                                          Show this help.
"""
import sys

from docopt import docopt
from loguru import logger

import validators
from modes import (collaborate_and_put_csv, create_appuser, delete_appuser,
                   emergency_remove_collaborations, fix, import_csv,
                   initialize_db, initialize_service_account_directory,
                   show_appuser_list, show_service_account_info, start_webserver)


def main(opt):
    validators.validate_option(opt)
    modes = {
        'initialize-db': initialize_db,
        'import-csv': import_csv,
        'initialize-service-account-directory': initialize_service_account_directory,
        'create-appuser': create_appuser,
        'delete-appuser': delete_appuser,
        'show-appuser-list': show_appuser_list,
        'show-service-account-info': show_service_account_info,
        'collaborate-and-put-csv': collaborate_and_put_csv,
        'start-webserver': start_webserver,
        'emergency-remove-collaborations': emergency_remove_collaborations,
        'fix': fix
    }

    if opt["--optcheck-only"]:
        print(opt, file=sys.stdout)
        sys.exit(0)

    for k, v in modes.items():
        if not opt.get(k, False):
            continue
        modes[k].main(opt)
        break


if __name__ == '__main__':
    opt = docopt(__doc__)
    main(opt)
