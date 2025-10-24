# app.py — Medulla AI (two OpenRouter keys: one for text, one for images)
from flask import Flask, render_template, request, jsonify
import os, requests, json, traceback

app = Flask(__name__, static_folder="static", template_folder="templates")

# --------- TEXT / VOICE (existing) ----------
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")  # text key you already use
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
TEXT_MODEL = os.getenv("TEXT_MODEL", "openrouter/auto:online")  # pick your text model

# --------- IMAGES (new, separate key) -------
OPENROUTER_IMAGE_KEY = os.getenv("OPENROUTER_IMAGE_API_KEY")  # NEW: image-only key
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "google/gemini-2.5-flash-image-preview")  # default image model

# ---------------- UI ------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- TEXT ----------------------
def call_openrouter_text(messages, temperature=0.7, max_tokens=700, timeout=60):
    if not OPENROUTER_KEY:
        return None, "OPENROUTER_API_KEY not set."
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": TEXT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    r = requests.post(OPENROUTER_CHAT_URL, headers=headers, json=payload, timeout=timeout)
    if r.status_code != 200:
        try:
            return None, f"OpenRouter error {r.status_code}: {r.json()}"
        except:
            return None, f"OpenRouter error {r.status_code}: {r.text}"
    data = r.json()
    # Standard OpenRouter chat shape
    try:
        return data["choices"][0]["message"]["content"].strip(), None
    except:
        try:
            return data["choices"][0]["text"].strip(), None
        except:
            return json.dumps(data)[:1500], None

@app.route("/ask", methods=["POST"])
def ask():
    try:
        body = request.get_json(force=True)
        msg = (body.get("message") or "").strip()
        if not msg:
            return jsonify({"error":"No message provided"}), 400
        messages = [
            {"role":"system","content":"You are Medulla AI — helpful, honest, friendly. Keep language simple."},
            {"role":"user","content": msg}
        ]
        reply, err = call_openrouter_text(messages)
        if err:
            return jsonify({"error": err}), 500
        return jsonify({"reply": reply})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------------- IMAGES --------------------
def call_openrouter_image(prompt, aspect_ratio=None, timeout=120):
    """
    Uses the *image key* and an image-capable model to generate a PNG data URL.
    OpenRouter docs: use /chat/completions with modalities ["image","text"].
    """
    if not OPENROUTER_IMAGE_KEY:
        return None, "OPENROUTER_IMAGE_API_KEY not set."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_IMAGE_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": IMAGE_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "modalities": ["image", "text"]  # required to request image output
    }

    # Optional aspect ratio (some models support this; Gemini image preview does)
    if aspect_ratio:
        payload["image_config"] = {"aspect_ratio": aspect_ratio}

    r = requests.post(OPENROUTER_CHAT_URL, headers=headers, json=payload, timeout=timeout)
    if r.status_code != 200:
        try:
            return None, f"Image API error {r.status_code}: {r.json()}"
        except:
            return None, f"Image API error {r.status_code}: {r.text}"

    data = r.json()
    # Expected shape for image gen per OpenRouter docs: assistant message has `images` with data URLs
    try:
        msg = data["choices"][0]["message"]
        imgs = msg.get("images") or []
        if not imgs:
            # Some models may put it under delta in streams; for non-stream we expect images here
            return None, "No images field in response."
        # Take the first image
        url = imgs[0]["image_url"]["url"]  # data:image/png;base64,....
        return url, None
    except Exception:
        return None, "Unexpected image response format."

@app.route("/image", methods=["POST"])
def image():
    try:
        body = request.get_json(force=True)
        prompt = (body.get("prompt") or "").strip()
        aspect_ratio = (body.get("aspect_ratio") or "").strip() or None  # e.g., "16:9"
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        img_data_url, err = call_openrouter_image(prompt, aspect_ratio=aspect_ratio)
        if err:
            return jsonify({"error": err}), 500

        # Return the base64 data URL for direct <img src="...">
        return jsonify({"image": img_data_url})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ---------------- HEALTH --------------------
@app.route("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    # Local testing only; production runs via gunicorn (Procfile)
    app.run(host="0.0.0.0", port=5000, debug=True)

