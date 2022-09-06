import consts
import utils
import sys


def main(opt):
    try:
        db = _initialize_db(opt)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


def _initialize_db(opt):
    db = utils.get_db(opt)

    db.begin()
    for table_name, schema in consts.TABLE_SCHEMAS.items():
        table = db.get_table(table_name, primary_id=schema['primary_id'])
        for column_name, definition in schema['columns'].items():
            table.create_column(
                column_name, definition['struct'], **definition['constraints'])
    db.commit()
    utils.close_db(db)
