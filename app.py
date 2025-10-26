import os
import requests
from dotenv import load_dotenv
from flask import Flask, request, render_template, Response, stream_with_context
from deep_translator import GoogleTranslator

load_dotenv()

app = Flask(__name__)

# --- ENV ---
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")  # e.g., "21m00Tcm4TlvDq8ikWAM"

if not ELEVEN_API_KEY:
    raise RuntimeError("Missing ELEVENLABS_API_KEY in .env")
if not VOICE_ID:
    raise RuntimeError("Missing ELEVENLABS_VOICE_ID in .env")

# --- Translation helpers ---
def englishToSpanish(text):
    return GoogleTranslator(source="en", target="es").translate(text)

def spanishToEnglish(text):
    return GoogleTranslator(source="es", target="en").translate(text)

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    translated_text = None
    if request.method == "POST":
        user_text = request.form.get("sentence", "")
        selected_lang = request.form.get("languages", "")
        if selected_lang == "en_to_es":
            translated_text = englishToSpanish(user_text)
        elif selected_lang == "es_to_en":
            translated_text = spanishToEnglish(user_text)
    return render_template("index.html", translated_text=translated_text)

@app.route("/tts")
def tts():
    text = request.args.get("text", "").strip()
    if not text:
        return ("Missing ?text parameter", 400)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2"
    }

    try:
        r = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
        r.raise_for_status()
    except requests.RequestException as e:
        return (f"TTS error: {e}", 502)

    def generate():
        for chunk in r.iter_content(chunk_size=16384):
            if chunk:
                yield chunk

    return Response(stream_with_context(generate()), mimetype="audio/mpeg")

# --- Start app *after* routes are defined ---
if __name__ == "__main__":
    app.run(debug=True)
