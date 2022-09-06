import tempfile
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from fixer import consts, utils
from fixer.modes import initialize_db, initialize_service_account_directory


class BoxUser:
    id = 1
    def get(*args, **kwargs):
        return BoxUser()

    def update_info(*args, **kwargs):
        return None


class BoxFolder:
    id = 1
    def create_subfolder(*args, **kwargs):
        return BoxFolder()

    def collaborate(*args, **kwargs):
        ...


def test_main_if_corrupted_db(mocker):
    # DB Not initialized!
    opt = {
        "<JWT-FILE>": "./test_assets/test-jwt-file.json",
        "<DATABASE-FILE>": ":memory:"
    }

    mocker.patch('fixer.modes.initialize_db._initialize_db',
                 side_effect=Exception('testException'))

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        initialize_service_account_directory.main(opt)


def test_main(mocker):
    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {
        "<DATABASE-FILE>": db_filename,
        "<JWT-FILE>": "./test_assets/test-jwt-file.json",
    }
    initialize_db.main(opt)

    # Insert test data
    db = utils.get_db(opt)
    db[consts.APP_USER_TABLENAME].insert({
        "box_user_id": 1,
        "login": "test-appuser@boxdeveloper.com",
        "name": "test-appuser",
        "created_at": datetime.now(),
    })

    db[consts.FIX_LIST_TABLENAME].insert({
        "restored_file_id": 1,
        "file_name": "test_file",
        "original_file_id": 1,
        "original_path_names": "/original/file/path",
        "original_folder_name": "Original Folder Name",
        "user_id": 1,
        "login": "folder-owner@example.com",
        "upload_user_id": 2,
        "uploader_email": "upload@example.com",
        "working_status": consts.WorkingStatus.BEFORE_PROCESS.value,
        "copy_file_id": None,
        "copy_folder_id": None,
        "copy_folder_name": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    })

    mocker.patch('boxsdk.client.Client.user', return_value=BoxUser())
    mocker.patch('boxsdk.client.Client.folder', return_value=BoxFolder())

    initialize_service_account_directory.main(opt)
