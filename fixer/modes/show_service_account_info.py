import utils
import sys
import pytest


def main(opt):
    try:
        service_client = utils.get_client(opt)
        service_account = service_client.user().get()
        print(f'ID: {service_account.id}')
        print(f'Login: {service_account.login}')

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
