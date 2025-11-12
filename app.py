from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from waitress import serve
import time

app = Flask(__name__)
CORS(app)

# --- Model Setup ---
PRIMARY_MODEL = "nousresearch/hermes-3-llama-3.1-70b"       # High intelligence (premium)
FALLBACK_MODEL = "openchat/openchat-8b"                     # Free + stable fallback
API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- System Persona ---
SYSTEM_PROMPT = (
    "You are Builduo.ai — an intelligent, confident, and creative business strategist. "
    "You combine the insight of a startup founder, the creativity of a branding expert, "
    "and the practicality of a business consultant. "
    "You always provide sharp, modern, and realistic ideas — never generic filler. "
    "If a user asks for ideas, give clear, structured answers with catchy phrasing, "
    "unique angles, and optional next steps. "
    "You can use emojis subtly to add personality when appropriate. "
    "Always sound like a confident professional, not a bot."
)


def ask_ai(prompt: str, model: str, retries: int = 2) -> str:
    """Send a message to OpenRouter with retry + error handling."""
    if not API_KEY:
        return "⚠️ Missing API key in environment (OPENROUTER_API_KEY)."

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://builduo-ai.onrender.com",
        "X-Title": "Builduo.ai Assistant"
    }

    payload = {
        "model": model,
        "temperature": 0.8,   # more creative, but still consistent
        "max_tokens": 600,    # limit output length to control costs
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    }

    for attempt in range(retries):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=90
            )

            text = response.text

            # Handle credit or missing model issues
            if "Insufficient credits" in text or "402" in text:
                return "CREDIT_ERROR"
            if "No endpoints found" in text or "404" in text:
                return "MODEL_NOT_FOUND"

            if response.status_code != 200:
                time.sleep(2)
                continue  # retry

            res_json = response.json()
            reply = res_json.get("choices", [{}])[0].get("message", {}).get("content", "")
            return reply.strip() or "⚠️ Empty response."

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return f"⚠️ Request failed: {str(e)}"

    return "⚠️ Could not reach model after multiple attempts."


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    prompt = data.get("message", "").strip()
    if not prompt:
        return jsonify({"error": "No message provided"}), 400

    reply = ask_ai(prompt, PRIMARY_MODEL)

    # --- Auto fallback if primary fails ---
    if reply in ["CREDIT_ERROR", "MODEL_NOT_FOUND"] or "Insufficient credits" in reply:
        fallback_reply = ask_ai(prompt, FALLBACK_MODEL)
        reply = (
            f"💡 Hermes unavailable — switched to OpenChat model.\n\n{fallback_reply}"
            if "⚠️" not in fallback_reply
            else "⚠️ Both models unavailable. Please check your OpenRouter account."
        )

    return jsonify({
        "assistant": "Builduo.ai",
        "reply": reply
    })


@app.route("/", methods=["GET"])
def index():
    return (
        "<h2>🤖 Builduo.ai — Your AI Business Partner</h2>"
        "<p>API is active.<br>"
        "Use <code>POST /chat</code> with JSON {'message': '...'} to get tailored business advice.</p>"
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "server": "ok",
        "primary_model": PRIMARY_MODEL,
        "fallback_model": FALLBACK_MODEL,
        "api_key_found": bool(API_KEY)
    })


@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200


@app.route("/favicon.ico")
def favicon():
    return "", 204


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Builduo.ai running locally on http://localhost:{port}")
    serve(app, host="0.0.0.0", port=port)
