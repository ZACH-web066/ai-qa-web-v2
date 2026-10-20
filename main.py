from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
load_dotenv()
# ===== 配置 =====
app = Flask(__name__, static_folder=os.path.dirname(os.path.abspath(__file__)), static_url_path='')
CORS(app, resources={r"/api/*": {
    "origins": [
        "https://ai-qa-web-v2-production.up.railway.app",
        "http://127.0.0.1:5002"
    ],
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type"]
}})
API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

# 从环境变量读，绝不硬编码（.env 本地用，Railway 后台配）
API_KEY = os.getenv("VOLC_API_KEY", "")
MODEL = os.getenv("VOLC_MODEL", "")

# 本地启动时的友好提示（帮你确认环境变量有没有读到）
if not API_KEY or not MODEL:
    print("⚠️  警告：VOLC_API_KEY 或 VOLC_MODEL 未设置，请检查 .env 文件或 Railway 变量！")
else:
    print(f"✅ API Key 已加载，模型：{MODEL}")

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    # 预检请求直接返回 204
    if request.method == "OPTIONS":
        return '', 204

    # 兼容前端两种字段名：content 或 prompt
    data = request.get_json(force=True, silent=True) or {}
    user_msg = data.get('content') or data.get('prompt') or 'hi'

    # 🚨 如果 Key 没读到，直接返回清晰错误，而不是让火山返回模糊报错
    if not API_KEY:
        return jsonify({"content": "服务端未配置 API Key，请联系开发者或检查 .env / Railway 环境变量"}), 500

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是大一C语言和思政知识点辅导老师，只回答大一C语言、思政相关名词解释、知识点讲解。如果用户问无关内容，请回复：我仅支持大一C语言与思政知识点答疑。回答简洁易懂，适合大学生复习。"
            },
            {"role": "user", "content": user_msg}
        ],
        "stream": False,
        "temperature": 0.7  # 加一个，避免部分模型严格校验
    }

    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        obj = r.json()
        answer = obj["choices"][0]["message"]["content"]
        return jsonify({"content": answer})

    except requests.exceptions.HTTPError as e:
        # 把火山返回的真实错误打出来，方便你定位
        print(f"❌ ARK HTTP 错误：{e}")
        print(f"   响应内容：{r.text[:200] if 'r' in dir() else '无'}")
        return jsonify({"content": f"AI接口返回错误（{r.status_code}）：{r.text[:100]}"}), 500

    except Exception as e:
        print(f"❌ ARK 其他错误：{repr(e)}")
        return jsonify({"content": f"请求失败：{str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    app.run(host='0.0.0.0', port=port, debug=False)
