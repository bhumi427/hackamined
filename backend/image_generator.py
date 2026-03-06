import os
import requests
from urllib.parse import quote_plus
from dotenv import load_dotenv

# ensure environment variables are loaded
load_dotenv()

# delay import of LLM helper to avoid module errors in environments without dependencies
try:
    from backend.llm_wrapper import generate_text
except ImportError:
    generate_text = None

# a small list of stopwords for naive keyword extraction
_STOPWORDS = set([
    'the', 'and', 'of', 'in', 'to', 'a', 'for', 'with', 'on', 'is',
    'an', 'by', 'from', 'as', 'that', 'this', 'it', 'at', 'these',
    'each', 'their', 'its', 'are', 'be', 'which', 'into', 'per',
    'are', 'or', 'such'
])

def _extract_keywords(text, max_terms=6):
    """Naively pull a few non‑stopword terms from the description."""
    words = []
    for token in text.replace('.', ' ').replace(',', ' ').split():
        w = token.strip().lower()
        if w and w not in _STOPWORDS:
            words.append(w)
        if len(words) >= max_terms:
            break
    return ','.join(words) if words else text


def expand_visual_description(short_description):
    """
    Use LLM to expand a short visual description into a more detailed one and
    derive a concise keyword query for image searches.

    Returns a tuple (detailed_description, keyword_query).
    """
    # if the LLM helper isn't available, fall back to simple keywords
    if generate_text is None:
        return short_description, _extract_keywords(short_description)

    prompt = f"""
You are an expert at crafting text for AI image generation.

Input: "{short_description}"

Tasks:
1. Produce a detailed, vivid description (50-100 words) suitable for
   high-quality image-generation tools (e.g., DALL·E, Midjourney).
2. Also output a concise comma-separated keyword query (5-10 words) that
   captures the core visual concepts for searching photo libraries.

Format output as two parts separated by a line containing the word
"===KEYWORDS===":
<detailed description text>
===KEYWORDS===
<keyword1, keyword2, keyword3>

Only output what is asked for; do not include extra explanation.
"""
    try:
        resp = generate_text(prompt)
        if resp:
            parts = resp.split('===KEYWORDS===')
            if len(parts) == 2:
                detailed = parts[0].strip()
                keywords = parts[1].strip()
                return detailed or short_description, keywords or short_description
        # fallback if format unrecognized
        return resp.strip() or short_description, short_description
    except Exception as e:
        print(f"Error expanding description: {e}")
        return short_description, short_description

import base64

HF_API_KEY = os.getenv("HF_API_KEY")

def generate_flux_image(prompt):
    """
    Generate an image using HuggingFace FLUX model.
    Returns a base64 image or saved local path.
    """

    url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt
    }

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


def get_scene_images(query, scene_id, num_images=1):
    # Use FLUX generation for first two scenes
    if scene_id in [1, 2]:

        print("Using HuggingFace FLUX generation")

        detailed_query, _ = expand_visual_description(query)

        flux_image = generate_flux_image(detailed_query)

        if flux_image:
            return [flux_image]
    """
    Fetch images from Pexels API based on expanded visual description.
    Includes better error handling and local fallbacks.
    """
    images = []

    # First expand the visual description using LLM
    detailed_query, keyword_query = expand_visual_description(query)
    print(f"Original: {query}")
    print(f"Expanded: {detailed_query}")
    print(f"Keywords: {keyword_query}")

    # use the keyword query for photo library searches; if it is empty fall back to detailed text
    clean_query = keyword_query if keyword_query else detailed_query
    clean_query = clean_query.strip()

    # Use Pexels API with your key from env
    try:
        pexels_api_key = os.getenv("PEXELS_API_KEY")
        if not pexels_api_key:
            raise RuntimeError("PEXELS_API_KEY not set in environment")
        headers = {"Authorization": pexels_api_key}
        # URL-encode query to avoid invalid characters
        encoded = quote_plus(clean_query)
        search_url = f"https://api.pexels.com/v1/search?query={encoded}&per_page={num_images}&orientation=landscape"
        print(f"Trying Pexels API: {search_url}")
        response = requests.get(search_url, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            photos = data.get('photos', [])
            print(f"Pexels returned {len(photos)} photos")

            if photos:
                images = [photo['src']['large'] for photo in photos[:num_images]]
                print("Using Pexels images")
                return images
        else:
            print(f"Pexels API error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Pexels API connection failed: {e}")

    # Fallback: Use Unsplash with expanded description
    try:
        print("Trying Unsplash fallback...")
        encoded_uns = quote_plus(clean_query.replace(' ', ','))
        for i in range(num_images):
            url = f"https://source.unsplash.com/featured/800/450/?{encoded_uns}"
            images.append(url)
        print("Using Unsplash images")
        return images
    except Exception as e:
        print(f"Unsplash fallback failed: {e}")

    # Final fallback: Use local placeholder images or generic working URLs
    print("Using final fallback images...")
    fallback_urls = [
        "https://picsum.photos/800/450?random=1",
        "https://picsum.photos/800/450?random=2",
        "https://picsum.photos/800/450?random=3",
        "https://picsum.photos/800/450?random=4",
        "https://picsum.photos/800/450?random=5"
    ]

    for i in range(num_images):
        images.append(fallback_urls[i % len(fallback_urls)])

    print("Using Lorem Picsum fallback images")
    return images