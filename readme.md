# TraceEdit - AI-Powered Video Editor

## Overview
**TraceEdit** is a Python-based application that generates videos from text scripts. The app takes user input, generates scenes with images, synthesizes audio, and merges them into a final video. It leverages AI models for text-to-image generation, script parsing, and text-to-speech conversion.

---

## Features
- Generate script-based video scenes automatically.
- Convert text to speech using **gTTS**.
- Create images for each scene using AI image generation.
- Merge audio and images into a final video.
- Streamlit-based interactive web interface for easy use.

---

## Tech Stack
- **Backend:** Python, PyPDF2, pdf2image, PIL, pytesseract
- **Frontend:** Streamlit
- **AI Tools:** GPT for script generation, AI image generation APIs
- **Audio:** gTTS (Google Text-to-Speech),mutagen
- **Video Processing:** ffmpeg
- **Environment:** .env for API keys and configuration

---

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/hackamined.git
cd hackamined
```

2. **Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
Create a `.env` file with your API keys, for example:
```
AIPIPE_API_KEY=your_api_key
GEMINI_API_KEY=your_api_key
LLM_PROVIDER=your_api_key
PEXELS_API_KEY=your_api_key
HF_API_KEY=your_api_key
```

---

## Usage

1. **Run the Streamlit app**
```bash
streamlit run frontend/app.py
```

2. **Use the interface**:
- Upload pdf
- Generate summary and choose depth level, edit if required
- click on generate script
- Generate scene images.
- Generate audio narration.
- Merge them to produce the final video.

---

## Project Structure(example)
```
hackamined/
│
├── frontend/           # Streamlit interface
│   └── app.py
├── backend/            # Core AI processing and utilities
│   ├── parser.py
│   ├── script_agent.py
│   └── image_generator.py
├── server.json         # Stores generated scripts and metadata
├── requirements.txt
└── README.md
```

---

## Notes
- Ensure you have a compatible Python version (≥3.10 recommended).  
- ensure system path variable is set up for ffmpeg .

---

## Author
**Hacknottohack**
Made with love by Nirma University Students