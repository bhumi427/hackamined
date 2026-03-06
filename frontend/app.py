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
from backend.video_generator import generate_voice, create_scene, export_final_video


def generate_audio(script):
    tts = gTTS(script)
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    return audio_bytes.getvalue()


st.set_page_config(page_title="Agentic Video Editor", layout="wide")
st.title("🎬 Agentic Video Editor")

CACHE_FILE = "scenes.json"

uploaded_file = st.file_uploader("Upload Document", type=["pdf"])

if uploaded_file:

    text = extract_text(uploaded_file)

    col1, col2 = st.columns(2)

    with col1:
        generate_btn = st.button("Generate Scenes")

    with col2:
        regenerate_btn = st.button("Regenerate Scenes")

    data = None

    if os.path.exists(CACHE_FILE) and not regenerate_btn:
        with open(CACHE_FILE) as f:
            data = json.load(f)

    if generate_btn or regenerate_btn:

        script = generate_script(text)

        try:
            data = json.loads(script)

            with open(CACHE_FILE, "w") as f:
                json.dump(data, f, indent=2)

        except:
            st.error("Failed to parse LLM JSON response")
            st.write(script)

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

                audio_data = generate_audio(scene["script"])
                audio_b64 = base64.b64encode(audio_data).decode()
                audio_url = f"data:audio/mp3;base64,{audio_b64}"

                html = f"""
                <audio id="audio{scene['scene_id']}" src="{audio_url}"></audio>
                <button onclick="document.getElementById('audio{scene['scene_id']}').play()">Play</button>
                <button onclick="document.getElementById('audio{scene['scene_id']}').pause(); document.getElementById('audio{scene['scene_id']}').currentTime=0;">Stop</button>
                """

                components.html(html)

                st.write("Duration:", scene["duration"], "seconds")

        st.divider()

        if st.button("🎬 Generate Video"):

            os.makedirs("temp_audio", exist_ok=True)
            os.makedirs("temp_scenes", exist_ok=True)

            scene_files = []

            with st.spinner("Generating video..."):

                for scene in scenes:

                    scene_id = scene["scene_id"]
                    script = scene["script"]

                    images = get_scene_images(scene["visual_description"])
                    image = images[0]

                    audio_file = f"temp_audio/scene_{scene_id}.mp3"
                    scene_video = f"temp_scenes/scene_{scene_id}.mp4"

                    generate_voice(script, audio_file)
                    create_scene(image, audio_file, scene_video)

                    scene_files.append(scene_video)

                export_final_video(scene_files)

            st.success("Video Generated!")
            st.video("final_video.mp4")