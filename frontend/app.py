import streamlit as st
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.parser import extract_text
from backend.script_agent import generate_script
from backend.image_generator import get_scene_image

st.set_page_config(page_title="Agentic Video Editor", layout="wide")

st.title("🎬 Agentic Video Editor")
st.write("Upload a document to generate a storyboard.")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])


if uploaded_file:

    text = extract_text(uploaded_file)

    if st.button("Generate Script"):

        response = generate_script(text)

        try:
            data = json.loads(response)

            scenes = data["scenes"]

            st.success(f"Generated {len(scenes)} scenes")

            scene_titles = [f"Scene {s['scene_id']}" for s in scenes]

            tabs = st.tabs(scene_titles)

            for i, tab in enumerate(tabs):

                scene = scenes[i]

                with tab:
                    image_url = get_scene_image(scene["visual_description"])

                    st.image(image_url)

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("🎙 Script")
                        st.write(scene["script"])

                    with col2:
                        st.subheader("🎥 Visual Description")
                        st.write(scene["visual_description"])

                    st.write("⏱ Duration:", scene["duration"], "seconds")

        except:
            st.error("Failed to parse JSON response")
            st.write(response)