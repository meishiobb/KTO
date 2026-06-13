from flask import Flask, request, jsonify
import json, requests, hashlib, hmac

app = Flask(__name__)

# ========== 配置 ==========
DEEPSEEK_KEY = "sk-cbfbe30aa0d547f4be32a9f789450018"          # ← 改这里
ADMIN_TOKEN = "KTO算法-美术老师"

user_data = {}

# ========== 防泄露 ==========

def check_token():
    token = request.headers.get("X-Admin-Token", "")
    return hmac.compare_digest(token, ADMIN_TOKEN)

def get_user_id():
    return request.headers.get("X-User-Token", request.remote_addr)

# ========== AI 生成算法 ==========

def generate_algo_code(idea):
    prompt = f"""你是一个预测算法生成器，用于PC28彩票游戏。

【游戏规则】
- 每期开出3个数字(x,y,z)，每个数字范围0-9，和值s=x+y+z，范围0-27
- 分类：小双(s≤13且偶)、小单(s≤13且奇)、大双(s>13且偶)、大单(s>13且奇)
- 用户每期选三个组合下注，排除一个
- 目标：预测下一期应该排除哪个组合

【函数要求】
函数名：predict
输入：history（整数和值列表，最新在最后）
返回：'小双'、'小单'、'大双' 或 '大单'

【用户策略】
{idea}

只输出Python代码，包含 def predict(history): 并以return结尾。"""
    
    headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
    
    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers, timeout=30)
        if r.status_code == 200:
            code = r.json()["choices"][0]["message"]["content"]
            if "```" in code:
                code = code.split("```")[1]
                if code.startswith("python"):
                    code = code[6:]
            return code.strip()
    except:
        pass
    return None

# ========== API ==========

@app.route('/api/generate', methods=['POST'])
def api_generate():
    if not check_token():
        return jsonify({"ok": False, "msg": "无权限"})
    
    data = request.get_json()
    idea = data.get('idea', '')
    if not idea:
        return jsonify({"ok": False, "msg": "请输入思路"})
    
    code = generate_algo_code(idea)
    if not code:
        return jsonify({"ok": False, "msg": "AI生成失败"})
    
    user_id = get_user_id()
    user_data[user_id] = {"algo_code": code, "history": []}
    
    return jsonify({"ok": True, "msg": "算法已生效"})

@app.route('/api/user_status')
def api_user_status():
    user_id = get_user_id()
    
    if user_id in user_data and user_data[user_id]["algo_code"]:
        algo = "用户自定义"
        history = user_data[user_id]["history"]
        try:
            namespace = {}
            exec(user_data[user_id]["algo_code"], namespace)
            next_kill = namespace["predict"](history)
        except:
            next_kill = "错误"
    else:
        algo = "默认"
        next_kill = "等待设置"
    
    return jsonify({
        "algo": algo,
        "next_kill": next_kill,
        "win_rate": 0,
        "total": len(user_data.get(user_id, {}).get("history", []))
    })

@app.route('/api/push_data', methods=['POST'])
def push_data():
    if not check_token():
        return jsonify({"ok": False, "msg": "无权限"})
    
    data = request.get_json()
    total_sum = data.get('sum')
    
    for uid in user_data:
        user_data[uid]["history"].append(total_sum)
        if len(user_data[uid]["history"]) > 100:
            user_data[uid]["history"].pop(0)
    
    return jsonify({"ok": True})

@app.route('/')
def home():
    return "KTO Server Running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
