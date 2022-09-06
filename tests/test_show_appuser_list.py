import tempfile
import uuid
from pathlib import Path

import freezegun
import pytest
from fixer import consts, utils
from fixer.modes import create_appuser, initialize_db, show_appuser_list


class AppUser():
    def __init__(self, id_num, login_str, name_str):
        self.id = id_num
        self.login = login_str
        self.name = name_str


@freezegun.freeze_time('2000-01-01 00:00:00')
def test_show_appuser_list_if_appuser_exit_in_db(capsys, mocker):
    # Initialize DB
    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {
        '<JWT-FILE>': './test_assets/test-jwt-file.json',
        '<DATABASE-FILE>': db_filename,
    }
    initialize_db.main(opt)

    opt = {
        '<JWT-FILE>': './test_assets/test-jwt-file.json',
        '<DATABASE-FILE>': db_filename,
        '--create-appuser-num': 1,
    }

    for i in range(1, 4):
        test_appuser = AppUser(i, f'{i}-login', name_str=f'{i}-name')
        mocker.patch('boxsdk.client.Client.create_user',
                     return_value=test_appuser)
        create_appuser.main(opt)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        show_appuser_list.main(opt)

    captured = capsys.readouterr()
    assert captured.out == (
        '╒═══════════════╤═════════╤════════╤═════════════════════╕\n'
        '│ box_user_id   │  login  │  name  │     created_at      │\n'
        '╞═══════════════╪═════════╪════════╪═════════════════════╡\n'
        '│ 1             │ 1-login │ 1-name │ 2000-01-01 00:00:00 │\n'
        '├───────────────┼─────────┼────────┼─────────────────────┤\n'
        '│ 2             │ 2-login │ 2-name │ 2000-01-01 00:00:00 │\n'
        '├───────────────┼─────────┼────────┼─────────────────────┤\n'
        '│ 3             │ 3-login │ 3-name │ 2000-01-01 00:00:00 │\n'
        '╘═══════════════╧═════════╧════════╧═════════════════════╛\n'
    )


def test_show_appuser_list_if_appuser_does_not_exit_in_db(capsys, mocker):
    # Initialize DB
    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {
        '<JWT-FILE>': './test_assets/test-jwt-file.json',
        '<DATABASE-FILE>': db_filename,
    }
    initialize_db.main(opt)

    opt = {
        '<JWT-FILE>': './test_assets/test-jwt-file.json',
        '<DATABASE-FILE>': db_filename,
        '--create-appuser-num': 1,
    }

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        show_appuser_list.main(opt)

    captured = capsys.readouterr()
    assert captured.out == "No appuser found.\n"
