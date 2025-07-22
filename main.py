from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import json
import threading
import os
import random
import string

app = Flask(__name__)
lock = threading.Lock()
KEYS_FILE = 'keys.json'

def load_keys():
    if not os.path.exists(KEYS_FILE):
        return {}
    with open(KEYS_FILE, 'r') as f:
        return json.load(f)

def save_keys(keys):
    with lock:
        with open(KEYS_FILE, 'w') as f:
            json.dump(keys, f, indent=4)

def generate_key():
    return 'DEVICEWARE-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@app.route('/')
def index():
    keys = load_keys()
    return render_template('index.html', keys=keys)

@app.route('/create_key', methods=['POST'])
def create_key():
    dias = request.form.get('dias', type=int)
    if not dias or dias <= 0:
        return jsonify({"status": "error", "message": "Dias inválidos"}), 400

    keys = load_keys()
    new_key = generate_key()
    expires = datetime.now() + timedelta(days=dias)
    keys[new_key] = {
        "expires": expires.strftime("%Y-%m-%d"),
        "status": "active"
    }
    save_keys(keys)
    return jsonify({"status": "ok", "key": new_key, "expires": keys[new_key]['expires']})

@app.route('/validate_key', methods=['POST'])
def validate_key():
    key = request.form.get('key')
    if not key:
        return jsonify({"status": "error", "message": "Chave não fornecida"}), 400
    
    keys = load_keys()
    key_data = keys.get(key)
    
    if not key_data:
        return jsonify({"status": "error", "message": "Chave inválida"}), 404
    
    expires_str = key_data.get("expires")
    if not expires_str:
        return jsonify({"status": "error", "message": "Dados da chave inválidos"}), 500
    
    expires_date = datetime.strptime(expires_str, "%Y-%m-%d")
    if expires_date < datetime.now():
        return jsonify({"status": "error", "message": "Chave expirada"}), 403
    
    if key_data.get("status") != "active":
        return jsonify({"status": "error", "message": "Chave inativa"}), 403
    
    return jsonify({"status": "ok", "message": "Chave válida"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
