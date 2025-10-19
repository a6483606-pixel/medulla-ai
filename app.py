# app.py
# Medulla AI — OpenRouter integration (chat + browser TTS)
# Usage: python app.py
# Make sure OPENROUTER_API_KEY is set in your environment before running.

from flask import Flask, render_template, request, jsonify
import os
import requests
import json
import traceback

app = Flask(__name__, static_folder="static", template_folder="templates")

# -------- CONFIG --------
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_KEY:
    raise RuntimeError(
        "OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable first.\n"
        'PowerShell example: setx OPENROUTER_API_KEY "or_your_key_here"\n'
        "Then open a NEW PowerShell window and run: python app.py"
    )

# OpenRouter chat endpoint
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

# Default model: let OpenRouter auto-route to best available model.
# You may replace "openrouter/auto" with a specific model id if you prefer.
MODEL = "openrouter/auto"

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_KEY}",
    "Content-Type": "application/json",
}

# -------- Helpers --------
def call_openrouter_chat(messages, temperature=0.7, max_tokens=700, timeout=60):
    """
    Calls OpenRouter chat completions endpoint with an OpenAI-style messages list.
    Returns assistant text or raises a RuntimeError with details.
    """
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }

    resp = requests.post(OPENROUTER_CHAT_URL, headers=HEADERS, data=json.dumps(payload), timeout=timeout)

    if resp.status_code != 200:
        # Try to decode JSON error if possible, raise informative error
        try:
            err_json = resp.json()
            raise RuntimeError(f"OpenRouter API error {resp.status_code}: {json.dumps(err_json)}")
        except ValueError:
            raise RuntimeError(f"OpenRouter API error {resp.status_code}: {resp.text}")

    data = resp.json()

    # Typical OpenAI-style response: choices[0].message.content
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    # Fallbacks: some providers return choices[0].text, or other shapes
    try:
        return data["choices"][0]["text"].strip()
    except Exception:
        pass

    # If still nothing, return a stringified version (limited length)
    return json.dumps(data)[:2000]


# -------- Routes --------
@app.route("/")
def index():
    # Serves templates/index.html (your existing UI)
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    try:
        req = request.get_json(force=True)
        user_message = req.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        messages = [
            {"role": "system", "content": "You are Medulla AI — a helpful, honest, and friendly assistant. Answer simply and clearly."},
            {"role": "user", "content": user_message}
        ]

        reply_text = call_openrouter_chat(messages)
        return jsonify({"reply": reply_text})
    except Exception as e:
        # Print full traceback to terminal for debugging
        print("Error in /ask endpoint:")
        traceback.print_exc()
        # Return concise error to browser
        return jsonify({"error": str(e)}), 500


# -------- Run server --------
if __name__ == "__main__":
    print("Starting Medulla AI (DeepSeek / OpenRouter) web server...")
    print("Model:", MODEL)
    print("Make sure your API key environment variable is set.")
    # Listen on all interfaces so other devices on the same network can reach it
    app.run(host="0.0.0.0", port=5000, debug=True)

