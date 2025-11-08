from flask import Flask, request, jsonify
import requests
import os
from waitress import serve

app = Flask(__name__)

MODEL = "meta-llama/llama-3.2-3b-instruct:free"  # verified available model
API_KEY = os.getenv("OPENROUTER_API_KEY")  # stored in Render environment

SYSTEM_PROMPT = (
    "You are Builduo.ai — a smart, creative business assistant. "
    "When users ask for business, brand, or website ideas, respond instantly "
    "with a numbered list of 3 to 5 catchy, professional, modern options. "
    "Do not introduce yourself or ask clarifying questions. Just give results clearly."
)

def ask_ai(prompt: str) -> str:
    if not API_KEY:
        return "⚠️ No API key found in environment (OPENROUTER_API_KEY)."

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
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
    """Main chat endpoint"""
    data = request.get_json(force=True)
    prompt = data.get("message", "").strip()
    if not prompt:
        return jsonify({"error": "No message provided"}), 400
    reply = ask_ai(prompt)
    return jsonify({"assistant": "Builduo.ai", "reply": reply})


@app.route("/", methods=["GET"])
def index():
    """Landing page"""
    return (
        "<h2>🤖 Builduo.ai is live!</h2>"
        "<p>Use <code>POST /chat</code> with JSON {'message': '...'} to get AI-generated business ideas.</p>"
    )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Render"""
    has_key = bool(API_KEY)
    return jsonify({"server": "ok", "openrouter_key_present": has_key, "model": MODEL})


@app.route("/favicon.ico")
def favicon():
    """Avoid browser favicon errors"""
    return "", 204


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Builduo.ai running locally on http://localhost:{port}")
    serve(app, host="0.0.0.0", port=port)
