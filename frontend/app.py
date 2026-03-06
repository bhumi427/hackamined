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

CACHE_FILE = "scenes.json"  # stores a dict mapping filename->scene data

uploaded_file = st.file_uploader("Upload Document", type=["pdf"])

# remember the last uploaded filename so we can detect when the user
# switches to a different PDF and clear the cache accordingly.
if 'last_file' not in st.session_state:
    st.session_state.last_file = None


if uploaded_file:

    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'scenes_visible' not in st.session_state:
        st.session_state.scenes_visible = False

    # if a new file is uploaded, delete any previous cache so we don't show
    # the old scenes
    if uploaded_file.name != st.session_state.last_file:
        st.session_state.last_file = uploaded_file.name
        for f_name in [CACHE_FILE, "server.json", "summary.txt"]:
            if os.path.exists(f_name):
                try:
                    os.remove(f_name)
                except Exception:
                    pass
        st.session_state.summary = None
        st.session_state.scenes_visible = False
        st.rerun()

    text = extract_text(uploaded_file)
    
    # Load summary if missing from session state but file exists
    if st.session_state.summary is None and os.path.exists("summary.txt"):
        try:
            with open("summary.txt", "r") as f:
                st.session_state.summary = f.read()
        except:
            pass

    st.subheader("Step 1: Review Summary")
    
    if st.session_state.summary is None:
        if st.button("Generate Summary"):
            if os.path.exists("summary.txt"):
                try:
                    with open("summary.txt", "r") as f:
                        st.session_state.summary = f.read()
                    st.success("Loaded existing summary from file!")
                    import time
                    time.sleep(1)
                    st.rerun()
                except Exception:
                    pass

            if st.session_state.summary is None:
                with st.spinner("Generating summary..."):
                    summary = generate_summary(text)
                    st.session_state.summary = summary
                    try:
                        with open("summary.txt", "w") as f:
                            f.write(summary)
                    except Exception:
                        pass
                with st.spinner("Generating scenes..."):
                    script = generate_script(summary)
                    try:
                        data = json.loads(script)
                        with open("server.json", "w") as f:
                            json.dump(data, f, indent=2)
                        st.success("Scenes generated and saved to server.json!")
                    except Exception:
                        cleaned_script = script.strip()
                        if cleaned_script.startswith('```json'):
                            cleaned_script = cleaned_script[7:]
                        if cleaned_script.startswith('```'):
                            cleaned_script = cleaned_script[3:]
                        if cleaned_script.endswith('```'):
                            cleaned_script = cleaned_script[:-3]
                        cleaned_script = cleaned_script.strip()
                        try:
                            data = json.loads(cleaned_script)
                            with open("server.json", "w") as f:
                                json.dump(data, f, indent=2)
                            st.success("Scenes generated and saved to server.json!")
                        except Exception:
                            try:
                                with open("server.json", "w") as sf:
                                    sf.write(cleaned_script)
                                st.info("Raw LLM output saved to server.json")
                            except Exception as _:
                                pass
                    st.rerun()
                
        # Stop execution here until summary is generated
        st.stop()
    else:
        st.session_state.summary = st.text_area(
            "Overall Summary (Edit if needed):", 
            value=st.session_state.summary, 
            height=250
        )
        
        try:
            with open("summary.txt", "w") as f:
                f.write(st.session_state.summary)
        except Exception:
            pass

        st.subheader("Step 2: Generate Scenes")

        col1, col2 = st.columns(2)

        with col1:
            generate_btn = st.button("Load Scenes from Cache")

        with col2:
            regenerate_btn = st.button("Regenerate Scenes")

    data = None

    # Only load data if scenes_visible flag is set (user explicitly loaded/generated)
    if st.session_state.scenes_visible and os.path.exists("server.json"):
        try:
            with open("server.json") as f:
                data = json.load(f)
        except Exception:
            pass

    # Handle Load Scenes button - only load from server.json, no API call
    if generate_btn:
        if os.path.exists("server.json"):
            try:
                with open("server.json") as f:
                    data = json.load(f)
                # Clear stale visual description backing values from previous file
                for key in list(st.session_state.keys()):
                    if key.startswith("vis_val_"):
                        del st.session_state[key]
                st.session_state.scenes_visible = True
                st.success("Scenes loaded from server.json")
            except Exception:
                st.error("Failed to load scenes from server.json")
        else:
            st.warning("No scenes found in server.json. Use 'Regenerate Scenes' to generate new content.")

    # Handle Regenerate Scenes button - call API and save to server.json
    if regenerate_btn:
        if os.path.exists("server.json"):
            try:
                os.remove("server.json")
            except Exception:
                pass

        with st.spinner("Generating scenes from summary..."):
            script = generate_script(st.session_state.summary)
        try:
            data = json.loads(script)
            with open("server.json", "w") as f:
                json.dump(data, f, indent=2)
            # Clear stale visual description backing values from previous file
            for key in list(st.session_state.keys()):
                if key.startswith("vis_val_"):
                    del st.session_state[key]
            st.session_state.scenes_visible = True
            st.success("Scenes regenerated and saved to server.json!")
        except Exception:
            # clean up any markdown formatting from the LLM response
            cleaned_script = script.strip()
            if cleaned_script.startswith('```json'):
                cleaned_script = cleaned_script[7:]
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

    # Display scenes
    if data:

        scenes = data["scenes"]

        st.success(f"{len(scenes)} scenes loaded")


        scene_titles = [f"Scene {s['scene_id']}" for s in scenes]

        tabs = st.tabs(scene_titles)

        for i, tab in enumerate(tabs):

            scene = scenes[i]

            with tab:

                # Script and Visual Description side by side
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Script")
                    # Make script editable
                    edited_script = st.text_area(
                        "Edit script:",
                        value=scene["script"],
                        height=150,
                        key=f"script_{scene['scene_id']}",
                        label_visibility="collapsed"
                    )

                with col2:
                    st.subheader("Visual Description")
                    # Backing key: updated by generate button, read as value every rerun
                    vis_val_key = f"vis_val_{scene['scene_id']}"
                    if vis_val_key not in st.session_state:
                        st.session_state[vis_val_key] = scene["visual_description"]
                    # No widget key — so value= always reflects the backing store
                    edited_visual = st.text_area(
                        "Edit visual description:",
                        value=st.session_state[vis_val_key],
                        height=150,
                        label_visibility="collapsed"
                    )

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    # Button to generate visual description from the current script
                    if st.button(f"Generate Visual Desc from Script (Scene {scene['scene_id']})", key=f"update_{scene['scene_id']}"):
                        with st.spinner("Generating visual description..."):
                            from backend.llm_wrapper import generate_text
                            prompt = f"""
You are an expert at creating visual descriptions for video scenes.

Based on this script: "{edited_script}"

Create a detailed visual description (2-3 sentences) that would work well for a video scene. Focus on what should be shown visually to match the script content.

Return only the visual description, nothing else.
"""
                            try:
                                new_visual_desc = generate_text(prompt).strip()
                                if new_visual_desc:
                                    data["scenes"][i]["script"] = edited_script
                                    data["scenes"][i]["visual_description"] = new_visual_desc
                                    with open("server.json", "w") as f:
                                        json.dump(data, f, indent=2)
                                    # Update the backing key — safe since it's not a widget key
                                    st.session_state[vis_val_key] = new_visual_desc
                                    st.success(f"Scene {scene['scene_id']} visual description updated!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Failed to generate visual description: {e}")

                with col_btn2:
                    if st.button(f"Save Manual Edits (Scene {scene['scene_id']})", key=f"save_{scene['scene_id']}"):
                        data["scenes"][i]["script"] = edited_script
                        data["scenes"][i]["visual_description"] = edited_visual
                        with open("server.json", "w") as f:
                            json.dump(data, f, indent=2)
                        st.success(f"Scene {scene['scene_id']} saved!")

                # Generate images on demand
                if st.button(f"Generate Images (Scene {scene['scene_id']})", key=f"gen_img_{scene['scene_id']}"):
                    with st.spinner("Generating images..."):
                        images = get_scene_images(edited_visual)
                        st.session_state[f"images_{scene['scene_id']}"] = images
                        st.success("Images generated!")

                # Display images if generated
                if f"images_{scene['scene_id']}" in st.session_state:
                    st.subheader("Visual Options")
                    images = st.session_state[f"images_{scene['scene_id']}"]
                    cols = st.columns(3)
                    for j, img in enumerate(images):
                        cols[j].image(img)

                # Audio
                st.subheader("Audio")
                audio_data = generate_audio(edited_script)
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