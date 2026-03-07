import os
import requests
from urllib.parse import quote_plus
from dotenv import load_dotenv
import base64

load_dotenv()

try:
    from backend.llm_wrapper import generate_text
except ImportError:
    generate_text = None

HF_API_KEY = os.getenv("HF_API_KEY")


def expand_visual_description(short_description):
    """
    Expand a short visual description into a detailed prompt
    and a short keyword query.
    """
    if generate_text is None:
        return short_description, short_description

    prompt = f"""
You are an expert at crafting prompts for AI image generation.

Input: "{short_description}"

Create:
1. A detailed image generation prompt (50 words)
2. A short keyword query for stock photo search

Return format:

<detailed description>
===KEYWORDS===
<keyword1, keyword2, keyword3>
"""

    try:
        resp = generate_text(prompt)
        parts = resp.split("===KEYWORDS===")
        if len(parts) == 2:
            detailed = parts[0].strip()
            keywords = parts[1].strip()
            return detailed, keywords
    except Exception:
        pass

    return short_description, short_description


# ---------------- HF IMAGE GENERATION ----------------
def generate_flux_image(prompt):
    """
    Generate an image using HuggingFace FLUX model.
    Returns the saved local filename.
    """
    url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"inputs": prompt}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        image_bytes = response.content
        filename = f"flux_scene_{abs(hash(prompt))}.png"
        with open(filename, "wb") as f:
            f.write(image_bytes)
        return filename
    else:
        print("FLUX generation failed:", response.text)
        return None


# ---------------- MAIN FUNCTION ----------------
def get_scene_images(query, scene_id, num_images=1):
    """
    Returns a list of local image paths for the given scene.
    Uses HuggingFace FLUX for first two scenes, Pexels for others.
    """
    # -------- HuggingFace for first two scenes --------
    if scene_id in [1, 2]:
        print("Using HuggingFace FLUX")
        detailed_query, _ = expand_visual_description(query)
        flux_img = generate_flux_image(detailed_query)
        if flux_img:
            return [flux_img]

    # -------- PEXELS for remaining scenes --------
    try:
        detailed_query, keyword_query = expand_visual_description(query)
        pexels_api_key = os.getenv("PEXELS_API_KEY")
        headers = {"Authorization": pexels_api_key}

        encoded = quote_plus(keyword_query)
        url = f"https://api.pexels.com/v1/search?query={encoded}&per_page=1&orientation=landscape"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            photos = response.json().get("photos", [])
            if photos:
                photo_url = photos[0]["src"]["large"]
                # Download and save locally
                img_response = requests.get(photo_url)
                if img_response.status_code == 200:
                    filename = f"pexels_scene_{scene_id}_{abs(hash(photo_url))}.jpg"
                    with open(filename, "wb") as f:
                        f.write(img_response.content)
                    return [filename]
    except Exception as e:
        print("Pexels failed:", e)

    # fallback if all else fails
    return ["https://picsum.photos/800/450"]