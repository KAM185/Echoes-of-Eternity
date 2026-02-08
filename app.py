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

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Echoes of Eternity",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------
# Styling
# -------------------------------------------------
st.markdown(
    """
    <style>
    body {
        background: radial-gradient(circle at top, #2b2b2b, #0f0f0f);
        color: #f5f0e6;
    }
    h1, h2, h3 {
        font-family: "Georgia", serif;
    }
    .story {
        font-family: "Georgia", serif;
        font-size: 1.1em;
        line-height: 1.6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Session state
# -------------------------------------------------
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "image" not in st.session_state:
    st.session_state.image = None
if "overlay_image" not in st.session_state:
    st.session_state.overlay_image = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -------------------------------------------------
# Hero section
# -------------------------------------------------
st.markdown("<h1>Echoes of Eternity</h1>", unsafe_allow_html=True)
st.markdown(
    "<h3><em>When ancient stones finally speak.</em></h3>",
    unsafe_allow_html=True,
)

st.write("")

# -------------------------------------------------
# Image uploader
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload or capture a monument image",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file:
    try:
        image = Image.open(uploaded_file).convert("RGB")
        st.session_state.image = image
        st.image(
            image,
            caption="Uploaded monument",
            use_container_width=True,
        )
    except Exception:
        st.error("Unable to read the image. Please try another file.")

# -------------------------------------------------
# Analysis button
# -------------------------------------------------
if st.button("Awaken the Echo", disabled=st.session_state.image is None):
    if not st.session_state.image:
        st.warning("Please upload an image first.")
    else:
        with st.spinner("Listening to the stones..."):
            stream, result = generate_analysis_stream(
                st.session_state.image,
                SYSTEM_PROMPT + ANALYSIS_PROMPT,
                primary_model="gemini-3-pro-preview",
                fallback_model="gemini-3-flash-preview",
            )

            st.write_stream(stream)

            if not result:
                st.error(
                    "The image could not be recognized as a monument. "
                    "Please try another image."
                )
            else:
                st.session_state.analysis_result = result

# -------------------------------------------------
# Display analysis
# -------------------------------------------------
result = st.session_state.analysis_result

if result:
    st.success("The monument has spoken.")

    with st.expander("Identification"):
        st.markdown(result.get("identification", "Unknown"))

    with st.expander("Architecture"):
        st.markdown(result.get("architecture", ""))

    with st.expander("Historical Significance"):
        st.markdown(result.get("significance", ""))

    with st.expander("Preservation Assessment"):
        preservation = result.get("preservation", {})
        st.markdown(
            f"**Severity score:** {preservation.get('severity_score', 0)}/100"
        )

        damage_types = preservation.get("damage_types", [])
        if damage_types:
            st.markdown("**Damage types:** " + ", ".join(damage_types))
        else:
            st.markdown("**Damage types:** None visible")

    # -------------------------------------------------
    # Damage overlay
    # -------------------------------------------------
    damaged_areas = (
        result.get("preservation", {}).get("damaged_areas", [])
    )

    overlay = draw_damage_overlay(
        st.session_state.image,
        damaged_areas,
    )
    st.session_state.overlay_image = overlay

    st.image(
        overlay,
        caption="Preservation damage overlay",
        use_container_width=True,
    )

    # -------------------------------------------------
    # Storytelling + audio
    # -------------------------------------------------
    story = result.get("storytelling", "")
    st.markdown(
        f"<div class='story'>{story}</div>",
        unsafe_allow_html=True,
    )

    audio_path = generate_audio(story)

    if audio_path:
        st.audio(audio_path)
        try:
            os.unlink(audio_path)
        except Exception:
            pass
    else:
        st.components.v1.html(
            f"""
            <script>
            const utterance = new SpeechSynthesisUtterance({json.dumps(story)});
            speechSynthesis.speak(utterance);
            </script>
            """
        )

    # -------------------------------------------------
    # Download result
    # -------------------------------------------------
    st.download_button(
        "Share the Echo",
        data=json.dumps(result, indent=2),
        file_name="echoes_of_eternity.json",
        mime="application/json",
    )

# -------------------------------------------------
# Chat section
# -------------------------------------------------
st.markdown("## Ask the Echo")

question = st.text_input("Speak to the monument...")

if question:
    st.session_state.chat_history.append(
        {"role": "user", "content": question}
    )

    try:
        model = init_gemini("gemini-3-pro-preview")
        chat = model.start_chat(history=st.session_state.chat_history)
        reply = chat.send_message(CHAT_PROMPT + question).text
    except Exception:
        model = init_gemini("gemini-3-flash-preview")
        chat = model.start_chat(history=st.session_state.chat_history)
        reply = chat.send_message(CHAT_PROMPT + question).text

    st.session_state.chat_history.append(
        {"role": "monument", "content": reply}
    )

for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Monument:** {msg['content']}")
