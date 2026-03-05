import streamlit as st
from backend.parser import extract_text
from backend.script_agent import generate_script

st.title("Agentic Video Editor")

uploaded_file = st.file_uploader("Upload Research Paper")

if uploaded_file:

    text = extract_text(uploaded_file)

    if st.button("Generate Script"):

        script = generate_script(text)

        st.write(script)