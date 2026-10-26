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

API_KEY = os.getenv("VOLC_API_KEY", "")
MODEL = os.getenv("VOLC_MODEL", "")

if not API_KEY or not MODEL:
    print("  警告：VOLC_API_KEY 或 VOLC_MODEL 未设置，请检查 .env 文件或 Railway 变量！")
else:
    print(f" API Key 已加载，模型：{MODEL}")

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return '', 204

    #  兼容更多字段名，加终端打印
    data = request.get_json(force=True, silent=True) or {}
    user_msg = data.get('content') or data.get('prompt') or data.get('q') or data.get('message') or 'hi'
    print(f"📩 收到提问: {user_msg}")  # 终端看这行，确认不是 'hi' 就说明前端传过来了

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
        "temperature": 0.7
    }

    try:
        print(" 请求火山方舟中...")
        r = requests.post(API_URL, headers=headers, json=payload, timeout=(20,60))
        r.raise_for_status()
        obj = r.json()
        answer = obj["choices"][0]["message"]["content"]
        print(f"返回成功，长度: {len(answer)}")
        return jsonify({"content": answer})
    except requests.exceptions.Timeout:
        print("火山方舟请求超时！")
        return jsonify({"content":"AI响应超时，请稍后重试"}),504
    except requests.exceptions.HTTPError as e:
        print(f" ARK HTTP 错误：{e}")
        print(f" 响应内容：{r.text[:200] if 'r' in dir() else '无'}")
        return jsonify({"content": f"AI接口返回错误（{r.status_code}）：{r.text[:100]}"}), 500

    except Exception as e:
        print(f" ARK 其他错误：{repr(e)}")
        return jsonify({"content": f"请求失败：{str(e)}"}), 500

#加 threaded=True，防连点卡死
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5002))
    app.run(host='0.0.0.0', port=port, threaded=True, debug=False)
