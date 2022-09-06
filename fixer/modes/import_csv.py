import csv
import sys
from datetime import datetime

import consts
import utils

"""
file_id -> オリジナルのFile ID
user_id -> 所有者(フォルダオーナー)
login -> 所有者(フォルダオーナー)の名前
restored_file_id -> 今回のコピー対象ファイル
uploader_user_id -> SAに掘るフォルダ名
"""


def check_csv_data(csv_data):
    if not utils.check_csv_headers(csv_data):
        print(f'Incorrect <CSV-FILE>', file=sys.stdout)
        sys.exit(1)


def main(opt):
    try:
        db = utils.get_db(opt)
        if not utils.check_db_table_and_column(db):
            raise Exception()

    except Exception as e:
        print(f"Can't open or incorrect <DATABASE-FILE>. {e}", file=sys.stdout)
        sys.exit(1)

    csv_data_list = list()
    with open(opt["<CSV-FILE>"]) as fh:
        reader = csv.DictReader(fh)
        for data in reader:
            check_csv_data(data)
            csv_data_list.append(data)

    now = datetime.now()

    db.begin()
    for i, csv_data in enumerate(csv_data_list):
        table = db[consts.FIX_LIST_TABLENAME]

        if table.find_one(
                restored_file_id=csv_data["restored_file_id"], upload_user_id=csv_data["upload_user_id"]):
            print(
                f"Data already exists in db. Line: {i} {csv_data}", file=sys.stderr)
            print("-" * 80, file=sys.stderr)

        insert_data = dict()
        for key in consts.REQUIRED_CSV_COLUMNS:
            insert_data[key] = csv_data[key]

        insert_data["original_file_id"] = csv_data["file_id"]
        insert_data["original_path_names"] = csv_data["path_names"]
        insert_data["original_folder_name"] = csv_data["folder_name"]
        insert_data['created_at'] = now
        insert_data['updated_at'] = now
        insert_data['working_status'] = consts.WorkingStatus.BEFORE_PROCESS.value

        table.insert(insert_data)
    db.commit()
    utils.close_db(db)
