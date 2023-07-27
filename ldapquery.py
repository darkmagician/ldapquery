from ldap3 import Server, Connection, ALL
from flask import request
from flask import jsonify
from flask import Flask
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

attributes = ['cn', 'sAMAccountName', 'displayName', 'uid', 'mail']

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route("/account", methods=["GET"])
def lookup():
    args = request.args
    key = 'sAMAccountName'
    value = args.get(key)
    if not value:
        return jsonify({'error': f'Please specify the {key}'}), 400

     # Set up the server connection
    server = Server(LDAP_SERVER, get_info=ALL)
    conn = Connection(server, user=LDAP_USER, password=LDAP_PASS)
    conn.open()
    conn.bind()
    # Perform the search
    conn.search(LDAP_BASE, f'({key}={value})', attributes=attributes)
    print(f'({key}={value})')
    print(f'({LDAP_USER})')
    result = []
    for entry in conn.entries:
        vals = entry.entry_attributes_as_dict
        result.append(vals)

    if result:
        return jsonify(result), 200
    else:
        return jsonify({'error': 'account is not found'}), 404


def main():
    app.run(host="0.0.0.0", port=HTTP_PORT)


if __name__ == '__main__':
    main()
