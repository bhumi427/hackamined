import os
from dotenv import load_dotenv
import requests
import base64

# Debug: current folder
print("Current working directory:", os.getcwd())

# Debug: does .env exist here?
env_path = ".env"
print(f".env exists? {os.path.exists(env_path)}")

# Load .env explicitly
load_dotenv(dotenv_path=env_path)

# Get the HF token
HF_API_KEY = os.getenv("HF_API_KEY")
print("HF_API_KEY loaded:", HF_API_KEY is not None)

if not HF_API_KEY:
    print("HF_API_KEY is missing! Check your .env file.")
    exit(1)

# Now test FLUX API
prompt = "A beautiful snowy mountain landscape"
url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
headers = {"Authorization": f"Bearer {HF_API_KEY}"}
payload = {"inputs": prompt, "options": {"wait_for_model": True}}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print("Status code:", response.status_code)
    print("Response snippet:", response.text[:500])
except Exception as e:
    print("Request failed:", e)