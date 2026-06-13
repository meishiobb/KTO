7fromfrom flask import Flask, request, jsonify
import json, hashlib, hmac

app = Flask(__name__)

ADMIN_TOKEN = "KTO2024meishu"
shared_history = []          # 最近5000期和值列表

def check_token():
    token = request.headers.get("X-Admin-Token", "")
    return hmac.compare_digest(token, ADMIN_TOKEN)

def is_safe_code(code):
    forbidden = ["import os", "import sys", "import subprocess",
                 "__", "eval(", "exec(", "open(", "write("]
    return not any(f in code for f in forbidden)

# ========== 接口 ==========

@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.get_json()
    code = data.get('code', '')
    history = data.get('history', [])

    if not is_safe_code(code):
        return jsonify({"ok": False, "kill": "代码含危险操作"})

    try:
        namespace = {}
        exec(code, namespace)
        result = namespace["predict"](history)
        return jsonify({"ok": True, "kill": result})
    except Exception as e:
        return jsonify({"ok": False, "kill": "执行错误", "error": str(e)})

@app.route('/api/data')
def api_data():
    return jsonify({"history": shared_history})

@app.route('/api/push_data', methods=['POST'])
def push_data():
    if not check_token():
        return jsonify({"ok": False, "msg": "无权限"})

    data = request.get_json()
    history = data.get('history', [])
    if history:
        global shared_history
        shared_history = history[-5000:]
    return jsonify({"ok": True})

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Admin-Token'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST'
    return response

@app.route('/')
def home():
    return "KTO Server Running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
