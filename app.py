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
# Moving blue fog video background
# ────────────────────────────────────────────────
video_url = "https://files.catbox.moe/b361zg.mp4"

st.components.v1.html(
    f"""
    <style>
        #bg-video {{
            position: fixed;
            right: 0;
            bottom: 0;
            min-width: 100%;
            min-height: 100%;
            width: auto;
            height: auto;
            z-index: -100;
            object-fit: cover;
            background: #0a0e1a;  /* dark fallback color */
        }}
        .stApp > div:first-child {{
            position: relative;
            z-index: 1;
        }}
        /* Semi-transparent overlay for text readability */
        .overlay {{
            position: fixed;
            inset: 0;
            background: rgba(8, 10, 22, 0.68);
            z-index: -99;
            pointer-events: none;
        }}
    </style>

    <div class="overlay"></div>
    <video autoplay muted loop playsinline id="bg-video">
        <source src="{video_url}" type="video/mp4">
    </video>
    """,
    height=0
)

# ────────────────────────────────────────────────
# Improved styling (text contrast, story box, etc.)
# ────────────────────────────────────────────────
st.markdown(
    """
    <style>
        h1, h2, h3 {
            color: #f0e0c0 !important;
            text-shadow: 0 2px 8px rgba(0,0,0,0.85);
            text-align: center;
        }
        h1 { font-size: 3.4rem; margin-bottom: 0.3rem; }
        h3 em { font-size: 1.5rem; opacity: 0.9; display: block; }

        p, div, span, li {
            color: #d8d0b8 !important;
            text-shadow: 0 1px 4px rgba(0,0,0,0.6);
        }

        .story {
            background: rgba(25, 28, 45, 0.72) !important;
            border: 1px solid rgba(140, 180, 220, 0.25);
            box-shadow: 0 0 32px rgba(140, 180, 220, 0.12);
            color: #f0e8d0 !important;
            padding: 1.8rem;
            border-radius: 12px;
            font-size: 1.15em;
            line-height: 1.7;
            margin: 1.5rem 0;
        }

        .stExpander {
            background: rgba(15, 20, 35, 0.75) !important;
            border: 1px solid rgba(80, 140, 220, 0.35) !important;
            margin-bottom: 1rem;
        }

        .stButton > button {
            background: linear-gradient(90deg, #0066cc, #0099ff) !important;
            color: white !important;
        }
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
# Hero
# ────────────────────────────────────────────────
st.markdown("<h1>Echoes of Eternity</h1>", unsafe_allow_html=True)
st.markdown(
    "<h3><em>When ancient stones finally speak.</em></h3>",
    unsafe_allow_html=True,
)

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
        st.image(image, caption="Uploaded monument", use_container_width=True)
    except Exception as e:
        st.error(f"Could not load image: {e}")

# ────────────────────────────────────────────────
# Analysis
# ────────────────────────────────────────────────
if st.button("Awaken the Echo", type="primary", disabled=st.session_state.image is None):
    with st.spinner("Awakening the echo..."):
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
            stream_placeholder.markdown(full_response + "▌")

        try:
            json_str = full_response.strip()
            if json_str.startswith("```json"):
                json_str = json_str.split("```json", 1)[1].split("```")[0].strip()
            result = json.loads(json_str)
            st.session_state.analysis_result = result
            stream_placeholder.empty()
            st.success("The monument has spoken.")
        except Exception:
            st.error("Could not parse the response.")
            stream_placeholder.markdown(f"Raw output:\n\n{full_response}")

# ────────────────────────────────────────────────
# Display results
# ────────────────────────────────────────────────
if st.session_state.analysis_result:
    res = st.session_state.analysis_result

    with st.expander("Identification", expanded=True):
        st.markdown(res.get("identification", "Unknown"))

    with st.expander("Architecture"):
        st.markdown(res.get("architecture", "—"))

    with st.expander("Significance"):
        st.markdown(res.get("significance", "—"))

    with st.expander("Preservation Assessment"):
        pres = res.get("preservation", {})
        st.markdown(f"**Severity score:** {pres.get('severity_score', 'N/A')}/100")
        damage_types = pres.get("damage_types", [])
        if damage_types:
            st.markdown("**Damage types:** " + ", ".join(damage_types))
        else:
            st.markdown("**Damage types:** None major detected")

        damaged_areas = pres.get("damaged_areas", [])
        if not damaged_areas:
            st.info("No significant damaged areas detected.")

    overlay = draw_damage_overlay(st.session_state.image, damaged_areas)
    st.image(overlay, caption="Damage overlay", use_container_width=True)

    story = res.get("storytelling", "")
    if story:
        st.markdown(f'<div class="story">{story}</div>', unsafe_allow_html=True)

        audio_path = generate_audio(story)
        if audio_path:
            st.audio(audio_path)
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
                speechSynthesis.speak(ut);
                </script>
                """,
                height=0
            )

    st.download_button(
        "Download analysis (JSON)",
        json.dumps(res, indent=2, ensure_ascii=False),
        file_name="echo_analysis.json",
        mime="application/json"
    )

# ────────────────────────────────────────────────
# Chat
# ────────────────────────────────────────────────
st.markdown("## Ask the Echo")

question = st.text_input("Your question to the monument…")

if question and question.strip():
    st.session_state.chat_history.append({"role": "user", "content": question})

    with st.spinner("The monument responds..."):
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
            reply = "The echo is faint... please try again."

    st.session_state.chat_history.append({"role": "monument", "content": reply})

for msg in st.session_state.chat_history:
    role = "You" if msg["role"] == "user" else "Monument"
    st.markdown(f"**{role}:** {msg['content']}")
