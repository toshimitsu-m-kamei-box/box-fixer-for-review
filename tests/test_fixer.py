from pathlib import Path

import pytest
from fixer import fixer as fixer_main
from fixer import consts, utils

MODE_LIST = [
    'modes.initialize_db',
    'modes.create_appuser',
    'modes.delete_appuser',
    'modes.show_appuser_list',
    'modes.show_service_account_info',
    'modes.fix',
]


def test_fixer_main(capsys, mocker):
    mocker.patch(f'docopt.docopt', return_value={})
    mocker.patch(f'validators.validate_option',
                 side_effect=None, return_value={})

    for mode in MODE_LIST:
        mocker.patch(f'{mode}.main', return_value=lambda x: None)
        mode_opt = mode.split(".")[1].replace("_", "-")
        print(f"mode:{mode_opt}")
        opt = {
            mode_opt: True,
            '--optcheck-only': False,
        }
        fixer_main.main(opt)


def test_optcheck_only(mocker):
    mocker.patch(f'docopt.docopt', return_value={})
    mocker.patch(f'validators.validate_option',
                 side_effect=None, return_value={})

    for mode in MODE_LIST:
        mocker.patch(f'{mode}.main', return_value=lambda x: None)
        mode_opt = mode.split(".")[1].replace("_", "-")
        print(f"mode:{mode_opt}")
        opt = {
            mode_opt: True,
            '--optcheck-only': True,
        }

        with pytest.raises(SystemExit) as pytest_wrapped_e:
            fixer_main.main(opt)
