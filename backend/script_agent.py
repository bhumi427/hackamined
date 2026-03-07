from backend.llm_wrapper import generate_text


def generate_summary(text, level="Beginner-friendly"):
    """
    You are an expert at summarizing documents for educational videos.

    Please provide a comprehensive but concise overall summary of the following document.
    Focus on the most important ideas that should be covered in a short educational video. 
    Make sure the flow is logical and clear.
    Generate a summary of the text.
    level: "Beginner-friendly" or "Expert-level"
    """
    if level == "Beginner-friendly":
        prompt = f"Summarize the following text in simple language suitable for a beginner:\n{text}"
    else:  # Expert-level
        prompt = f"Summarize the following text in a detailed, expert-level manner:\n{text}"

    # Call your LLM wrapper
    from backend.llm_wrapper import generate_text
    summary = generate_text(prompt)
    return summary


def generate_script(text):

    # For the script length calculation, we use the length of the summary
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
- Include a field 'source_text' which is a small snippet (first 20–30 words) from the document used to generate this scene.
- Total number of scenes: {num_scenes}
- Each scene duration: {scene_duration} seconds
- Each narration should be about 20–30 words
- Scenes should summarize the most important ideas from the document
- For traceability, include a "source_text" field containing 20-30 words **directly from the original document** that were used to generate this scene.

Return ONLY valid JSON in this format:

{{
 "scenes":[
  {{
   "scene_id":1,
   "script":"scene narration",
   "visual_description":"what appears visually",
   "duration":{scene_duration},
   "source_text":"exact snippet from original document"
  }}
 ]
}}

Document:
{text[:5000]}
"""

    response = generate_text(prompt)

    return response