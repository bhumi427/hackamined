import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

provider = os.getenv("LLM_PROVIDER")

AIPIPE_KEY = os.getenv("AIPIPE_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")


def call_aipipe(prompt):

    response = requests.post(
        "https://api.aipipe.org/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {AIPIPE_KEY}"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    return response.json()["choices"][0]["message"]["content"]


def call_gemini(prompt):

    genai.configure(api_key=GEMINI_KEY)

    model = genai.GenerativeModel("gemini-pro")

    response = model.generate_content(prompt)

    return response.text


def generate_text(prompt):

    if provider == "aipipe":
        return call_aipipe(prompt)

    elif provider == "gemini":
        return call_gemini(prompt)