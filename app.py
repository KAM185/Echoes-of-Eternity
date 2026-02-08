import streamlit as st
import json
from PIL import Image
import os

# Assume you have utils.py and prompts.py with the functions
from utils import generate_analysis_stream, draw_damage_overlay, generate_audio, init_gemini
from prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT, CHAT_PROMPT

st.set_page_config(page_title="Echoes of Eternity", page_icon="🪨", layout="centered")

# Background image
bg_url = "https://raw.githubusercontent.com/KAM185/Echoes-of-Eternity/main/bg_final.jpg"

# Glowing golden-blue title + full transparent-ish background
st.markdown(
    f"""
    <style>
        .stApp {{
            background: url('{bg_url}') center/cover no-repeat fixed !important;
            background-color: #0a0e1a;
        }}
        section[data-testid="stAppViewContainer"] {{
            background: rgba(8, 10, 22, 0.28) !important;
        }}
        .block-container {{
            background: rgba(18, 22, 38, 0.40) !important;
            backdrop-filter: blur(12px);
            border-radius: 20px;
            box-shadow: 0 12px 50px rgba(0,0,0,0.5);
            padding: 3rem 2rem !important;
            margin: 1.5rem auto;
            max-width: 1100px;
            border: 1px solid rgba(190, 160, 255, 0.15);
        }}
        h1 {{
            font-family: 'Georgia', serif;
            font-size: 4.5rem !important;
            font-weight: bold;
            text-align: center;
            background: linear-gradient(90deg, #0f1c3a, #1e3a5f, #2a4e7a, #3a6aa6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            background-size: 300% 300%;
            animation: gradientFlow 8s ease infinite;
            text-shadow: 
                0 0 20px #a78bfa,
                0 0 40px #c4a1ff,
                0 0 70px #ffd07a,
                0 0 100px #ffdb8a;
            letter-spacing: 4px;
            margin-bottom: 0.8rem;
            filter: drop-shadow(0 0 30px rgba(190, 160, 255, 0.8));
        }}
        h3 em {{
            font-size: 1.8rem;
            color: #d4b37a !important;
            text-align: center;
            display: block;
            opacity: 0.9;
        }}
        @keyframes gradientFlow {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        /* Rest of your styles for readability */
        p, div, span, li, label {{ color: #e0d8c0 !important; text-shadow: 0 1px 6px #000; }}
        .stFileUploader [data-testid="stFileUploaderDropzone"] {{
            background: rgba(25, 30, 50, 0.35) !important;
            border: 2px dashed #a78bfa !important;
        }}
        .stButton > button {{
            background: linear-gradient(90deg, #1e5799, #3a6aa6) !important;
            color: white !important;
            border: none;
        }}
    </style>
    <h1>Echoes of Eternity</h1>
    <h3><em>When ancient stones finally speak.</em></h3>
    """,
    unsafe_allow_html=True
)

# Your existing session state, uploader, analysis, results, chat code goes here...
# (copy the rest from your previous version)

# Example placeholder for the rest (add your full logic)
st.file_uploader("Upload or capture a monument image (jpg/png)", type=["jpg", "jpeg", "png"])
st.button("Awaken the Echo")
st.text_input("Ask the Echo")
