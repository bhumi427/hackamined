from llm_wrapper import generate_text

def generate_script(text):

    prompt = f"""
Convert this research paper into a video storyboard.

Return JSON with:
scene_id
script
visual_description
duration

Text:
{text}
"""

    response = generate_text(prompt)

    return response