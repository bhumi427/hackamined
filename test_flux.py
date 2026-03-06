import os
from dotenv import load_dotenv

print("Current working directory:", os.getcwd())
print(".env exists?", os.path.exists(".env"))

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")
print("HF_API_KEY loaded:", HF_API_KEY)

if not HF_API_KEY:
    raise ValueError("HF_API_KEY not loaded! Check your .env file.")

prompt = "A serene snowy mountain landscape at sunrise"

url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
headers = {"Authorization": f"Bearer {HF_API_KEY}"}
payload = {"inputs": prompt, "options": {"wait_for_model": True}}

response = requests.post(url, headers=headers, json=payload)

print("Status code:", response.status_code)
print("Response text:", response.text[:500])  # print first 500 chars

if response.status_code == 200:
    try:
        result = response.json()
        if "generated_images" in result:
            img_b64 = result["generated_images"][0]
            image_bytes = base64.b64decode(img_b64)
            filename = "flux_test.png"
            with open(filename, "wb") as f:
                f.write(image_bytes)
            print("Image saved as flux_test.png ✅")
        else:
            print("No 'generated_images' in response:", result)
    except Exception as e:
        print("Error parsing JSON:", e)
else:
    print("HF FLUX call failed! Check token or plan.")