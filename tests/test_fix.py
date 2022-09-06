import logging
import multiprocessing
import queue
import sys
import uuid
from audioop import mul
from pathlib import Path

import freezegun
from fixer import consts, utils
from fixer.modes import fix
from loguru import logger


def test_true_gen():
    gen = fix.true_gen(1)
    assert gen.__next__() == True


def test_put_log():
    test_queue = queue.Queue()
    test_data = {"msg": "test message", "level": logging.INFO}
    fix.put_log(test_queue, test_data)
    queued_data = test_queue.get()
    assert queued_data['msg']['msg'] == test_data['msg']


def test_log_operation(capsys):
    logger.remove()
    logger.add(sys.stdout, format='{level} {message}')
    data = {"msg": "ALL YOUR BASE ARE BELONG TO US", "level": logging.INFO}
    fix.log_operation(data)
    captured = capsys.readouterr()
    assert captured.out == "INFO ALL YOUR BASE ARE BELONG TO US\n"


def test_db_opeartion(capsys, mocker):
    opt = {'<DATABASE-FILE>': ':memory:'}
    db = utils.get_db(opt)
    table_name = 'test-table'
    db.get_table(table_name)

    log_queue = multiprocessing.Queue()

    # Insert operation
    for i in range(1, 10 + 1):
        operation_data = {
            'table_name': table_name,
            'command': 'insert',
            'args': [{'name': f'testuser-{i}', 'age': i}]
        }
        fix.db_operation(db, operation_data, log_queue)

    # Select Operation
    for i in range(1, 10 + 1):
        operation_data = {
            'table_name': table_name,
            'command': 'find_one',
            'kwargs': {'age': {'=': i}}
        }
        result = fix.db_operation(db, operation_data, log_queue)
        assert result['name'] == f'testuser-{i}'
        assert result['age'] == i

    # Update
    for i in range(1, 10 + 1):
        operation_data = {
            'table_name': table_name,
            'command': 'update',
            'args': [{"id": i, "age": 100 + i}, ["id"]]
        }
        fix.db_operation(db, operation_data, log_queue)

    for i in range(1, 10 + 1):
        operation_data = {
            'table_name': table_name,
            'command': 'find_one',
            'kwargs': {'id': {'=': i}}
        }
        result = fix.db_operation(db, operation_data, log_queue)
        assert result['name'] == f'testuser-{i}'
        assert result['age'] == i + 100


def test_db_operation_if_error_occured(capsys, mocker):
    logger.remove()
    logger.add(sys.stdout, format='{level} {message}')

    opt = {'<DATABASE-FILE>': ':memory:'}
    db = utils.get_db(opt)
    table_name = 'test-table'
    db.get_table(table_name)

    log_queue = multiprocessing.Queue()

    # Corrupted data
    corrupted_operation_data = {"ALLYOURBASEARE": "BELONGTOUS", }
    fix.db_operation(db, corrupted_operation_data, log_queue)

    logging_data = log_queue.get()
    assert logging_data['level'] == logging.ERROR
    assert logging_data['msg'] == "Database operation error: 'table_name'"


def test_log_process_func_if_queue_exist(capsys, mocker):
    def true_gen_mock_for_log_process(system_status):
        for i in range(1):
            yield True

        system_status.value = consts.SystemStatus.AFTER_SHUTDOWN_DB.value
        while True:
            yield True

    log_queue = multiprocessing.Queue()
    system_status = multiprocessing.Value(
        'i', consts.SystemStatus.WORKING.value)

    for i in range(1, 10 + 1):
        log_queue.put(
            {"msg": f"test-log-process-func {i}", "level": logging.INFO})

    logger.remove()
    logger.add(sys.stdout, format='{level} {message}')

    mocker.patch('fixer.modes.fix.true_gen',
                 side_effect=true_gen_mock_for_log_process)
    fix.log_process_func(system_status, log_queue)

    captured = capsys.readouterr()

    for line in (
        "INFO test-log-process-func 1\n"
        "INFO test-log-process-func 2\n"
        "INFO test-log-process-func 3\n"
        "INFO test-log-process-func 4\n"
        "INFO test-log-process-func 5\n"
        "INFO test-log-process-func 6\n"
        "INFO test-log-process-func 7\n"
        "INFO test-log-process-func 8\n"
        "INFO test-log-process-func 9\n"
        "INFO test-log-process-func 10\n"
    ):
        assert line in captured.out


def test_log_process_func_if_queue_does_not_exist(capsys, mocker):
    def true_gen_mock_for_log_process(system_status):
        for i in range(1):
            yield True

        system_status.value = consts.SystemStatus.AFTER_SHUTDOWN_DB.value
        while True:
            yield True

    system_status = multiprocessing.Value(
        'i', consts.SystemStatus.WORKING.value)
    log_queue = multiprocessing.Queue()
    logger.remove()
    logger.add(sys.stdout, format='{level} {message}')

    mocker.patch('fixer.modes.fix.true_gen',
                 side_effect=true_gen_mock_for_log_process)
    fix.log_process_func(system_status, log_queue)


def test_get_appuser_access_token_operation(capsys, mocker, benchmark):
    opt = {
        '<DATABASE-FILE>': ':memory:',
        '<JWT-FILE>': './test_assets/test-jwt-file.json'
    }
    manager = multiprocessing.Manager()

    appuser_list = manager.list()
    for i in range(1, 100 + 1):
        appuser_list.append({"box_user_id": i, "login": uuid.uuid4(
        ).hex[0:8], "login": uuid.uuid4().hex[0:8]})

    log_queue = manager.Queue()
    access_token_dict_lock = manager.Lock()
    access_token_dict = manager.dict()

    access_token_list = [uuid.uuid4().hex[0:8]
                         for i in range(len(appuser_list))]

    def _access_token_gen():
        for access_token in access_token_list:
            yield access_token

    access_token_gen = _access_token_gen()
    mocker.patch("boxsdk.auth.jwt_auth.JWTAuth.authenticate_app_user",
                 side_effect=access_token_gen.__next__)
    mocker.patch("boxsdk.object.user.User.get", return_value=None)

    for i in range(len(appuser_list) - 1):
        access_token, _ = fix.get_appuser_access_token_operation(
            opt, log_queue, appuser_list, access_token_dict, access_token_dict_lock)
        assert access_token in access_token_list

    assert len(access_token_dict) == len(appuser_list)
    assert log_queue.get()[
        "msg"] == "Obtain access tokens for all Appusers for initial startup."

    while not log_queue.empty():
        assert "access token has been obtained" in log_queue.get()["msg"]


def test_get_appuser_access_token_operation_if_token_expired(
        capsys, mocker, benchmark):
    opt = {
        '<DATABASE-FILE>': ':memory:',
        '<JWT-FILE>': './test_assets/test-jwt-file.json'
    }
    manager = multiprocessing.Manager()

    appuser_list = manager.list()
    for i in range(1, 100 + 1):
        appuser_list.append({"box_user_id": i, "login": uuid.uuid4().hex[0:8]})

    log_queue = manager.Queue()
    access_token_dict_lock = manager.Lock()
    access_token_dict = manager.dict()

    def gen_uuid():
        return uuid.uuid4().hex[0:8]

    mocker.patch(
        "boxsdk.auth.jwt_auth.JWTAuth.authenticate_app_user", side_effect=gen_uuid)
    mocker.patch("boxsdk.object.user.User.get", return_value=None)

    # First take
    with freezegun.freeze_time('2000-01-01 00:00:00'):
        _ = fix.get_appuser_access_token_operation(
            opt, log_queue, appuser_list, access_token_dict, access_token_dict_lock)

        # Second take
        for i in range(len(appuser_list)):
            _ = fix.get_appuser_access_token_operation(
                opt, log_queue, appuser_list, access_token_dict, access_token_dict_lock)

        assert log_queue.get()[
            "msg"] == "Obtain access tokens for all Appusers for initial startup."
        while not log_queue.empty():
            assert "access token has been obtained" in log_queue.get()["msg"]

    # Safe
    with freezegun.freeze_time('2000-01-01 00:45:00'):
        for i in range(len(appuser_list)):
            _ = fix.get_appuser_access_token_operation(
                opt, log_queue, appuser_list, access_token_dict, access_token_dict_lock)
        assert log_queue.empty()

    # All out!!
    with freezegun.freeze_time('2000-01-01 00:45:01'):
        for i in range(len(appuser_list)):
            _ = fix.get_appuser_access_token_operation(
                opt, log_queue, appuser_list, access_token_dict, access_token_dict_lock)
        assert not log_queue.empty()
        while not log_queue.empty():
            data = log_queue.get_nowait()
            assert "access token is about to expire. A new one will be issued." in data["msg"]
