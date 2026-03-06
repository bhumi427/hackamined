import os
import requests

# some environments may not have the google generative client installed
try:
    import google.generativeai as genai
except ImportError:
    genai = None

from dotenv import load_dotenv

load_dotenv()

provider = os.getenv("LLM_PROVIDER")

AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")


def call_aipipe(prompt):

    url = "https://aipipe.org/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {AIPIPE_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    result = response.json()

    print(result)   # debug

    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    else:
        return f"API Error: {result}"
    

def call_gemini(prompt):
    if genai is None:
        raise RuntimeError("google.generativeai package not available")

    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text


def generate_text(prompt):

    if provider == "aipipe":
        return call_aipipe(prompt)

    elif provider == "gemini":
        return call_gemini(prompt)  # may raise if google library missing