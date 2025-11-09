from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from waitress import serve

app = Flask(__name__)
CORS(app)  # Enable CORS for Wix & external access

# 🚀 Model + Key setup
MODEL = "nousresearch/hermes-3-llama-3.1-70b"
API_KEY = os.getenv("OPENROUTER_API_KEY")  # Stored in Render environment

# 💼 System prompt for a real, professional AI assistant
SYSTEM_PROMPT = (
    "You are Builduo.ai — an intelligent and experienced AI business strategist. "
    "You think like a branding expert, a web consultant, and a startup advisor. "
    "Your tone is professional but friendly, confident, and human-like. "
    "When users ask for business ideas, names, or strategy suggestions, "
    "you provide structured, creative, and realistic insights. "
    "Give responses in clear bullet points or short paragraphs — "
    "always actionable, catchy, and modern. "
    "You never say 'as an AI' — you speak naturally and confidently as Builduo.ai."
)

def ask_ai(prompt: str) -> str:
    """Send a user prompt to the AI model via OpenRouter"""
    if not API_KEY:
        return "⚠️ Missing API key in environment (OPENROUTER_API_KEY)."

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://builduo-ai.onrender.com",
        "X-Title": "Builduo.ai Assistant"
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
            timeout=90
        )
        if response.status_code != 200:
            return f"⚠️ API Error {response.status_code}: {response.text}"

        res_json = response.json()
        reply = res_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        return reply.strip() or "⚠️ No response from the model."
    except Exception as e:
        return f"⚠️ Request failed: {str(e)}"


@app.route("/chat", methods=["POST"])
def chat():
    """Main AI chat endpoint"""
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
        "<h2>🤖 Builduo.ai — Your AI Business Partner</h2>"
        "<p>API is active.<br>"
        "Use <code>POST /chat</code> with JSON {'message': '...'} to get tailored business advice.</p>"
    )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Render"""
    return jsonify({
        "server": "ok",
        "model": MODEL,
        "api_key_found": bool(API_KEY)
    })


@app.route("/favicon.ico")
def favicon():
    """Ignore browser favicon requests"""
    return "", 204


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Builduo.ai running locally at http://localhost:{port}")
    serve(app, host="0.0.0.0", port=port)
