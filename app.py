# app.py
import os
import json
import streamlit as st
from PIL import Image

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
# Background image (your uploaded bg_final.jpg)
# ────────────────────────────────────────────────
bg_url = "https://github.com/KAM185/Echoes-of-Eternity/blob/main/bg_final.jpg?raw=true"

st.markdown(
    f"""
    <style>
        .stApp {{
            background: url('{bg_url}') center/cover no-repeat fixed !important;
            background-color: #0a0e1a;  /* dark fallback color */
        }}
        section[data-testid="stAppViewContainer"] {{
            background: rgba(8, 10, 22, 0.48) !important;  /* balanced overlay */
        }}
        .block-container {{
            background: rgba(18, 22, 38, 0.82) !important;
            backdrop-filter: blur(8px);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.6);
            padding: 2.5rem 1.8rem !important;
            margin: 1rem auto;
            max-width: 1100px;
        }}
        /* Better text contrast on dark background */
        h1, h2, h3 {{
            color: #f0e0c0 !important;
            text-shadow: 0 2px 12px rgba(0,0,0,0.9) !important;
            text-align: center;
        }}
        h1 {{ font-size: 3.5rem; margin-bottom: 0.4rem; }}
        h3 em {{ font-size: 1.6rem; opacity: 0.92; display: block; }}
        p, div, span, li, label {{
            color: #d8d0b8 !important;
            text-shadow: 0 1px 6px rgba(0,0,0,0.7) !important;
        }}
        .story {{
            background: rgba(25, 28, 45, 0.78) !important;
            border: 1px solid rgba(140, 180, 220, 0.3);
            box-shadow: 0 0 35px rgba(140, 180, 220, 0.15);
            color: #f0e8d0 !important;
            padding: 1.8rem;
            border-radius: 12px;
            font-size: 1.18em;
            line-height: 1.75;
            margin: 2rem 0;
        }}
        .stExpander {{
            background: rgba(18, 22, 38, 0.82) !important;
            border: 1px solid rgba(80, 140, 220, 0.4) !important;
            margin: 1rem 0;
        }}
        .stButton > button {{
            background: linear-gradient(90deg, #1e5799, #2989d8) !important;
            color: white !important;
            border: none !important;
            font-weight: 600;
        }}
        .stButton > button:hover {{
            box-shadow: 0 0 25px rgba(41, 137, 216, 0.5) !important;
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
if "overlay_image" not in st.session_state:
    st.session_state.overlay_image = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ────────────────────────────────────────────────
# Hero section
# ────────────────────────────────────────────────
st.markdown("<h1>Echoes of Eternity</h1>", unsafe_allow_html=True)
st.markdown(
    "<h3><em>When ancient stones finally speak.</em></h3>",
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────
# Image uploader
# ────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload or capture a monument image (jpg/png)",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file).convert("RGB")
        st.session_state.image = image
        st.image(image, caption="Your uploaded monument", use_container_width=True)
    except Exception as e:
        st.error(f"Could not load image: {str(e)}")

# ────────────────────────────────────────────────
# Analysis button
# ────────────────────────────────────────────────
if st.button("Awaken the Echo", type="primary", disabled=st.session_state.image is None):
    with st.spinner("Listening across centuries..."):
        st.session_state.analysis_result = None

        stream_placeholder = st.empty()

        full_response = ""
        for chunk in generate_analysis_stream(
            st.session_state.image,
            SYSTEM_PROMPT + ANALYSIS_PROMPT,
            primary_model="gemini-3-pro-preview",
            fallback_model="gemini-3-flash-preview",
        ):
            full_response += chunk
            stream_placeholder.markdown(full_response + " ▌")

        try:
            json_str = full_response.strip()
            if json_str.startswith("```json"):
                json_str = json_str.split("```json", 1)[1].split("```", 1)[0].strip()
            result = json.loads(json_str)
            st.session_state.analysis_result = result
            stream_placeholder.empty()
            st.success("The echo has awakened.")
        except Exception as e:
            st.error("Failed to parse response as JSON.")
            stream_placeholder.markdown(f"**Raw response (debug):**\n\n{full_response}")

# ────────────────────────────────────────────────
# Display analysis results
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

        damage_types = pres.get("damage_types", [])
        if damage_types:
            st.markdown("**Damage types:** " + ", ".join(damage_types))
        else:
            st.markdown("**Damage types:** None major visible")

        damaged_areas = pres.get("damaged_areas", [])
        if not damaged_areas:
            st.info("No significant damaged areas detected.")

    overlay = draw_damage_overlay(
        st.session_state.image,
        damaged_areas
    )
    st.image(overlay, caption="Preservation damage overlay", use_container_width=True)

    story = res.get("storytelling", "")
    if story:
        st.markdown(f'<div class="story">{story}</div>', unsafe_allow_html=True)

        audio_path = generate_audio(story)
        if audio_path:
            st.audio(audio_path, format="audio/mp3")
            try:
                os.unlink(audio_path)
            except:
                pass
        else:
            st.components.v1.html(
                f"""
                <script>
                const ut = new SpeechSynthesisUtterance({json.dumps(story)});
                ut.lang = 'en-GB';
                ut.rate = 0.92;
                ut.pitch = 1.05;
                speechSynthesis.speak(ut);
                </script>
                """,
                height=0
            )

    st.download_button(
        "Download full analysis (JSON)",
        json.dumps(res, indent=2, ensure_ascii=False),
        file_name="echo_of_eternity.json",
        mime="application/json"
    )

# ────────────────────────────────────────────────
# Chat section
# ────────────────────────────────────────────────
st.markdown("## Ask the Echo")

question = st.text_input("Your question to the monument…", key="chat_input")

if question and question.strip():
    st.session_state.chat_history.append({"role": "user", "content": question})

    with st.spinner("The monument answers..."):
        try:
            model = init_gemini("gemini-3-pro-preview")
        except:
            model = init_gemini("gemini-3-flash-preview")

        try:
            history = [
                {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                for m in st.session_state.chat_history[:-1]
            ]
            chat = model.start_chat(history=history)
            response = chat.send_message(question)
            reply = response.text.strip()
        except Exception as e:
            st.warning("Chat connection issue.")
            reply = "The winds carry my voice faintly... ask again."

    st.session_state.chat_history.append({"role": "monument", "content": reply})

for msg in st.session_state.chat_history:
    role = "You" if msg["role"] == "user" else "Monument"
    st.markdown(f"**{role}:** {msg['content']}")
