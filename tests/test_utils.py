import logging
import os
import sys
import tempfile
import uuid
from pathlib import Path

import dataset
from boxsdk import Client
from fixer import consts, fixer, utils
from fixer.modes import initialize_db


def test_logger_func(capsys):
    fixer.logger.remove()
    fixer.logger.add(sys.stdout, format='{level} {message}')

    consts.LOGGER_FUNCS[logging.INFO]("INFO MSG")
    consts.LOGGER_FUNCS[logging.DEBUG]("DEBUG MSG")
    consts.LOGGER_FUNCS[logging.WARNING]("WARNING MSG")
    consts.LOGGER_FUNCS[logging.ERROR]("ERROR MSG")
    consts.LOGGER_FUNCS[logging.CRITICAL]("CRITICAL MSG")
    captured = capsys.readouterr()

    assert captured.out == (
        'INFO INFO MSG\n'
        'DEBUG DEBUG MSG\n'
        'WARNING WARNING MSG\n'
        'ERROR ERROR MSG\n'
        'CRITICAL CRITICAL MSG\n'
    )


def test_get_db():
    opt = {"<DATABASE-FILE>": ":memory:"}
    db = utils.get_db(opt)
    table = db.get_table("Test")
    test_data = {"test": "All your base are belong to us."}

    table.insert(test_data)
    for data in table.all():
        assert data['test'] == test_data['test']
    assert isinstance(db, dataset.Database)


def test_close_db():
    opt = {"<DATABASE-FILE>": ":memory:"}
    db = utils.get_db(opt)
    utils.close_db(db)


def test_check_table_and_column_if_correct(capsys):
    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {
        '<DATABASE-FILE>': db_filename,
    }
    initialize_db._initialize_db(opt)

    db = utils.get_db(opt)
    assert True == utils.check_db_table_and_column(db)


def test_check_table_and_column_if_incorrect(capsys):
    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {
        '<DATABASE-FILE>': db_filename,
    }
    initialize_db._initialize_db(opt)

    # drop table
    db = utils.get_db(opt)
    db[consts.APP_USER_TABLENAME].drop()

    corrupted_table = db.get_table(consts.APP_USER_TABLENAME)
    corrupted_table.insert(
        {"ALL": "YOUR", "BASE": "ARE", "BELONG": "TO", "US": "."})
    assert False == utils.check_db_table_and_column(db)
    captured = capsys.readouterr()
    assert captured.err == (
        "Error: APP_USERS table does not have 'box_user_id' column.\n"
        "Error: APP_USERS table does not have 'login' column.\n"
        "Error: APP_USERS table does not have 'name' column.\n"
        "Error: APP_USERS table does not have 'created_at' column.\n"
    )


def test_get_auth():
    opt = {"<JWT-FILE>": "./test_assets/test-jwt-file.json"}
    utils.get_auth(opt)


def test_get_auth_benchmark(benchmark):
    opt = {"<JWT-FILE>": "./test_assets/test-jwt-file.json"}
    benchmark.pedantic(utils.get_auth, args=[opt, ], rounds=100, iterations=3)


def test_get_client():
    opt = {"<JWT-FILE>": "./test_assets/test-jwt-file.json"}
    utils.get_client(opt)


def test_get_client_with_access_token():
    assert isinstance(utils.get_client_with_access_token("test-access-token"), Client)
