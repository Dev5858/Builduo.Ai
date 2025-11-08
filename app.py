from flask import Flask, request, jsonify
import subprocess, shlex

app = Flask(__name__)
MODEL = "gemma3:4b"  # Your local Ollama model


# 💬 AI Brain — ask Ollama locally
def ask_ollama(prompt):
    system_prompt = (
        "You are Builduo.ai — a smart, creative business assistant. "
        "When users ask for business, brand, or website ideas, respond instantly "
        "with a numbered list of 3 to 5 catchy, professional, modern options. "
        "Do not introduce yourself or ask clarifying questions. Just give results clearly."
    )

    full_prompt = system_prompt + "\n\nUser: " + prompt
    cmd = f"ollama run {shlex.quote(MODEL)} {shlex.quote(full_prompt)}"
    print("🧠 Running:", cmd)

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("💬 Raw output:", result.stdout)

    # Handle no response / Ollama error
    if not result.stdout.strip():
        return "⚠️ Ollama returned nothing. Make sure it's running and the model name is correct."

    return result.stdout.strip()


# 🔗 API Endpoint — handle POST requests from your Wix site or curl
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("message", "")
    if not prompt:
        return jsonify({"error": "No message provided"}), 400

    reply = ask_ollama(prompt)
    return jsonify({"assistant": "Builduo.ai", "reply": reply})


# 🏠 Root page — for browser visits (no 404)
@app.route("/", methods=["GET"])
def index():
    return (
        "<h2>Builduo.ai</h2>"
        "<p>✅ API is up and running.<br>"
        "Use POST /chat with JSON {'message': '...'} to get AI responses.</p>"
    )


# 🖼️ Favicon handler — stops annoying 404s
@app.route("/favicon.ico")
def favicon():
    return "", 204


# 🚀 Run server locally (Flask dev mode)
if __name__ == "__main__":
    print("🚀 Builduo.ai is now running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000)

