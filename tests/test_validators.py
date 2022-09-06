import os
import sys
import tempfile
from pathlib import Path

import pytest
from fixer import fixer, validators


def test_convert_to_abs_path():
    relative_path = "test.txt"
    assert validators.convert_to_abs_path(
        relative_path) == os.path.join(os.getcwd(), relative_path)

    relative_path = "../test.txt"
    assert validators.convert_to_abs_path(
        relative_path) == str(Path.cwd().parent / "test.txt")

    absolute_path = "/foo/bar/baz/test.txt"
    assert validators.convert_to_abs_path(
        absolute_path) == os.path.join(os.getcwd(), absolute_path)


def test_check_db_file_exist(capsys):
    # corret
    opt = {"<DATABASE-FILE>": __file__}
    validators.check_db_file_exist(opt)

    # incorrect
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        opt = {"<DATABASE-FILE>": "/foo/bar/baz"}
        validators.check_db_file_exist(opt)

    captured = capsys.readouterr()
    assert captured.err == "<DATABASE-FILE> does not exist.\n"


def test_check_db_file_can_create(capsys):
    # corret (full-path)
    opt = {"<DATABASE-FILE>": tempfile.gettempdir() + "/test.db"}
    validators.check_db_file_can_create(opt)

    # incorrect
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        opt = {"<DATABASE-FILE>": "/test.db"}
        validators.check_db_file_can_create(opt)

    captured = capsys.readouterr()
    assert captured.err == "Can't create '/test.db'. The directory does not exist or does not have write permission.\n"


def test_check_csv_file_exist(capsys):
    # corret
    opt = {"<CSV-FILE>": __file__}
    validators.check_csv_file_exist(opt)

    # incorrect
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        opt = {"<CSV-FILE>": "/foo/bar/baz"}
        validators.check_csv_file_exist(opt)

    captured = capsys.readouterr()
    assert captured.err == "<CSV-FILE> does not exist.\n"


def test_check_jwt_file_exist(capsys):
    # corret
    opt = {"<JWT-FILE>": __file__}
    validators.check_jwt_file_exist(opt)

    # incorrect
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        opt = {"<JWT-FILE>": "/foo/bar/baz"}
        validators.check_jwt_file_exist(opt)

    captured = capsys.readouterr()
    assert captured.err == "<JWT-FILE> does not exist.\n"


def test_check_process_num(capsys):
    opt = {"--process": 16}
    validators.check_process_num(opt)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        opt = {"--process": "it-is-not-number"}
        validators.check_process_num(opt)

    captured = capsys.readouterr()
    assert captured.err == "--process must be numeric.\n"


def test_check_create_appuser_num(capsys):
    opt = {"--create-appuser-num": 32}
    validators.check_create_appuser_num(opt)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        opt = {"--process": "it-is-not-number"}
        validators.check_create_appuser_num(opt)

    captured = capsys.readouterr()
    assert captured.err == "--create-appuser-num must be numeric.\n"


def test_check_box_user_id(capsys):
    opt = {"<BOX-USER-ID>": 10242048096}
    validators.check_box_user_id(opt)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        opt = {"<BOX-USER-ID>": "is-is-not-number"}
        validators.check_box_user_id(opt)

    captured = capsys.readouterr()
    assert captured.err == "<BOX-USER-ID> must be numeric.\n"


def test_check_box_folder_id(capsys):
    opt = {"<BOX-FOLDER-ID>": 10242048096}
    validators.check_box_folder_id(opt)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        opt = {"<BOX-FOLDER-ID>": "is-is-not-number"}
        validators.check_box_folder_id(opt)

    captured = capsys.readouterr()
    assert captured.err == "<BOX-FOLDER-ID> must be numeric.\n"


def test_check_box_file_url(capsys):
    opt = {"--box-file-url": "ftp://example.com"}
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        validators.check_box_file_url(opt)

    captured = capsys.readouterr()
    assert captured.err == "--box-file-url must be URL.\n"

    opt = {"--box-file-url": "ALL YOUR BASE ARE BELONG TO US"}
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        validators.check_box_file_url(opt)

    captured = capsys.readouterr()
    assert captured.err == "--box-file-url must be URL.\n"

    opt = {"--box-file-url": "https://app.box.com/file/"}
    validators.check_box_file_url(opt)


def test_check_cert_and_private_key(capsys):
    opt = {
        "--cert": "test_assets/test_textfile.txt",
        "--private-key": ""
    }
    validators.check_cert_and_private_key(opt)
    opt = {
        "--cert": "",
        "--private-key": "test_assets/test_textfile.txt",
    }
    validators.check_cert_and_private_key(opt)

    opt = {
        "--cert": "./test_assets/test_textfile.txt",
        "--private-key": "./test_assets/test_textfile.txt",
    }
    validators.check_cert_and_private_key(opt)

    opt = {
        "--cert": "/file/not/exists",
        "--private-key": "./test_assets/test_textfile.txt",
    }

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        validators.check_cert_and_private_key(opt)

    captured = capsys.readouterr()
    assert captured.err == "--cert file does not exist.\n"

    opt = {
        "--cert": "./test_assets/test_textfile.txt",
        "--private-key": "/file/not/exists",
    }

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        validators.check_cert_and_private_key(opt)

    captured = capsys.readouterr()
    assert captured.err == "--private-key file does not exist.\n"


def test_validate_option(capsys, mocker):

    check_func_list = [
        "check_db_file_exist",
        "check_db_file_can_create",
        "check_csv_file_exist",
        "check_jwt_file_exist",
        "check_process_num",
        "check_create_appuser_num",
        "check_box_user_id",
    ]

    mocker.patch(f'validators.convert_to_abs_path',
                 side_effect=lambda x: None, return_value={})

    for check_function in check_func_list:
        mocker.patch(f'fixer.validators.{check_function}',
                     side_effect=lambda x: None, return_value={})

    opt = {
        '<DATABASE-FILE>': "/path/to/file",
        '<CSV-FILE>': "/path/to/file",
        '<JWT-FILE>': "/path/to/file",
        '<BOX-FOLDER-ID>': 1,
        '--box-file-url': "https://app.box.com/file/",
        '--create-appuser-num': 1,
        '--process': 1,
        '--skip-collaboration': True,
        '--skip-put-csv': True,
        '--cert': None,
        "--private-key": None,
        '--port': 8080,
    }

    mode_list = [
        'initialize-db',
        'import-csv',
        'initialize-service-account-directory',
        'create-appuser',
        'delete-appuser',
        'show-appuser-list',
        'show-service-account-info',
        'collaborate-and-put-csv',
        'fix',
        'start-webserver',
        'emergency-remove-collaborations',
    ]
    for choose_mode in mode_list:
        for mode in mode_list:
            opt[mode] = False
        opt[choose_mode] = True
        validators.validate_option(opt)
