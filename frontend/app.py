# import streamlit as st
# import sys
# import os
# import json

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from backend.parser import extract_text
# from backend.script_agent import generate_script
# from backend.image_generator import get_scene_image

# st.set_page_config(page_title="Agentic Video Editor", layout="wide")

# st.title("🎬 Agentic Video Editor")
# st.write("Upload a document to generate a storyboard.")

# uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])


# if uploaded_file:

#     text = extract_text(uploaded_file)

#     if st.button("Generate Script"):

#         response = generate_script(text)

#         try:
#             data = json.loads(response)

#             scenes = data["scenes"]

#             st.success(f"Generated {len(scenes)} scenes")

#             scene_titles = [f"Scene {s['scene_id']}" for s in scenes]

#             tabs = st.tabs(scene_titles)

#             for i, tab in enumerate(tabs):

#                 scene = scenes[i]

#                 with tab:
#                     image_url = get_scene_image(scene["visual_description"])

#                     st.image(image_url)

#                     col1, col2 = st.columns(2)

#                     with col1:
#                         st.subheader("🎙 Script")
#                         st.write(scene["script"])

#                     with col2:
#                         st.subheader("🎥 Visual Description")
#                         st.write(scene["visual_description"])

#                     st.write("⏱ Duration:", scene["duration"], "seconds")

#         except:
#             st.error("Failed to parse JSON response")
#             st.write(response)


import streamlit as st
import sys
import os
import json
import io
import base64
from gtts import gTTS
import streamlit.components.v1 as components

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.parser import extract_text
from backend.script_agent import generate_script
from backend.image_generator import get_scene_images


def generate_audio(script):
    tts = gTTS(script)
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    return audio_bytes.getvalue()


st.set_page_config(page_title="Agentic Video Editor", layout="wide")

st.title("🎬 Agentic Video Editor")

CACHE_FILE = "scenes.json"  # stores a dict mapping filename->scene data

uploaded_file = st.file_uploader("Upload Document", type=["pdf"])

# remember the last uploaded filename so we can detect when the user
# switches to a different PDF and clear the cache accordingly.
if 'last_file' not in st.session_state:
    st.session_state.last_file = None


if uploaded_file:

    # if a new file is uploaded, delete any previous cache so we don't show
    # the old scenes
    if uploaded_file.name != st.session_state.last_file:
        st.session_state.last_file = uploaded_file.name
        if os.path.exists(CACHE_FILE):
            try:
                os.remove(CACHE_FILE)
            except Exception:
                pass

    text = extract_text(uploaded_file)

    col1, col2 = st.columns(2)

    with col1:
        generate_btn = st.button("Generate Scenes")

    with col2:
        regenerate_btn = st.button("Regenerate Scenes")

    data = None

    # Handle Generate Scenes button - only load from server.json, no API call
    if generate_btn:
        if os.path.exists("server.json"):
            try:
                with open("server.json") as f:
                    data = json.load(f)
                st.success("Scenes loaded from server.json")
            except Exception:
                st.error("Failed to load scenes from server.json")
        else:
            st.warning("No scenes found in server.json. Use 'Regenerate Scenes' to generate new content.")

    # Handle Regenerate Scenes button - call API and save to server.json
    elif regenerate_btn:
        with st.spinner("Regenerating scenes..."):
            script = generate_script(text)
        try:
            data = json.loads(script)
            with open("server.json", "w") as f:
                json.dump(data, f, indent=2)
            st.success("Scenes regenerated and saved to server.json!")
        except Exception:
            # clean up any markdown formatting from the LLM response
            cleaned_script = script.strip()
            if cleaned_script.startswith('```json'):
                cleaned_script = cleaned_script[7:]
            if cleaned_script.startswith('```'):
                cleaned_script = cleaned_script[3:]
            if cleaned_script.endswith('```'):
                cleaned_script = cleaned_script[:-3]
            cleaned_script = cleaned_script.strip()
            
            # try parsing the cleaned version
            try:
                data = json.loads(cleaned_script)
                with open("server.json", "w") as f:
                    json.dump(data, f, indent=2)
                st.success("Scenes regenerated and saved to server.json!")
            except Exception:
                # save raw cleaned output to server.json
                try:
                    with open("server.json", "w") as sf:
                        sf.write(cleaned_script)
                    st.info("Raw LLM output saved to server.json")
                except Exception as _:
                    pass

    # If no button pressed and we have cached data, load it
    elif os.path.exists("server.json"):
        try:
            with open("server.json") as f:
                data = json.load(f)
        except Exception:
            pass

    # Display scenes
    if data:

        scenes = data["scenes"]

        st.success(f"{len(scenes)} scenes loaded")

        scene_titles = [f"Scene {s['scene_id']}" for s in scenes]

        tabs = st.tabs(scene_titles)

        for i, tab in enumerate(tabs):

            scene = scenes[i]

            with tab:

                st.subheader("Visual Options")

                images = get_scene_images(scene["visual_description"])

                cols = st.columns(3)

                for j, img in enumerate(images):
                    cols[j].image(img)

                st.divider()

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Script")
                    st.write(scene["script"])

                with col2:
                    st.subheader("Visual Description")
                    st.write(scene["visual_description"])

                st.subheader("Audio")

                # Audio playback
                audio_data = generate_audio(scene["script"])
                audio_b64 = base64.b64encode(audio_data).decode()
                audio_url = f"data:audio/mp3;base64,{audio_b64}"
                html = f"""
                <style>
                button {{
                    background-color: #4CAF50;
                    border: none;
                    color: white;
                    padding: 10px 20px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    margin: 4px 2px;
                    cursor: pointer;
                    border-radius: 4px;
                }}
                button:hover {{
                    background-color: #45a049;
                }}
                </style>
                <audio id="audio{scene['scene_id']}" src="{audio_url}"></audio>
                <button onclick="document.getElementById('audio{scene['scene_id']}').play()">Play</button>
                <button onclick="document.getElementById('audio{scene['scene_id']}').pause(); document.getElementById('audio{scene['scene_id']}').currentTime=0;">Stop</button>
                """
                components.html(html)

                st.write("Duration:", scene["duration"], "seconds")