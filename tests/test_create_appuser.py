import tempfile
import uuid
from pathlib import Path

import pytest
from fixer import consts, utils
from fixer.modes import create_appuser, initialize_db


class AppUser:
    id = 1
    login = "testuser@boxdeveloper.com"
    name = "test-app-user"


def test_create_appuser_if_success(mocker):
    test_appuser = AppUser()
    mocker.patch('boxsdk.client.Client.create_user', return_value=test_appuser)
    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {
        '<JWT-FILE>': './test_assets/test-jwt-file.json',
        '<DATABASE-FILE>': db_filename,
        '--create-appuser-num': 1
    }
    initialize_db.main(opt)
    create_appuser.main(opt)

    db = utils.get_db(opt)
    appuser = db[consts.APP_USER_TABLENAME].find_one(box_user_id=1)

    assert appuser['box_user_id'] == test_appuser.id
    assert appuser['login'] == test_appuser.login
    assert appuser['name'] == 'test-app-user'


def test_create_appuser_if_error(capsys):
    opt = {
        "<JWT-FILE>": './test_assets/test-jwt-file.json',
        "<DATABASE-FILE>": ":memory",
        "--create-appuser-num": 1
    }
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        create_appuser.main(opt)
