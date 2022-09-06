import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest
from fixer import consts, utils
from fixer.modes import create_appuser, delete_appuser, initialize_db


class AppUser():
    id = 1
    login = "test-app-user@boxdeveloper.com"
    name = "test-app-user"


def test_delete_appuser_from_appuser_table_if_user_exist_in_db(mocker):
    # Initialize DB
    test_appuser = AppUser()

    mocker.patch('boxsdk.client.Client.create_user', return_value=test_appuser)
    mocker.patch('boxsdk.object.user.User.delete',
                 return_value=None, side_effect=None)

    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {
        '<JWT-FILE>': './test_assets/test-jwt-file.json',
        '<DATABASE-FILE>': db_filename,
        '--create-appuser-num': 1,
    }

    initialize_db.main(opt)
    create_appuser.main(opt)

    opt = {
        '<JWT-FILE>': './test_assets/test-jwt-file.json',
        '<DATABASE-FILE>': db_filename,
        '<BOX-USER-ID>': 1,
    }
    delete_appuser.main(opt)

    db = utils.get_db(opt)
    assert db[consts.APP_USER_TABLENAME].count() == 0


def test_delete_appuser_from_appuser_table_if_user_does_not_exist_in_db(
        capsys):
    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {"<DATABASE-FILE>": db_filename}
    initialize_db.main(opt)

    # Delete from db
    opt = {
        '<JWT-FILE>': './test_assets/test-jwt-file.json',
        '<DATABASE-FILE>': db_filename,
        '<BOX-USER-ID>': 1,
    }

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        delete_appuser.main(opt)

    captured = capsys.readouterr()
    assert captured.err == "Not found 1 in database.\n"


def test_delete_appuser_from_appuser_table_if_user_does_not_exist_in_box(
        capsys, mocker):
    test_appuser = AppUser()

    mocker.patch('boxsdk.client.Client.create_user', return_value=test_appuser)
    mocker.patch('boxsdk.object.user.User.delete',
                 return_value=None, side_effect=Exception("IT-IS-TEST"))

    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {
        '<JWT-FILE>': './test_assets/test-jwt-file.json',
        '<DATABASE-FILE>': db_filename,
        '--create-appuser-num': 1,
    }

    initialize_db.main(opt)
    create_appuser.main(opt)

    opt = {
        '<JWT-FILE>': './test_assets/test-jwt-file.json',
        '<DATABASE-FILE>': db_filename,
        '<BOX-USER-ID>': 1,
    }

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        delete_appuser.main(opt)

    captured = capsys.readouterr()
    assert captured.err == "An error occurred while deleting a user from the Box: IT-IS-TEST\n"
