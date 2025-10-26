# app.py
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
def englishToSpanish(text: str) -> str:
    return GoogleTranslator(source="en", target="es").translate(text or "")

def spanishToEnglish(text: str) -> str:
    return GoogleTranslator(source="es", target="en").translate(text or "")

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


@app.route("/stt", methods=["POST"])
def stt():
    """
    Receives a recorded audio blob, sends it to ElevenLabs STT,
    and returns recognized text as JSON.
    """
    if "audio" not in request.files:
        return {"error": "Missing audio file"}, 400

    audio_file = request.files["audio"]

    if not audio_file.filename:
        return {"error": "Empty filename"}, 400

    audio_bytes = audio_file.read()
    if not audio_bytes:
        return {"error": "Empty audio payload"}, 400

    mimetype = getattr(audio_file, "mimetype", None) or "application/octet-stream"

    files = {
        "file": (audio_file.filename, audio_bytes, mimetype)
    }
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "application/json"
    }

    # ✅ Correct STT model for ElevenLabs
    data = {
        "model_id": "scribe_v1"
    }

    url = "https://api.elevenlabs.io/v1/speech-to-text"

    try:
        response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
    except requests.RequestException as e:
        return {"error": f"Upstream request failed: {e}"}, 502

    if not response.ok:
        try:
            return {"error": response.json()}, response.status_code
        except ValueError:
            return {"error": response.text}, response.status_code

    try:
        result = response.json()
    except ValueError:
        return {"error": "Upstream returned non-JSON"}, 502

    recognized_text = result.get("text", "")
    return {"text": recognized_text}


@app.route("/translate", methods=["POST"])
def translate_api():
    """
    Simple JSON/form translate helper for the frontend.
    Accepts JSON { sentence, languages } or form-encoded data and
    returns JSON { translated_text }.
    """
    data = request.get_json(silent=True) or request.form or {}
    user_text = (data.get("sentence") or data.get("text") or "").strip()
    selected_lang = (data.get("languages") or data.get("language") or "").strip()

    if not user_text:
        return {"error": "Missing sentence parameter"}, 400

    translated_text = None
    if selected_lang == "en_to_es":
        translated_text = englishToSpanish(user_text)
    elif selected_lang == "es_to_en":
        translated_text = spanishToEnglish(user_text)
    else:
        # If no/unknown language provided, try to auto-detect based on simple heuristic:
        # default to English->Spanish
        translated_text = englishToSpanish(user_text)

    return {"translated_text": translated_text}


@app.route("/tts")
def tts():
    """
    Streams ElevenLabs TTS audio (MPEG) for the given ?text= query param.
    """
    text = request.args.get("text", "").strip()
    if not text:
        return ("Missing ?text parameter", 400)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    # ✅ Keep TTS model as multilingual
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
