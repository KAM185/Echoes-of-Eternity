# app.py

import os
import json
import streamlit as st
from PIL import Image

# 🔍 TEMPORARY DEBUG CHECK
if st.button("Check API key loaded"):
    key = os.getenv("GEMINI_API_KEY")
    if key:
        st.success(f"API key is loaded (length: {len(key)})")
    else:
        st.error("API key NOT found")

import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

models = genai.list_models()

for m in models:
    print(m.name)
    print("  supported methods:", m.supported_generation_methods)


import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Say OK")
    print(response.text)
except Exception as e:
    print("ERROR TYPE:", type(e))
    print("ERROR MESSAGE:", e)


import google.generativeai as genai

if st.button("Test Gemini text"):
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Say OK in one word.")
        st.success("Text generation works")
        st.write(response.text)
    except Exception as e:
        st.error("Text generation FAILED")
        st.exception(e)






from utils import (
    generate_analysis_stream,
    draw_damage_overlay,
    generate_audio,
    init_gemini,
)
from prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT, CHAT_PROMPT

# ────────────────────────────────────────────────
# Page config
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="Echoes of Eternity",
    page_icon="🪨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ────────────────────────────────────────────────
# Page title
# ────────────────────────────────────────────────
st.markdown("<h1>Echoes of Eternity</h1>", unsafe_allow_html=True)
st.markdown(
    '<h3><em>Whispers of history in every stone</em></h3>',
    unsafe_allow_html=True
)

# ────────────────────────────────────────────────
# Background + transparent UI + glowing title
# ────────────────────────────────────────────────
bg_url = "https://raw.githubusercontent.com/KAM185/Echoes-of-Eternity/main/bg_final.jpg"

st.markdown(
    f"""
    <style>
        .stApp {{
            background: url('{bg_url}') center/cover no-repeat fixed !important;
            background-color: #0a0e1a;
        }}
        section[data-testid="stAppViewContainer"] {{
            background: rgba(8, 10, 22, 0.25) !important;
        }}
        .block-container {{
            background: rgba(18, 22, 38, 0.32) !important;
            backdrop-filter: blur(14px);
            border-radius: 24px;
            box-shadow: 0 15px 60px rgba(0,0,0,0.55);
            padding: 3.2rem 2.5rem !important;
            margin: 2rem auto;
            max-width: 1150px;
            border: 1px solid rgba(190, 160, 255, 0.20);
        }}

        /* Strong mysterious golden-blue glowing title */
        h1 {{
            font-family: 'Georgia', serif;
            font-size: 5rem !important;
            font-weight: bold;
            text-align: center;
            background: linear-gradient(90deg, #0f1c3a, #1e3a5f, #2a4e7a, #3a6aa6, #4a82c6, #6a9ae6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            background-size: 400% 400%;
            animation: gradientFlow 10s ease infinite;
            text-shadow:
                0 0 30px #a78bfa,
                0 0 60px #c4a1ff,
                0 0 90px #ffd07a,
                0 0 140px #ffdb8a,
                0 0 200px #ffd07a;
            letter-spacing: 5px;
            margin: 0.5rem 0 1.2rem 0;
            filter: drop-shadow(0 0 45px rgba(190, 160, 255, 0.9));
        }}
        @keyframes gradientFlow {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        h3 em {{
            font-size: 2rem;
            color: #d4b37a !important;
            text-align: center;
            display: block;
            opacity: 0.92;
            text-shadow: 0 2px 15px #000;
        }}

        /* Fully transparent/glass elements */
        .stFileUploader [data-testid="stFileUploaderDropzone"] {{
            background: rgba(25, 30, 50, 0.25) !important;
            border: 2px dashed #a78bfa !important;
            border-radius: 20px;
            min-height: 180px;
            backdrop-filter: blur(10px);
        }}
        .stExpander {{
            background: rgba(25, 30, 50, 0.30) !important;
            border: 1px solid rgba(190, 160, 255, 0.30) !important;
            border-radius: 16px;
            backdrop-filter: blur(12px);
            margin: 1.5rem 0;
        }}
        .stTextInput > div > div {{
            background: rgba(25, 30, 50, 0.30) !important;
            border: 1px solid rgba(190, 160, 255, 0.35) !important;
            border-radius: 16px;
            backdrop-filter: blur(12px);
            color: #e0d8c0 !important;
        }}
        .stButton > button {{
            background: linear-gradient(90deg, #1e5799, #3a6aa6, #5a8ac6) !important;
            color: white !important;
            border: none !important;
            font-weight: 600;
            box-shadow: 0 6px 25px rgba(58, 106, 166, 0.5) !important;
            transition: all 0.3s;
        }}
        .stButton > button:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(58, 106, 166, 0.8) !important;
        }}

        /* Text readability */
        p, div, span, li, label {{
            color: #e0d8c0 !important;
            text-shadow: 0 1px 8px rgba(0,0,0,0.85) !important;
        }}
        .story {{
            background: rgba(25, 30, 50, 0.40) !important;
            border: 1px solid rgba(190, 160, 255, 0.40);
            box-shadow: 0 0 50px rgba(190, 160, 255, 0.25);
            color: #f0e8d0 !important;
            padding: 2.5rem;
            border-radius: 20px;
            font-size: 1.25em;
            line-height: 1.9;
            margin: 3rem 0;
            backdrop-filter: blur(14px);
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────
# Session state
# ────────────────────────────────────────────────
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "image" not in st.session_state:
    st.session_state.image = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ────────────────────────────────────────────────
# Image uploader
# ────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload or capture a monument image (jpg/png)",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.session_state.image = image
    st.image(image, caption="Your uploaded monument", use_container_width=True)

# ────────────────────────────────────────────────
# Analysis button
# ────────────────────────────────────────────────
if st.button("Awaken the Echo", disabled=st.session_state.image is None):
    with st.spinner("Listening across centuries..."):
        stream_placeholder = st.empty()
        full_response = ""

        stream, parsed = generate_analysis_stream(
            st.session_state.image,
            SYSTEM_PROMPT + ANALYSIS_PROMPT,
        )

        for chunk in stream:
            full_response += chunk
            stream_placeholder.markdown(full_response + " ▌")

        stream_placeholder.empty()

        if parsed:
            st.session_state.analysis_result = parsed
            st.success("The echo has awakened.")
        else:
            st.error("Failed to interpret the echo.")
            st.markdown(f"**Raw response:**\n\n{full_response}")

# ────────────────────────────────────────────────
# Results
# ────────────────────────────────────────────────
if st.session_state.analysis_result:
    res = st.session_state.analysis_result

    with st.expander("Identification", expanded=True):
        st.markdown(res.get("identification", "Unknown"))

    with st.expander("Architecture"):
        st.markdown(res.get("architecture", "Not described"))

    with st.expander("Significance"):
        st.markdown(res.get("significance", "Not described"))

    with st.expander("Preservation Assessment"):
        pres = res.get("preservation", {})
        st.markdown(f"**Severity score:** {pres.get('severity_score', 'N/A')}/100")

    overlay = draw_damage_overlay(
        st.session_state.image,
        pres.get("damaged_areas", []),
    )
    st.image(overlay, caption="Preservation damage overlay", use_container_width=True)

    story = res.get("storytelling", "")
    if story:
        st.markdown(f'<div class="story">{story}</div>', unsafe_allow_html=True)

        audio_path = generate_audio(story)
        if audio_path:
            st.audio(audio_path, format="audio/mp3")
            os.unlink(audio_path)

# ────────────────────────────────────────────────
# Chat
# ────────────────────────────────────────────────
st.markdown("## Ask the Echo")

question = st.text_input("Your question to the monument…")

if question:
    st.session_state.chat_history.append({"role": "user", "content": question})

    model = init_gemini("gemini-3.0-flash")
    chat = model.start_chat()

    try:
        reply = chat.send_message(question).text.strip()
    except Exception:
        reply = "The winds carry my voice faintly… ask again."

    st.session_state.chat_history.append({"role": "monument", "content": reply})

for msg in st.session_state.chat_history:
    role = "You" if msg["role"] == "user" else "Monument"
    st.markdown(f"**{role}:** {msg['content']}")


