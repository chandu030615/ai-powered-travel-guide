
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / "Backend" / ".env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: Gemini API key not found")
    raise SystemExit(1)

client = genai.Client(api_key=api_key)

models_to_test = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-3-flash-preview"
]

for model_name in models_to_test:
    print(f"\nTesting: {model_name}")

    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Write two short sentences about the Taj Mahal."
        )

        if response.text:
            print("STATUS: SUCCESS")
            print("Response:", response.text)
            break

        print("STATUS: Empty response")

    except Exception as error:
        print("STATUS: FAILED")
        print("Error:", error)
