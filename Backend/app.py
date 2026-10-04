
import os
import base64
import tempfile
import logging
from pathlib import Path

import requests

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai


# ==========================================
# CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "Backend"
FRONTEND_DIR = BASE_DIR / "Frontend"

load_dotenv(BACKEND_DIR / ".env")

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")

GEMINI_MODEL = "gemini-flash-lite-latest"

MURF_URL = "https://global.api.murf.ai/v1/speech/stream"

client = (
    genai.Client(api_key=GEMINI_API_KEY)
    if GEMINI_API_KEY
    else None
)


# ==========================================
# VOICES AND LOCALES
# ==========================================

VOICES = {
    "English": {
        "Male": "Matthew",
        "Female": "Alicia"
    },
    "Hindi": {
        "Male": "Aman",
        "Female": "Namrita"
    },
    "Tamil": {
        "Male": "Murali",
        "Female": "Iniya"
    },
    "Telugu": {
        "Male": "Zion",
        "Female": "Josie"
    }
}

LOCALES = {
    "English": "en-US",
    "Hindi": "hi-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN"
}


# ==========================================
# PROMPTS
# ==========================================

PROMPTS = {
    "Summary": """
Create an engaging travel guide of approximately 150-200 words
about {place} in {language}.

Include its history, cultural significance, important attractions,
and interesting facts.

Write naturally for a tourist listening to an audio guide.
Use {language} throughout.
Avoid markdown and unnecessary headings.
""",

    "Detailed": """
Create an engaging detailed travel guide of approximately 350-400
words about {place} in {language}.

Include historical background, architecture, cultural significance,
major attractions, interesting facts, visitor information,
and useful travel tips.

Write naturally for a tourist listening to an audio guide.
Use {language} throughout.
Avoid markdown and unnecessary headings.
"""
}


# ==========================================
# FRONTEND
# ==========================================

@app.route("/")
def homepage():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def frontend_asset(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ==========================================
# AUDIO GUIDE API
# ==========================================

@app.route("/generate-audio-guide", methods=["POST"])
def generate_audio_guide():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A valid JSON request is required"
        }), 400

    place = str(data.get("place", "")).strip()
    answer_type = str(data.get("answerType", "")).strip()
    language = str(data.get("language", "")).strip()

    voice_id = str(data.get("voiceId", "")).strip()
    locale = str(data.get("locale", "")).strip()

    if not place or not answer_type or not language:
        return jsonify({
            "error": "Destination, guide type, and language are required"
        }), 400

    if answer_type not in PROMPTS:
        return jsonify({
            "error": "Unsupported guide type"
        }), 400

    if language not in VOICES:
        return jsonify({
            "error": "Unsupported language"
        }), 400

    if locale != LOCALES[language]:
        return jsonify({
            "error": "Invalid language locale"
        }), 400

    allowed_voices = VOICES[language].values()

    if voice_id not in allowed_voices:
        return jsonify({
            "error": "Invalid voice selection"
        }), 400

    if client is None:
        return jsonify({
            "error": "Gemini API key is not configured"
        }), 500

    if not MURF_API_KEY:
        return jsonify({
            "error": "Murf API key is not configured"
        }), 500

    prompt = PROMPTS[answer_type].format(
        place=place,
        language=language
    )

    # --------------------------------------
    # STEP 1: GEMINI TEXT GENERATION
    # --------------------------------------

    try:
        app.logger.info("Generating guide for %s", place)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )

        description = response.text

        if not description:
            return jsonify({
                "error": "Gemini returned an empty response"
            }), 502

    except Exception:
        app.logger.exception("Gemini generation failed")

        return jsonify({
            "error": "Gemini could not generate the travel guide"
        }), 502

    # --------------------------------------
    # STEP 2: MURF FALCON AUDIO GENERATION
    # --------------------------------------

    payload = {
        "voice_id": voice_id,
        "text": description,
        "locale": locale,
        "model": "FALCON",
        "format": "MP3",
        "sampleRate": 24000,
        "channelType": "MONO"
    }

    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json"
    }

    audio_base64 = None
    audio_error = None

    try:
        app.logger.info(
            "Generating Murf audio using voice %s",
            voice_id
        )

        with tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        ) as temp_audio:

            audio_path = Path(temp_audio.name)

        try:
            with requests.post(
                MURF_URL,
                headers=headers,
                json=payload,
                stream=True,
                timeout=(15, 180)
            ) as murf_response:

                if murf_response.status_code != 200:
                    error_body = murf_response.text[:1000]

                    raise RuntimeError(
                        f"Murf HTTP {murf_response.status_code}: "
                        f"{error_body}"
                    )

                total_bytes = 0

                with open(audio_path, "wb") as audio_file:

                    for chunk in murf_response.iter_content(
                        chunk_size=8192
                    ):
                        if chunk:
                            audio_file.write(chunk)
                            total_bytes += len(chunk)

                if total_bytes == 0:
                    raise RuntimeError(
                        "Murf returned an empty audio file"
                    )

            with open(audio_path, "rb") as audio_file:
                audio_base64 = base64.b64encode(
                    audio_file.read()
                ).decode("utf-8")

            app.logger.info(
                "Murf audio generated successfully: %s bytes",
                total_bytes
            )

        finally:
            if audio_path.exists():
                audio_path.unlink()

    except Exception as error:
        app.logger.exception("Murf audio generation failed")

        audio_error = str(error)[:500]

    # --------------------------------------
    # STEP 3: RESPONSE TO EXISTING FRONTEND
    # --------------------------------------

    return jsonify({
        "description": description,
        "audioBase64": audio_base64,
        "audioError": audio_error
    }), 200


# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )