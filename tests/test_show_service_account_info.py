import pytest
from fixer import utils
from fixer.modes import show_service_account_info


class ServiceAccount:
    id = 1
    login = "test-service-account@boxdeveloper.com"


def test_show_service_account_info_if_error(capsys, mocker):

    mocker.patch('boxsdk.object.user.User.get', return_value=ServiceAccount())
    opt = {"<JWT-FILE>": "/foo/bar/no-exist-file.json"}
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        show_service_account_info.main(opt)

    captured = capsys.readouterr()
    assert captured.err == "Error: [Errno 2] No such file or directory: '/foo/bar/no-exist-file.json'\n"


def test_show_service_account_info_if_success(capsys, mocker):

    mocker.patch('boxsdk.object.user.User.get', return_value=ServiceAccount())

    opt = {"<JWT-FILE>": "./test_assets/test-jwt-file.json"}
    show_service_account_info.main(opt)

    captured = capsys.readouterr()
    assert captured.out == (
        "ID: 1\n"
        "Login: test-service-account@boxdeveloper.com\n"
    )
