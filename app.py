from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ✅ Model & API setup
MODEL = "meta-llama/llama-3-8b-instruct:free"
API_KEY = os.getenv("OPENROUTER_API_KEY")  # Render environment variable

def ask_ai(prompt):
    system_prompt = (
        "You are Builduo.ai — a smart, creative business assistant. "
        "When users ask for business, brand, or website ideas, respond instantly "
        "with a numbered list of 3 to 5 catchy, professional, modern options. "
        "Do not introduce yourself or ask clarifying questions. Just give results clearly."
    )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            return f"⚠️ API Error {response.status_code}: {response.text}"

        res_json = response.json()
        reply = res_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        return reply.strip() or "⚠️ Model returned no reply."

    except Exception as e:
        return f"⚠️ Request failed: {str(e)}"


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("message", "")
    if not prompt:
        return jsonify({"error": "No message provided"}), 400

    reply = ask_ai(prompt)
    return jsonify({"assistant": "Builduo.ai", "reply": reply})


@app.route("/", methods=["GET"])
def index():
    return (
        "<h2>🤖 Builduo.ai is live!</h2>"
        "<p>Use POST /chat with JSON {'message': '...'} to get AI-generated business ideas.</p>"
    )


@app.route("/favicon.ico")
def favicon():
    return "", 204


if __name__ == "__main__":
    print("🚀 Builduo.ai running locally at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000)
