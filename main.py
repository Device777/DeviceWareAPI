
from flask import Flask, request, jsonify
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
    # Gera chave estilo DEVICEWARE-XXXXXXXX (8 chars)
    return 'DEVICEWARE-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@app.route('/create', methods=['POST'])
def create_key():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "JSON obrigatório."})

    dias = data.get('dias', 7)

    keys = load_keys()

    # Gera nova key
    new_key = generate_key()
    expires = datetime.now() + timedelta(days=dias)
    keys[new_key] = {
        "expires": expires.strftime("%Y-%m-%d"),
        "status": "active"
    }
    save_keys(keys)
    return jsonify({"status": "ok", "key": new_key, "expires": expires.strftime("%Y-%m-%d")})

@app.route('/check')
def check_key():
    key = request.args.get('key')

    if not key:
        return jsonify({"status": "error", "message": "Parâmetro 'key' é obrigatório."})

    keys = load_keys()
    entry = keys.get(key)

    if not entry:
        return jsonify({"status": "invalid", "message": "Key inválida."})

    if entry.get('status') != 'active':
        return jsonify({"status": "banned", "message": "Key banida."})

    expires = datetime.strptime(entry['expires'], "%Y-%m-%d")
    if datetime.now() > expires:
        return jsonify({"status": "expired", "message": "Key expirada."})

    dias_restantes = (expires - datetime.now()).days
    return jsonify({"status": "ok", "dias_restantes": dias_restantes, "message": "Key válida."})

@app.route('/deactivate', methods=['POST'])
def deactivate_key():
    data = request.json
    if not data or 'key' not in data:
        return jsonify({"status": "error", "message": "Campo 'key' obrigatório."})

    key = data['key']
    keys = load_keys()

    if key not in keys:
        return jsonify({"status": "error", "message": "Key não encontrada."})

    keys[key]['status'] = 'banned'
    save_keys(keys)
    return jsonify({"status": "ok", "message": f"Key '{key}' desativada."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
