import ssl
import time

import consts
import utils
from flask import Flask, render_template
from flask_httpauth import HTTPBasicAuth

app = Flask(
    __name__,
    template_folder='../templates',
    static_url_path='/static_files',
    static_folder='../static_files',
)
auth = HTTPBasicAuth()

SCOPES = [
    "base_explorer",
    "root_readonly",
    "item_download",
]

fixer_option = None

users = {
    "boxjpnusers": "Fixit!1234"
}


@auth.get_password
def get_pw(username):
    return users.get(username, None)


# For Let's encrypt challenge url
@app.route('/.well-known/acme-challenge/<filename>')
def well_known(filename):
    return render_template(filename)


@app.route('/')
@auth.login_required
def index():
    downscope_token_info = None

    for i in range(1, consts.WEBSERVER_RETRY_COUNT+1):
        try:
            service_client = utils.get_client(fixer_option)
            target_folder = service_client.folder("0")
            downscope_token_info = service_client.downscope_token(SCOPES, target_folder)
            break
        except  Exception as e:
            print(e)
            time.sleep(consts.WEBSERVER_RETRY_WAIT_TIME * i)

    return render_template(
        'index.html', access_token=downscope_token_info.access_token)


def main(opt):
    global fixer_option
    fixer_option = opt

    ssl_context = None
    if fixer_option.get("--cert", None) and fixer_option.get("--private-key", None):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.load_cert_chain(fixer_option["--cert"], fixer_option["--private-key"])
        print("SSL!")

    app.run(debug=True, host='0.0.0.0', port=opt["--port"], ssl_context=ssl_context)
