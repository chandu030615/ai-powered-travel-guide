# AI-Powered Travel Guide Using Murf.AI

## 1. Project Overview

**Project type:** Web-based AI travel information and audio narration application.

Users enter a tourist destination, select a guide length, language, and voice, and receive a written travel guide plus spoken narration.

The implementation follows the supplied workshop approach: Flask backend, Google Gemini for text generation, and Murf Falcon for speech synthesis.

## 2. Goals

- Generate historical and travel information about a selected place.
- Provide Summary and Detailed guide options.
- Support English, Hindi, Tamil, and Telugu.
- Offer supported male and female voice options.
- Display the generated transcript.
- Provide audio playback controls.
- Preserve the original workshop frontend and its request/response contract.

## 3. Scope

### In Scope
- Destination input and guide customization.
- Flask `POST /generate-audio-guide` endpoint.
- JSON request parsing using `request.json`.
- Gemini text generation using `gemini-2.5-flash`.
- Murf Falcon speech generation.
- Temporary MP3 handling.
- Base64 audio encoding.
- JSON response containing description and audio.
- Transcript display and audio playback.
- API keys configured through environment variables.

### Out of Scope
Unless the workshop source is explicitly extended, do not add authentication, databases, booking, payment, itinerary management, React, Next.js, FastAPI, or alternative AI/audio providers.

## 4. Technology Stack

| Layer | Technology / Method |
|---|---|
| Frontend | Original workshop HTML, CSS, JavaScript |
| Backend | Python Flask |
| CORS | Flask-CORS |
| Text generation | Google GenAI Python SDK |
| Model | `gemini-2.5-flash` |
| Speech synthesis | Murf Falcon API |
| HTTP client | Python `requests` |
| Environment | `python-dotenv` |
| Temporary audio | Python `tempfile` |
| Audio encoding | Python `base64` |
| API response | Flask `jsonify()` |

## 5. User Flow

1. User opens the web application.
2. User enters a tourist destination.
3. User selects Summary or Detailed.
4. User selects English, Hindi, Tamil, or Telugu.
5. User selects a supported voice.
6. Original frontend sends a JSON POST request to `/generate-audio-guide`.
7. Flask extracts fields using `request.json`.
8. Gemini generates the travel description using the selected prompt.
9. Murf Falcon converts the description to speech.
10. Backend saves the audio to a temporary MP3 file.
11. Backend Base64-encodes the audio and returns it with the description as JSON.
12. Original frontend displays the transcript and audio player.

## 6. Functional Requirements

### FR-01: Destination
Allow the user to enter a tourist place, such as Taj Mahal, Paris, or Goa.

### FR-02: Guide Length
- `Summary`: prompt target of approximately 200 words.
- `Detailed`: prompt target of approximately 400 words.

These are prompt targets, not strict word-count guarantees.

### FR-03: Languages
Support English, Hindi, Tamil, and Telugu as specified in the workshop.

### FR-04: Voice
The frontend sends `voiceId` and `locale`; the backend passes them to Murf Falcon. Use only voice IDs and locale combinations confirmed to be supported. Preserve the original frontend's voice options.

### FR-05: Gemini Description
Use the Google GenAI SDK and the workshop model `gemini-2.5-flash`. Select a prompt from a `PROMPTS` dictionary based on Summary or Detailed, formatted with the destination and language.

Workshop method:

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)
```

Use `response.text` as the generated description.

### FR-06: Murf Speech
Use the Murf Falcon endpoint:

`https://global.api.murf.ai/v1/speech/stream`

Use Python `requests` and the server-side Murf API key. Implement `generate_speech(text, voice_id, locale)`, create a temporary `.mp3` using `tempfile.NamedTemporaryFile`, and save the returned audio to that file.

### FR-07: API Response
Return JSON containing:
- `description`: generated travel guide text.
- `audio`: Base64-encoded audio.
- `audioFormat`: audio MIME type such as `audio/mpeg`, if expected by the original frontend.

Response property names must match the actual original frontend contract.

### FR-08: Playback and Transcript
Use the original frontend's transcript display and audio player. Do not replace or redesign them.

### FR-09: Error Handling
Return useful JSON errors and appropriate HTTP status codes for invalid input or upstream API failures. Never expose API keys or sensitive provider details to the browser.

## 7. API Contract

**Endpoint:** `POST /generate-audio-guide`

The workshop request fields are:

```json
{
  "place": "Taj Mahal",
  "answerType": "Summary",
  "language": "English",
  "voiceId": "<supported Murf voice ID>",
  "locale": "<supported locale>"
}
```

Voice IDs and locale values must be taken from the original workshop frontend and verified with Murf. Do not invent replacements.

Illustrative successful response:

```json
{
  "description": "Generated travel guide text...",
  "audio": "<base64-encoded MP3 data>",
  "audioFormat": "audio/mpeg"
}
```

Adjust response keys only when the original frontend source requires it.

## 8. Prompt Requirements

Maintain a `PROMPTS` dictionary with Summary and Detailed templates. Format them with `place` and `language`.

The Summary prompt should request concise history, significance, attractions, and interesting facts. The Detailed prompt should request a fuller guide with relevant context and travel information, consistent with the workshop prompt.

Use the specified Gemini SDK method and model above.

## 9. Architecture

```text
Original Browser Frontend
        |
        | POST /generate-audio-guide (JSON)
        v
Flask API -> request.json
        |
        +--> Gemini 2.5 Flash -> Travel description
        |
        +--> Murf Falcon -> Speech audio
        |
        +--> Temporary MP3
        |
        +--> Base64 encoding
        |
        v
JSON response: description + audio
        |
        v
Original transcript and audio player
```

## 10. Suggested Project Structure

Preserve the original workshop filenames and layout if supplied. A compatible structure may be:

```text
AI-Travel-Guide/
├── app.py
├── requirements.txt
├── .env
├── .gitignore
├── templates/
│   └── index.html
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    │   └── index.js
    └── images/
```

This is illustrative; do not replace existing frontend files just to match it.

## 11. Environment Configuration

Use server-side environment variables:

```env
GEMINI_API_KEY=your_gemini_api_key
MURF_API_KEY=your_murf_api_key
```

Never commit `.env` or expose provider keys in frontend code. Add `.env` to `.gitignore`.

## 12. Dependencies

```text
flask
flask-cors
google-genai
requests
python-dotenv
```

## 13. Non-Functional Requirements

- Keep the implementation beginner-friendly and workshop-aligned.
- Preserve the original frontend source and behavior.
- Keep credentials server-side.
- Handle missing fields and provider errors gracefully.
- Ensure audio is returned in a format the original frontend can play.
- Clean up temporary audio files only after their contents have been read for the response.
- Test language and voice combinations; do not assume unsupported combinations work.

## 14. Acceptance Criteria

- [ ] Flask starts successfully.
- [ ] Original workshop homepage loads.
- [ ] Original CSS and JavaScript load without errors.
- [ ] Frontend sends the expected JSON fields.
- [ ] Flask receives and parses the request.
- [ ] Gemini `gemini-2.5-flash` generates a description.
- [ ] Summary and Detailed prompt paths work.
- [ ] Murf Falcon generates speech for a supported voice/locale.
- [ ] Audio is saved temporarily as MP3.
- [ ] Audio is Base64-encoded and returned in JSON.
- [ ] Original frontend displays the transcript.
- [ ] Original audio player plays the generated audio.
- [ ] Supported language/voice combinations are tested.
- [ ] API keys are not exposed or committed.
- [ ] Errors are handled without leaking secrets.

## 15. Instructions for AI Coding Assistants

1. Read the workshop source and original frontend files first.
2. Treat those materials as authoritative.
3. Do not redesign, rewrite, replace, or modernize the frontend.
4. Use Flask, `request.json`, Google GenAI `client.models.generate_content`, `gemini-2.5-flash`, Murf Falcon, `requests`, `tempfile`, `base64`, and `jsonify` as specified.
5. Preserve frontend request fields and expected response keys.
6. Make the smallest necessary integration fixes.
7. Explain any proposed deviation and obtain approval before changing the specified approach.
8. Work incrementally, giving exact Windows Git Bash commands and testing each stage before continuing.
9. If original frontend source is missing, request it rather than reconstructing or replacing it.
