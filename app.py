from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time
from waitress import serve

app = Flask(__name__)
CORS(app)

# --- Model Setup ---
PRIMARY_MODEL = "nousresearch/hermes-3-llama-3.1-70b"
FALLBACK_MODEL = "mistralai/mistral-7b-instruct"  # stable + active model
API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- Memory Store (in RAM) ---
conversations = {}  # {session_id: [{"role": "user"/"assistant", "content": "..."}]}

# --- System Persona ---
SYSTEM_PROMPT = (
    "You are Builduo.ai — a highly intelligent, confident, and creative business strategist. "
    "You act like a professional consultant with expertise in startups, branding, and web strategy. "
    "You remember recent conversation context to continue naturally. "
    "Your tone is sharp, friendly, and modern — you think like a real business partner, not a bot. "
    "Always respond with structured insights, examples, and creative reasoning. "
    "Give responses that sound like you're brainstorming alongside the user, not preaching. "
    "Be proactive, inspiring, and precise."
)


def ask_ai(session_id: str, model: str, retries: int = 2) -> str:
    """Send the conversation (context included) to OpenRouter."""
    if not API_KEY:
        return "⚠️ Missing API key in environment (OPENROUTER_API_KEY)."

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://builduo-ai.onrender.com",
        "X-Title": "Builduo.ai Assistant"
    }

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += conversations.get(session_id, [])

    payload = {
        "model": model,
        "temperature": 0.85,   # slightly more creative
        "max_tokens": 700,
        "messages": messages
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

            # Handle common issues
            if "Insufficient credits" in text or "402" in text:
                return "CREDIT_ERROR"
            if "No endpoints found" in text or "404" in text:
                return "MODEL_NOT_FOUND"
            if response.status_code != 200:
                time.sleep(2)
                continue

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
    session_id = data.get("session_id", "default_user").strip()

    if not prompt:
        return jsonify({"error": "No message provided"}), 400

    # Initialize conversation for new user
    if session_id not in conversations:
        conversations[session_id] = []

    # Add user message to memory
    conversations[session_id].append({"role": "user", "content": prompt})

    # Limit memory length (keep last 10 messages)
    if len(conversations[session_id]) > 10:
        conversations[session_id] = conversations[session_id][-10:]

    # Generate AI reply
    reply = ask_ai(session_id, PRIMARY_MODEL)

    # Fallback if Hermes fails
    if reply in ["CREDIT_ERROR", "MODEL_NOT_FOUND"] or "Insufficient credits" in reply:
        fallback_reply = ask_ai(session_id, FALLBACK_MODEL)
        reply = (
            f"💡 Hermes unavailable — switched to Mistral model.\n\n{fallback_reply}"
            if "⚠️" not in fallback_reply
            else "⚠️ Both models unavailable. Please check your OpenRouter account."
        )

    # Save assistant reply in memory
    conversations[session_id].append({"role": "assistant", "content": reply})

    return jsonify({
        "assistant": "Builduo.ai",
        "reply": reply,
        "memory_length": len(conversations[session_id])
    })


@app.route("/", methods=["GET"])
def index():
    return (
        "<h2>🤖 Builduo.ai — Your AI Business Partner</h2>"
        "<p>API is active.<br>"
        "Use <code>POST /chat</code> with JSON {'message': '...', 'session_id': 'user123'} "
        "to maintain conversation context.</p>"
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "server": "ok",
        "primary_model": PRIMARY_MODEL,
        "fallback_model": FALLBACK_MODEL,
        "active_conversations": len(conversations),
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
