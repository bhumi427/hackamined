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
from backend.script_agent import generate_script, generate_summary
from backend.image_generator import get_scene_images


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

if 'last_file' not in st.session_state:
    st.session_state.last_file = None


if uploaded_file:

    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'scenes_visible' not in st.session_state:
        st.session_state.scenes_visible = False

    if uploaded_file.name != st.session_state.last_file:

        st.session_state.last_file = uploaded_file.name

        for f_name in [CACHE_FILE, "server.json", "summary.txt"]:
            if os.path.exists(f_name):
                try:
                    os.remove(f_name)
                except:
                    pass

        st.session_state.summary = None
        st.session_state.scenes_visible = False
        st.rerun()

    text = extract_text(uploaded_file)

    if st.session_state.summary is None and os.path.exists("summary.txt"):
        try:
            with open("summary.txt") as f:
                st.session_state.summary = f.read()
        except:
            pass

    st.subheader("Step 1: Review Summary")

    if st.session_state.summary is None:

        if st.button("Generate Summary"):

            if os.path.exists("summary.txt"):

                with open("summary.txt") as f:
                    st.session_state.summary = f.read()

                st.success("Loaded existing summary!")
                st.rerun()

            with st.spinner("Generating summary..."):

                summary = generate_summary(text)
                st.session_state.summary = summary

                with open("summary.txt", "w") as f:
                    f.write(summary)

            with st.spinner("Generating scenes..."):

                script = generate_script(summary)

                try:

                    data = json.loads(script)

                    with open("server.json", "w") as f:
                        json.dump(data, f, indent=2)

                except:

                    cleaned = script.replace("```json", "").replace("```", "")
                    data = json.loads(cleaned)

                    with open("server.json", "w") as f:
                        json.dump(data, f, indent=2)

            st.rerun()

        st.stop()

    else:

        st.session_state.summary = st.text_area(
            "Overall Summary (Edit if needed):",
            value=st.session_state.summary,
            height=250
        )

        with open("summary.txt", "w") as f:
            f.write(st.session_state.summary)

    st.subheader("Step 2: Generate Scenes")

    col1, col2 = st.columns(2)

    with col1:
        generate_btn = st.button("Load Scenes from Cache")

    with col2:
        regenerate_btn = st.button("Regenerate Scenes")

    data = None

    if st.session_state.scenes_visible and os.path.exists("server.json"):
        with open("server.json") as f:
            data = json.load(f)

    if generate_btn:

        if os.path.exists("server.json"):

            with open("server.json") as f:
                data = json.load(f)

            st.session_state.scenes_visible = True
            st.success("Scenes loaded from server.json")

        else:

            st.warning("No scenes found in server.json.")

    if regenerate_btn:

        if os.path.exists("server.json"):
            os.remove("server.json")

        with st.spinner("Generating scenes..."):

            script = generate_script(st.session_state.summary)

        cleaned = script.replace("```json", "").replace("```", "")

        data = json.loads(cleaned)

        with open("server.json", "w") as f:
            json.dump(data, f, indent=2)

        st.session_state.scenes_visible = True

        st.success("Scenes regenerated!")

    if data:

        scenes = data["scenes"]

        st.success(f"{len(scenes)} scenes loaded")

        scene_titles = [f"Scene {s['scene_id']}" for s in scenes]

        tabs = st.tabs(scene_titles)

        for i, tab in enumerate(tabs):

            scene = scenes[i]

            with tab:

                col1, col2 = st.columns(2)

                with col1:

                    st.subheader("Script")

                    edited_script = st.text_area(
                        "Edit script:",
                        value=scene["script"],
                        height=150,
                        key=f"script_{scene['scene_id']}",
                        label_visibility="collapsed"
                    )

                with col2:

                    st.subheader("Visual Description")

                    vis_val_key = f"vis_val_{scene['scene_id']}"

                    if vis_val_key not in st.session_state:
                        st.session_state[vis_val_key] = scene["visual_description"]

                    visual_description = st.text_area(
                        "Edit visual description:",
                        value=st.session_state[vis_val_key],
                        height=150,
                        label_visibility="collapsed"
                    )

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:

                    if st.button(
                        f"Generate Visual Desc (Scene {scene['scene_id']})",
                        key=f"update_{scene['scene_id']}"
                    ):

                        from backend.llm_wrapper import generate_text

                        prompt = f"""
Create a visual description for this script:

{edited_script}

Return 2 sentences describing what should appear in the scene.
"""

                        new_visual = generate_text(prompt).strip()

                        data["scenes"][i]["visual_description"] = new_visual

                        with open("server.json", "w") as f:
                            json.dump(data, f, indent=2)

                        st.session_state[vis_val_key] = new_visual

                        st.success("Visual description updated!")

                        st.rerun()

                with col_btn2:

                    if st.button(
                        f"Save Edits (Scene {scene['scene_id']})",
                        key=f"save_{scene['scene_id']}"
                    ):

                        data["scenes"][i]["script"] = edited_script
                        data["scenes"][i]["visual_description"] = visual_description

                        with open("server.json", "w") as f:
                            json.dump(data, f, indent=2)

                        st.success("Scene saved!")

                if st.button(
                    f"Generate Image (Scene {scene['scene_id']})",
                    key=f"gen_img_{scene['scene_id']}"
                ):

                    with st.spinner("Generating image..."):

                        images = get_scene_images(
                            visual_description,
                            scene["scene_id"]
                        )

                        st.session_state[f"images_{scene['scene_id']}"] = images

                        st.success("Image generated!")

                if f"images_{scene['scene_id']}" in st.session_state:

                    st.subheader("Visual Preview")

                    images = st.session_state[f"images_{scene['scene_id']}"]

                    st.image(images[0], use_container_width=True)

                st.subheader("Audio")

                audio_data = generate_audio(edited_script)

                audio_b64 = base64.b64encode(audio_data).decode()

                audio_url = f"data:audio/mp3;base64,{audio_b64}"

                html = f"""
                <audio id="audio{scene['scene_id']}" src="{audio_url}"></audio>
                <button onclick="document.getElementById('audio{scene['scene_id']}').play()">Play</button>
                <button onclick="document.getElementById('audio{scene['scene_id']}').pause();document.getElementById('audio{scene['scene_id']}').currentTime=0;">Stop</button>
                """

                components.html(html)

                st.write("Duration:", scene["duration"], "seconds")