import logging

import dataset
from loguru import logger
from enum import Enum


class SystemStatus(Enum):
    HALT = 0
    PREPARE = 1
    WORKING = 2
    SHUTDOWN_START = 3
    AFTER_SHUTDOWN_FIXER_PROCESS = 4
    AFTER_SHUTDOWN_DB = 5
    AFTER_SHUTDOWN_LOG = 6


class WorkingStatus(Enum):
    BEFORE_PROCESS = 0
    CAN_NOT_PREPARED_UPLOAD_USER_FOLDER = 1
    CAN_NOT_PREPARED_UPLOAD_USER_IN_OWNER_FOLDER = 2
    CAN_NOT_ADD_COLLABORATION = 3
    FILE_ALREADY_EXIST_WHEN_FILE_COPY = 4
    CAN_NOT_COPY = 5
    CAN_NOT_REMOVE_COLLABORATION = 6
    COMPLETE = 100


APP_USER_TABLENAME = "APP_USERS"
FIX_LIST_TABLENAME = "FIX_LIST"

TABLE_SCHEMAS = {
    APP_USER_TABLENAME: {
        'primary_id': 'box_user_id',
        'columns': {
            'box_user_id': {
                'struct': dataset.database.Types.integer,
                'constraints': {
                    'nullable': False,
                    # 'unique': True,
                }
            },
            'login': {
                'struct': dataset.database.Types.text,
                'constraints': {
                    'nullable': False,
                    # 'unique': True,
                }
            },
            'name': {
                'struct': dataset.database.Types.text,
                'constraints': {
                    'nullable': False,
                    # 'unique': True,
                }
            },
            'created_at': {
                'struct': dataset.database.Types.text,
                'constraints': {'nullable': False, }
            }
        },
    },

    FIX_LIST_TABLENAME: {
        'primary_id': 'id',
        'columns': {
            'restored_file_id': {
                'struct': dataset.database.Types.integer,
                'constraints': {'nullable': False, }
            },
            'file_name': {
                'struct': dataset.database.Types.text,
                'constraints': {'nullable': False, }
            },
            'original_file_id': {
                'struct': dataset.database.Types.integer,
                'constraints': {'nullable': False, }
            },
            'original_path_names': {
                'struct': dataset.database.Types.text,
                'constraints': {'nullable': False, }
            },
            'original_folder_name': {
                'struct': dataset.database.Types.text,
                'constraints': {'nullable': False, }
            },
            'user_id': {
                'struct': dataset.database.Types.integer,
                'constraints': {'nullable': False, }
            },
            'login': {
                'struct': dataset.database.Types.text,
                'constraints': {'nullable': False, }
            },
            'upload_user_id': {
                'struct': dataset.database.Types.integer,
                'constraints': {'nullable': False, }
            },
            'uploader_email': {
                'struct': dataset.database.Types.text,
                'constraints': {'nullable': False, }
            },
            'working_status': {
                'struct': dataset.database.Types.integer,
                'constraints': {'nullable': False, }
            },
            'copy_file_id': {
                'struct': dataset.database.Types.integer,
                'constraints': {'nullable': True, }
            },
            'copy_folder_id': {
                'struct': dataset.database.Types.integer,
                'constraints': {'nullable': True, }
            },

            'copy_folder_name': {
                'struct': dataset.database.Types.text,
                'constraints': {'nullable': True, }
            },

            'created_at': {
                'struct': dataset.database.Types.datetime,
                'constraints': {'nullable': False, }
            },
            'updated_at': {
                'struct': dataset.database.Types.datetime,
                'constraints': {'nullable': False, }
            }
        }
    }
}


REQUIRED_CSV_COLUMNS = (
    "restored_file_id",
    "login",
    "file_name",
    "user_id",
    "upload_user_id",
    "uploader_email",
)

FIX_PROCESS_RETRY_COUNT = 10
FIX_PROCESS_RETRY_WAIT_TIME = 3
FIX_PROCESS_DB_RETRY_COUNT = 10

FIX_PROCESS_WAIT_FOR_COLLABORATE_TIME = 3
PROCESS_BASIC_WAIT_TIME = 0.01
SHUTDOWN_BASIC_WAIT_TIME = 1.0
NEXT_REFRESH_ACCESS_TOKEN_SEC = 60 * 45

WEBSERVER_RETRY_COUNT = 10
WEBSERVER_RETRY_WAIT_TIME = 1

EMERGENCY_REMOVE_COLLABORATION_RETRY_COUNT = 10
EMERGENCY_REMOVE_COLLABORATION_BASIC_WAIT_TIME = 1


LOGGER_FUNCS = {
    logging.INFO: logger.info,
    logging.DEBUG: logger.debug,
    logging.INFO: logger.info,
    logging.WARNING: logger.warning,
    logging.ERROR: logger.error,
    logging.CRITICAL: logger.critical,
}
