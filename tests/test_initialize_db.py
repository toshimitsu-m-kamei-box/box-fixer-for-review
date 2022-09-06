from fixer.modes import initialize_db
from fixer import consts, utils
import pytest
from pathlib import Path
import uuid
import tempfile


def test_initialize_db_if_success():
    db_filename = Path(tempfile.gettempdir()) / \
        Path(f'test-{uuid.uuid4().hex[0:8]}.db')
    opt = {"<DATABASE-FILE>": db_filename}
    initialize_db.main(opt)

    db = utils.get_db(opt)
    for table_name, schema in consts.TABLE_SCHEMAS.items():
        assert db.has_table(table_name)

        table = db.get_table(table_name)
        for column_name in schema['columns'].keys():
            assert table.has_column(column_name)


def test_initialize_db_if_success_if_error(mocker):
    mocker.patch('fixer.modes.initialize_db._initialize_db',
                 side_effect=Exception('testException'))

    opt = {'<DATABASE-FILE>': 'no-exist-file'}

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        initialize_db.main(opt)
