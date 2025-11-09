from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from waitress import serve

app = Flask(__name__)
CORS(app)

# --- MODELS ---
PRIMARY_MODEL = "nousresearch/hermes-3-llama-3.1-70b"  # Premium model
FALLBACK_MODEL = "mistralai/mistral-7b-instruct"       # Free fallback model

API_KEY = os.getenv("OPENROUTER_API_KEY")

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

# --- Function to Query Model ---
def ask_ai(prompt: str, model: str) -> str:
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

        # Handle API-level issues
        if response.status_code != 200:
            return f"⚠️ API Error {response.status_code}: {response.text}"

        res_json = response.json()
        reply = res_json.get("choices", [{}])[0].get("message", {}).get("content", "")

        if "Insufficient credits" in response.text:
            return "⚠️ Insufficient credits — please upgrade your plan or try again later."

        return reply.strip() or "⚠️ No response from the model."
    except Exception as e:
        return f"⚠️ Request failed: {str(e)}"

# --- Chat Endpoint ---
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    prompt = data.get("message", "").strip()
    if not prompt:
        return jsonify({"error": "No message provided"}), 400

    # Try primary model
    reply = ask_ai(prompt, PRIMARY_MODEL)

    # Auto fallback if credit issue or Hermes fails
    if "Insufficient credits" in reply or "API Error" in reply:
        fallback_reply = ask_ai(prompt, FALLBACK_MODEL)
        if "⚠️" not in fallback_reply:
            reply = f"💡 Hermes unavailable — switched to free Mistral model.\n\n{fallback_reply}"

    return jsonify({"assistant": "Builduo.ai", "reply": reply})


# --- Other Endpoints ---
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
    """Ultra-fast uptime endpoint"""
    return "pong", 200


@app.route("/favicon.ico")
def favicon():
    return "", 204


# --- Run Server ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Builduo.ai running locally on http://localhost:{port}")
    serve(app, host="0.0.0.0", port=port)
