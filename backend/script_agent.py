from backend.llm_wrapper import generate_text


def generate_script(text):

    word_count = len(text.split())

    # Estimate video length based on document size
    if word_count < 800:
        video_length = 60
    elif word_count < 2000:
        video_length = 120
    else:
        video_length = 180

    scene_duration = 10

    num_scenes = video_length // scene_duration

    # Keep scenes manageable for editor
    num_scenes = max(6, min(num_scenes, 12))

    prompt = f"""
You are an AI video storyboard generator.

The input may be any type of document such as:
- research paper
- report
- lecture notes
- policy brief
- financial report

Your job is to convert the content into a clear educational video storyboard.

Rules:
- Total number of scenes: {num_scenes}
- Each scene duration: {scene_duration} seconds
- Each narration should be about 20–30 words
- Scenes should summarize the most important ideas from the document
- Make the explanation simple and clear

Return ONLY valid JSON in this format:

{{
 "scenes":[
  {{
   "scene_id":1,
   "script":"scene narration",
   "visual_description":"what should appear visually",
   "duration":{scene_duration}
  }}
 ]
}}

Document:
{text[:5000]}
"""

    response = generate_text(prompt)

    return response