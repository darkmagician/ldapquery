from ldap3 import Server, Connection, ALL, MODIFY_REPLACE, MODIFY_ADD, MODIFY_DELETE
from flask import request
from flask import jsonify
from flask import Flask
from flask import json
import traceback
import os
import threading
import gradio as gr


def getENV(key, defaultVal=None):
    if defaultVal:
        return os.getenv(key, default=defaultVal)
    val = os.getenv(key)
    if val:
        return val
    raise Exception(f'env {key} is not configured')


# Environments
HTTP_PORT = getENV('HTTP_PORT', 4084)
GRADIO_HTTP_PORT = getENV('GRADIO_HTTP_PORT', 4085)
LDAP_SERVER = getENV('LDAP_SERVER')
LDAP_USER = getENV('LDAP_USER')
LDAP_PASS = getENV('LDAP_PASS')
LDAP_BASE = getENV('LDAP_BASE')
SEARCH_LIMIT = getENV('SEARCH_LIMIT', 10)

filters = ['cn', 'sAMAccountName', 'displayName', 'uid', 'mail']
attributes = ['cn', 'sAMAccountName', 'displayName', 'uid', 'mail', 'userAccountControl']

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
# flask ver<2.3
# app.config['JSON_AS_ASCII'] = False
# flask ver>=2.3
json.provider.DefaultJSONProvider.ensure_ascii = False


def buildFilter(args):
    filter = None

    for key in args:
        if key in filters:
            value = args[key]
            if filter:
                filter = f'(&{filter}({key}={value}))'
            else:
                filter = f'({key}={value})'
    return filter


UserAccountControl_DEF = {
    "SCRIPT": 0x0001,
    "ACCOUNTDISABLE": 0x0002,
    "HOMEDIR_REQUIRED": 0x0008,
    "LOCKOUT": 0x0010,
    "PASSWD_NOTREQD": 0x0020,
    "PASSWD_CANT_CHANGE": 0x0040,
    "ENCRYPTED_TEXT_PWD_ALLOWED": 0x0080,
    "TEMP_DUPLICATE_ACCOUNT": 0x0100,
    "NORMAL_ACCOUNT": 0x0200,
    "INTERDOMAIN_TRUST_ACCOUNT": 0x0800,
    "WORKSTATION_TRUST_ACCOUNT": 0x1000,
    "SERVER_TRUST_ACCOUNT": 0x2000,
    "DONT_EXPIRE_PASSWORD": 0x10000,
    "MNS_LOGON_ACCOUNT": 0x20000,
    "SMARTCARD_REQUIRED": 0x40000,
    "TRUSTED_FOR_DELEGATION": 0x80000,
    "NOT_DELEGATED": 0x100000,
    "USE_DES_KEY_ONLY": 0x200000,
    "DONT_REQ_PREAUTH": 0x400000,
    "PASSWORD_EXPIRED": 0x800000,
    "TRUSTED_TO_AUTH_FOR_DELEGATION": 0x1000000,
    "PARTIAL_SECRETS_ACCOUNT": 0x04000000


}


def doTranlsateUserAccountControl(raw):
    val = {"raw": raw}
    for key, value in UserAccountControl_DEF.items():
        val[key] = (raw & value) > 0
    return val


def tranlsateUserAccountControl(raw):
    if isinstance(raw, list):
        return [doTranlsateUserAccountControl(item) for item in raw]
    else:
        return doTranlsateUserAccountControl(raw)


def do_query(filter):
    server = Server(LDAP_SERVER, get_info=ALL)
    with Connection(server, user=LDAP_USER, password=LDAP_PASS) as conn:
        conn.open()
        conn.bind()
        # Perform the search
        # print('pppp' + filter)
        conn.search(LDAP_BASE, filter, attributes=attributes, size_limit=SEARCH_LIMIT)

        result = []
        for entry in conn.entries:
            vals = entry.entry_attributes_as_dict
            if 'userAccountControl' in vals:
                vals['userAccountControl'] = tranlsateUserAccountControl(vals['userAccountControl'])
            result.append(vals)
    return result


@app.route("/account", methods=["GET"])
def lookup():
    args = request.args
    filter = buildFilter(args)
    if not filter:
        return jsonify({'error': f'Please specify the conditions: {filters}'}), 400, {'Content-Type': 'application/json;charset=UTF-8'}

     # Set up the server connection

    result = do_query(filter)
    if result:
        return jsonify(result), 200, {'Content-Type': 'application/json;charset=UTF-8'}
    else:
        return jsonify({'error': 'account is not found'}), 404, {'Content-Type': 'application/json;charset=UTF-8'}


@app.route("/auth", methods=["POST"])
def auth():
    username = request.form['username']
    password = request.form['password']
    server = Server(LDAP_SERVER, get_info=ALL)
    try:
        with Connection(server, user=f'tonghao\\{username}', password=password) as conn:
            return jsonify({'auth': 'success'}), 200, {'Content-Type': 'application/json;charset=UTF-8'}
    except Exception as err:
        traceback.print_exc()
        return jsonify({'auth': 'failed'}), 400, {'Content-Type': 'application/json;charset=UTF-8'}


@app.route("/changepw", methods=["POST"])
def changepw():
    ''' Not working. Maybe it must be LDAPS'''
    username = request.form['username']
    password = request.form['old_password']
    new_pass = request.form['new_password']
    server = Server(LDAP_SERVER, get_info=ALL)
    try:
        with Connection(server, user=f'tonghao\\{username}', password=password) as conn:
            # oldpwd_utf16 = '"{0}"'.format(password).encode('utf-16-le')
            # newpwd_utf16 = '"{0}"'.format(new_pass).encode('utf-16-le')
            # conn.modify('CN=戴智杰,OU=Employee,DC=Tonghao,DC=local',
            #             {'unicodePwd': [(MODIFY_DELETE, [oldpwd_utf16]), (MODIFY_ADD, [newpwd_utf16])]})
            conn.extend.microsoft.modify_password('CN=戴智杰,OU=Employee,DC=Tonghao,DC=local', new_password=new_pass, old_password=password)
            print(conn.result)
            return jsonify({'operation': 'success'}), 200, {'Content-Type': 'application/json;charset=UTF-8'}
    except Exception as err:
        traceback.print_exc()
        return jsonify({'operation': 'failed'}), 400, {'Content-Type': 'application/json;charset=UTF-8'}


def startFlask():
    app.run(host="0.0.0.0", port=HTTP_PORT)


def gradio_lookup(query_type, query_value):
    args = {query_type: query_value}
    filter = buildFilter(args)
    if not filter:
        return {'error': f'Please specify the conditions: {filters}'}
    result = do_query(filter)
    if result:
        return result
    else:
        return {'error': 'account is not found'}


def launch_gradio():
    demo = gr.Interface(fn=gradio_lookup, title="Query LDAP Users",
                        inputs=[gr.Radio(filters, label="LDAP Attributes", info="Please specify the query attribute"),
                                gr.Textbox(label="Attribute Value")],
                        outputs=[gr.JSON(label="Query Result")])
    demo.launch(server_name="0.0.0.0", server_port=GRADIO_HTTP_PORT)


def main():
    daemon_thread = threading.Thread(target=startFlask)
    daemon_thread.daemon = True
    daemon_thread.start()
    launch_gradio()


if __name__ == '__main__':
    main()
