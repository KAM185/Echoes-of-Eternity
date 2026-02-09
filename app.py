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
# Page title
# ────────────────────────────────────────────────
st.markdown("<h1>Echoes of Eternity</h1>", unsafe_allow_html=True)
st.markdown(
    "<h3><em>Whispers of history in every stone</em></h3>",
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
    try:
        image = Image.open(uploaded_file).convert("RGB")
        st.session_state.image = image
        st.image(image, caption="Your uploaded monument", use_container_width=True)
    except Exception as e:
        st.error(f"Could not load image: {e}")


# ────────────────────────────────────────────────
# Analysis button
# ────────────────────────────────────────────────
if st.button(
    "Awaken the Echo",
    type="primary",
    disabled=st.session_state.image is None,
):
    with st.spinner("Listening across centuries..."):
        stream_placeholder = st.empty()
        full_response = ""

        # ✅ CORRECT USAGE (unpack return values)
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
            st.error("The echo was unclear. Please try again.")
            st.markdown(f"**Raw response (debug):**\n\n{full_response}")


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

        damage_types = pres.get("damage_types", [])
        if damage_types:
            st.markdown("**Damage types:** " + ", ".join(damage_types))
        else:
            st.markdown("**Damage types:** None major visible")

    overlay = draw_damage_overlay(
        st.session_state.image,
        pres.get("damaged_areas", []),
    )
    st.image(
        overlay,
        caption="Preservation damage overlay",
        use_container_width=True,
    )

    story = res.get("storytelling", "")
    if story:
        st.markdown(
            f'<div class="story">{story}</div>',
            unsafe_allow_html=True,
        )

        audio_path = generate_audio(story)
        if audio_path:
            st.audio(audio_path, format="audio/mp3")
            try:
                os.unlink(audio_path)
            except Exception:
                pass


# ────────────────────────────────────────────────
# Chat
# ────────────────────────────────────────────────
st.markdown("## Ask the Echo")

question = st.text_input("Your question to the monument…")

if question and question.strip():
    st.session_state.chat_history.append(
        {"role": "user", "content": question}
    )

    with st.spinner("The monument answers..."):
        try:
            model = init_gemini("gemini-3.0-pro")
        except Exception:
            model = init_gemini("gemini-3.0-flash")

        try:
            history = [
                {
                    "role": "user" if m["role"] == "user" else "model",
                    "parts": [m["content"]],
                }
                for m in st.session_state.chat_history[:-1]
            ]
            chat = model.start_chat(history=history)
            response = chat.send_message(question)
            reply = response.text.strip()
        except Exception:
            reply = "The winds carry my voice faintly… ask again."

    st.session_state.chat_history.append(
        {"role": "monument", "content": reply}
    )

for msg in st.session_state.chat_history:
    role = "You" if msg["role"] == "user" else "Monument"
    st.markdown(f"**{role}:** {msg['content']}")

