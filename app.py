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
st.markdown('<h3><em>Whispers of history in every stone</em></h3>', unsafe_allow_html=True)

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
        /* Your original glowing title and styling remains untouched */
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
# Uploader
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

        try:
            for chunk in generate_analysis_stream(
                st.session_state.image,
                SYSTEM_PROMPT + ANALYSIS_PROMPT,
            ):
                full_response += chunk
                stream_placeholder.markdown(full_response + " ▌")

            # Parse JSON safely
            json_str = full_response.strip()
            if json_str.startswith("```json"):
                json_str = json_str.split("```json", 1)[1].split("```", 1)[0].strip()
            result = json.loads(json_str)
            st.session_state.analysis_result = result
            stream_placeholder.empty()
            st.success("The echo has awakened.")

        except Exception as e:
            st.error("Failed to interpret the echo.")
            stream_placeholder.markdown(f"**Raw response (debug):**\n\n{full_response}")

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

        damaged_areas = pres.get("damaged_areas", [])
        if not damaged_areas:
            st.info("No significant damaged areas detected.")

    overlay = draw_damage_overlay(st.session_state.image, pres.get("damaged_areas", []))
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
# Chat
# ────────────────────────────────────────────────
st.markdown("## Ask the Echo")

question = st.text_input("Your question to the monument…", key="chat_input")

if question and question.strip():
    st.session_state.chat_history.append({"role": "user", "content": question})

    with st.spinner("The monument answers..."):
        try:
            # Use 3-model priority for chat
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
