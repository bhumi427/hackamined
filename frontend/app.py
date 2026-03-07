import streamlit as st
import sys
import os
import json
import io
import base64
from gtts import gTTS
import streamlit.components.v1 as components

from PIL import Image
from mutagen.mp3 import MP3
import subprocess

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.parser import extract_text
from backend.script_agent import generate_script, generate_summary
from backend.image_generator import get_scene_images

# ----------------- Helper Functions -----------------
def generate_audio(script):
    tts = gTTS(script)
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)
    return audio_bytes.getvalue()

def save_audio_file(audio_bytes, scene_id):
    filename = f"scene_{scene_id}.mp3"
    with open(filename, "wb") as f:
        f.write(audio_bytes)
    return filename

def create_scene_video(images, audio_path, output_path):
    if not images:
        raise ValueError("No images provided for video generation.")

    audio_length = MP3(audio_path).info.length
    num_images = len(images)
    duration_per_image = audio_length / num_images

    resized_images = []
    for img_path in images:
        img = Image.open(img_path)
        w, h = img.size
        w2 = w - w % 2
        h2 = h - h % 2
        if (w2, h2) != (w, h):
            img = img.resize((w2, h2))
            resized_path = f"resized_{os.path.basename(img_path)}"
            img.save(resized_path)
            resized_images.append(resized_path)
        else:
            resized_images.append(img_path)

    input_files = []
    filter_complex = ""
    for i, img in enumerate(resized_images):
        input_files.extend(["-loop", "1", "-t", str(duration_per_image), "-i", img])
        filter_complex += f"[{i}:v]"

    filter_complex += f"concat=n={num_images}:v=1:a=0[outv]"

    cmd = [
        "ffmpeg",
        "-y",
        *input_files,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", f"{num_images}:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]

    subprocess.run(cmd, check=True)

    for img in resized_images:
        if img.startswith("resized_") and os.path.exists(img):
            os.remove(img)

    return output_path

def concatenate_videos(video_files, output_file="final_video.mp4"):
    list_file = "file_list.txt"
    with open(list_file, "w") as f:
        for vf in video_files:
            f.write(f"file '{os.path.abspath(vf)}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_file
    ]
    subprocess.run(cmd, check=True)
    os.remove(list_file)
    return output_file

# ----------------- Streamlit Setup -----------------
st.set_page_config(page_title="Agentic Video Editor", layout="wide")
st.title("🎬 Agentic Video Editor")

CACHE_FILE = "scenes.json"
uploaded_file = st.file_uploader("Upload Document", type=["pdf"])

if 'last_file' not in st.session_state:
    st.session_state.last_file = None

# ----------------- File Upload Handling -----------------
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

    # ----------------- Step 1: Review Summary -----------------
    st.subheader("Step 1: Review Summary")

    # Ask user for summary level
    summary_level = st.radio(
        "Select Summary Level:",
        ("Beginner-friendly", "Expert-level"),
        index=0
    )

    if st.session_state.summary is None:

        if st.button("Generate Summary"):

            if os.path.exists("summary.txt"):
                with open("summary.txt") as f:
                    st.session_state.summary = f.read()
                st.success("Loaded existing summary!")
                st.rerun()

            with st.spinner("Generating summary..."):
                # Pass level to generate_summary
                summary = generate_summary(text, level=summary_level)
                st.session_state.summary = summary
                with open("summary.txt", "w") as f:
                    f.write(summary)

            with st.spinner("Generating scenes..."):
                script = generate_script(text)  # <-- text extracted from PDF
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

    else:
        st.session_state.summary = st.text_area(
            "Overall Summary (Edit if needed):",
            value=st.session_state.summary,
            height=250
        )
        with open("summary.txt", "w") as f:
            f.write(st.session_state.summary)

    # ----------------- Step 2: Generate Scenes -----------------
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

    # ----------------- Display Scenes -----------------
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
                    st.caption(f"Reference snippet: {scene.get('source_text', 'N/A')}")
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
                    if st.button(f"Generate Visual Desc (Scene {scene['scene_id']})", key=f"update_{scene['scene_id']}"):
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
                    if st.button(f"Save Edits (Scene {scene['scene_id']})", key=f"save_{scene['scene_id']}"):
                        data["scenes"][i]["script"] = edited_script
                        data["scenes"][i]["visual_description"] = visual_description
                        with open("server.json", "w") as f:
                            json.dump(data, f, indent=2)
                        st.success("Scene saved!")

                # Generate Image
                if st.button(f"Generate Image (Scene {scene['scene_id']})", key=f"gen_img_{scene['scene_id']}"):
                    with st.spinner("Generating image..."):
                        images = get_scene_images(visual_description, scene["scene_id"])
                        st.session_state[f"images_{scene['scene_id']}"] = images
                        st.success("Image generated!")

                if f"images_{scene['scene_id']}" in st.session_state:
                    st.subheader("Visual Preview")
                    images = st.session_state[f"images_{scene['scene_id']}"]
                    # st.image(images[0], use_container_width=True)
                    st.image(images[0], width=700)  # fixed width, maintains aspect ratio

                # Audio preview
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
                st.write("Duration:", scene.get("duration", "N/A"), "seconds")

                # ----------------- Scene Video & Full Video -----------------
                st.subheader("Scene Video Preview")
                images_key = f"images_{scene['scene_id']}"
                if images_key in st.session_state:
                    # Scene video
                    if st.button(f"Generate Scene Video (Scene {scene['scene_id']})", key=f"gen_vid_{scene['scene_id']}"):
                        with st.spinner("Generating scene video..."):
                            images = st.session_state[images_key]
                            audio_file = save_audio_file(audio_data, scene['scene_id'])
                            scene_video_file = f"scene_{scene['scene_id']}.mp4"
                            create_scene_video(images, audio_file, scene_video_file)
                            st.success(f"Scene {scene['scene_id']} video created!")
                            st.video(scene_video_file, format="video/mp4", start_time=0, width=700)

                    # Cumulative full video up to this scene
                    st.subheader("Full Video up to This Scene")
                    if st.button(f"Generate Full Video (up to Scene {scene['scene_id']})", key=f"full_vid_{scene['scene_id']}"):
                        with st.spinner("Generating full video..."):
                            scene_videos = []
                            missing_scenes = []
                            for s in scenes[:i+1]:
                                vid_file = f"scene_{s['scene_id']}.mp4"
                                if os.path.exists(vid_file):
                                    scene_videos.append(vid_file)
                                else:
                                    missing_scenes.append(s['scene_id'])
                                    # Insert placeholder black video of 3 seconds
                                    placeholder = f"placeholder_scene_{s['scene_id']}.mp4"
                                    cmd_placeholder = [
                                        "ffmpeg", "-y",
                                        "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=3",
                                        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                                        "-t", "3",
                                        "-c:v", "libx264", "-pix_fmt", "yuv420p",
                                        "-c:a", "aac",
                                        "-shortest",
                                        placeholder
                                    ]
                                    subprocess.run(cmd_placeholder, check=True)
                                    scene_videos.append(placeholder)

                            if missing_scenes:
                                st.warning(f"Missing scenes detected: {missing_scenes}. Placeholders inserted.")

                            if scene_videos:
                                final_video_file = f"full_video_up_to_scene_{scene['scene_id']}.mp4"
                                concatenate_videos(scene_videos, final_video_file)
                                st.success("Full video generated!")
                                st.video(final_video_file, format="video/mp4", start_time=0, width=700)

                            # Clean up placeholder videos
                            for s_id in missing_scenes:
                                placeholder = f"placeholder_scene_{s_id}.mp4"
                                if os.path.exists(placeholder):
                                    os.remove(placeholder)
                else:
                    st.warning("Please generate images for this scene first to create video.")