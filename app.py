from flask import Flask, render_template, request, jsonify
import os, requests, json, traceback

app = Flask(__name__, static_folder="static", template_folder="templates")

# ================= API KEYS =================
TEXT_KEY  = os.getenv("OPENROUTER_API_KEY")         # TEXT / VOICE KEY (existing)
IMG_KEY   = os.getenv("OPENROUTER_IMAGE_API_KEY")   # IMAGE ONLY KEY (new)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

TEXT_MODEL = os.getenv("TEXT_MODEL" , "openrouter/auto:online")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "google/gemini-2.5-flash-image-preview")

# ================= ROUTES ===================

@app.route("/")
def home():
    return render_template("index.html")    # TEXT CHAT PAGE

@app.route("/voice")
def voice_page():
    return render_template("voice.html")    # VOICE MODE PAGE

@app.route("/image")
def image_page():
    return render_template("image.html")    # IMAGE MODE PAGE


# ================= TEXT / VOICE AI ==============
def call_openrouter_text(messages):
    if not TEXT_KEY:
        return None, "OPENROUTER_API_KEY not set"
    headers = {
        "Authorization": f"Bearer {TEXT_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": TEXT_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 800
    }
    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        data = r.json()
        if r.status_code != 200:
            return None, f"ERR {r.status_code}: {data}"
        # Standard openrouter responses
        msg = data["choices"][0]["message"]
        return msg.get("content","").strip(), None
    except Exception as e:
        return None, f"Exception: {e}"


@app.route("/ask", methods=["POST"])
def ask():
    try:
        body = request.get_json(force=True)
        user_msg = (body.get("message") or "").strip()
        agent = (body.get("agent") or "Luffy").strip()

        if not user_msg:
            return jsonify({"error":"Empty message"}), 400

        # PERSONALITY PROMPTS
        persona_map = {
            "Luffy":  "You speak like Monkey D. Luffy. Energetic, friendly, optimistic.",
            "Naruto": "You speak like Naruto Uzumaki. Determined, hopeful, brotherhood tone.",
            "Nami":   "You speak like Nami. Smart, practical, sharp mind but friendly.",
            "Sita":   "You speak like Sita. Calm, polite, dignified, compassionate."
        }
        persona = persona_map.get(agent,"")

        messages = [
            {"role":"system","content": persona + " Keep answers clear and simple; avoid emojis."},
            {"role":"user","content": user_msg}
        ]

        reply, err = call_openrouter_text(messages)
        if err:
            return jsonify({"error":err}), 500
        return jsonify({"reply":reply})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error":str(e)}), 500


# ============== IMAGE GENERATION ==============
def call_openrouter_image(prompt, aspect_ratio=None):
    if not IMG_KEY:
        return None, "OPENROUTER_IMAGE_API_KEY not set"
    headers = {
        "Authorization": f"Bearer {IMG_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": IMAGE_MODEL,
        "messages":[{"role":"user","content":prompt}],
        "modalities":["image","text"]
    }
    if aspect_ratio:
        payload["image_config"] = {"aspect_ratio": aspect_ratio}

    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
        data = r.json()
        if r.status_code != 200:
            return None, f"ERR {r.status_code}: {data}"
        msg = data["choices"][0]["message"]
        imgs = msg.get("images") or []
        if not imgs:
            return None,"No image in response"
        return imgs[0]["image_url"]["url"],None
    except Exception as e:
        return None, f"Exception: {e}"


@app.route("/image",methods=["POST"])
def make_image():
    try:
        body = request.get_json(force=True)
        prompt = (body.get("prompt") or "").strip()
        ratio = (body.get("aspect_ratio") or "").strip() or None
        if not prompt:
            return jsonify({"error":"Empty prompt"}),400
        url,err = call_openrouter_image(prompt,ratio)
        if err:
            return jsonify({"error":err}),500
        return jsonify({"image":url})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error":str(e)}),500


# ============= HEALTH CHECK ==================
@app.route("/health")
def health():
    return "ok",200


# ============== DEV MODE LOCAL RUN ============
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000,debug=True)
