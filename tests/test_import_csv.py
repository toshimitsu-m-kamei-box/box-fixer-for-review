import csv
import tempfile
import uuid
from pathlib import Path

import pytest
from fixer import utils, consts
from fixer.modes import import_csv, initialize_db


def test_main_if_corrupted_db(capsys, mocker):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        import_csv.main({"<DATABASE-FILE>": "./test_assets/test_textfile.txt"})


def test_import_csv_if_correct(capsys, mocker):
    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {"<DATABASE-FILE>": db_filename}
    initialize_db.main(opt)

    opt = {"<DATABASE-FILE>": db_filename,
           "<CSV-FILE>": "./test_assets/test.csv"}
    import_csv.main(opt)

    db = utils.get_db(opt)
    with open("./test_assets/test.csv", "r") as fh:
        reader = csv.DictReader(fh)
        for data in reader:
            result = db[consts.FIX_LIST_TABLENAME].find_one(
                restored_file_id=data["restored_file_id"], upload_user_id=data["upload_user_id"])
            assert result is not None


def test_import_csv_if_confict_data(capsys, mocker):
    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {"<DATABASE-FILE>": db_filename}
    initialize_db.main(opt)

    opt = {"<DATABASE-FILE>": db_filename,
           "<CSV-FILE>": "./test_assets/test_conflict.csv"}
    import_csv.main(opt)

    captured = capsys.readouterr()
    assert "Data already exists in db. Line: 1 {'file_id': '1002511206202'" in captured.err


def test_import_csv_if_corrupted_db(capsys, mocker):
    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {"<DATABASE-FILE>": db_filename}
    initialize_db.main(opt)
    db = utils.get_db(opt)
    db[consts.FIX_LIST_TABLENAME].drop()

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        import_csv.main(opt)


def test_import_corrupted_header_csv(capsys, mocker):
    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {"<DATABASE-FILE>": db_filename}
    initialize_db.main(opt)
    opt = {"<DATABASE-FILE>": db_filename,
           "<CSV-FILE>": "./test_assets/test_corrupted_header.csv"}
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        import_csv.main(opt)
