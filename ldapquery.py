from ldap3 import Server, Connection, ALL, MODIFY_REPLACE, MODIFY_ADD, MODIFY_DELETE
from flask import request
from flask import jsonify
from flask import Flask
from flask import json
import traceback
import os


def getENV(key, defaultVal=None):
    if defaultVal:
        return os.getenv(key, default=defaultVal)
    val = os.getenv(key)
    if val:
        return val
    raise Exception(f'env {key} is not configured')


# Environments
HTTP_PORT = getENV('HTTP_PORT', 4084)
LDAP_SERVER = getENV('LDAP_SERVER')
LDAP_USER = getENV('LDAP_USER')
LDAP_PASS = getENV('LDAP_PASS')
LDAP_BASE = getENV('LDAP_BASE')
SEARCH_LIMIT = getENV('SEARCH_LIMIT', 10)

filters = ['cn', 'sAMAccountName', 'displayName', 'uid', 'mail']
attributes = ['cn', 'sAMAccountName', 'displayName', 'uid', 'mail']

app = Flask(__name__)
# flask ver<2.3
#app.config['JSON_AS_ASCII'] = False
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


@app.route("/account", methods=["GET"])
def lookup():
    args = request.args
    filter = buildFilter(args)
    if not filter:
        return jsonify({'error': f'Please specify the conditions: {filters}'}), 400, {'Content-Type': 'application/json;charset=UTF-8'}

     # Set up the server connection
    server = Server(LDAP_SERVER, get_info=ALL)
    with Connection(server, user=LDAP_USER, password=LDAP_PASS) as conn:
        conn.open()
        conn.bind()
        # Perform the search
        #print('pppp' + filter)
        conn.search(LDAP_BASE, filter, attributes=attributes, size_limit=SEARCH_LIMIT)

        result = []
        for entry in conn.entries:
            vals = entry.entry_attributes_as_dict
            result.append(vals)

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


def main():
    app.run(host="0.0.0.0", port=HTTP_PORT)


if __name__ == '__main__':
    main()
