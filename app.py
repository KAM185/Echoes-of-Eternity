# app.py
import os
import json
import streamlit as st
from PIL import Image
import io

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
# Mystical dark background with subtle rune animation
# ────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* Base cosmic dark background */
        .stApp {
            background: linear-gradient(135deg, #0a0e1a 0%, #0f1626 50%, #1a1f2e 100%) !important;
            background-attachment: fixed;
            overflow: hidden;
        }
        section[data-testid="stAppViewContainer"] {
            background: transparent !important;
        }
        .block-container {
            background: rgba(10, 14, 26, 0.78) !important;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(6px);
            padding: 2rem !important;
            position: relative;
            z-index: 1;
        }

        /* Subtle glowing rune layer */
        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image: 
                radial-gradient(circle at 15% 25%, rgba(0, 220, 180, 0.04) 0%, transparent 60%),
                radial-gradient(circle at 80% 70%, rgba(180, 120, 255, 0.04) 0%, transparent 60%),
                radial-gradient(circle at 40% 85%, rgba(220, 180, 80, 0.03) 0%, transparent 50%);
            animation: rune-drift 120s linear infinite;
            opacity: 0.6;
            z-index: -2;
        }

        .stApp::after {
            content: "⟟ ⋮ ⋰ ⋱ ⟡ ✧ ∴ ∵ ∞ ⊹ ⋆ ✶ 𓂀 ⊹ ⋆ ✦";
            position: fixed;
            inset: 0;
            font-family: "Georgia", serif;
            font-size: 5rem;
            color: transparent;
            background: linear-gradient(90deg, 
                rgba(0, 220, 180, 0.12) 0%, 
                rgba(180, 120, 255, 0.10) 30%, 
                rgba(220, 180, 80, 0.08) 70%, 
                rgba(0, 220, 180, 0.12) 100%);
            -webkit-background-clip: text;
            background-clip: text;
            opacity: 0.15;
            pointer-events: none;
            animation: rune-pulse 18s ease-in-out infinite alternate, rune-float 90s linear infinite;
            z-index: -1;
            white-space: pre-wrap;
            overflow: hidden;
            user-select: none;
        }

        @keyframes rune-drift {
            0%   { transform: translate(0, 0) rotate(0deg); }
            100% { transform: translate(-8%, -5%) rotate(3deg); }
        }

        @keyframes rune-pulse {
            0%   { opacity: 0.10; filter: blur(1px); }
            100% { opacity: 0.22; filter: blur(0.5px); }
        }

        @keyframes rune-float {
            0%   { transform: translateY(0) rotate(0deg); }
            50%  { transform: translateY(-4%) rotate(1deg); }
            100% { transform: translateY(0) rotate(0deg); }
        }

        /* Text & glow accents */
        h1, h2, h3 {
            color: #e0d4b8 !important;
            text-shadow: 0 0 12px rgba(224, 212, 184, 0.25);
            text-align: center;
        }
        h1 { font-size: 3.4rem; margin-bottom: 0.3rem; }
        h3 em { font-size: 1.5rem; opacity: 0.9; display: block; }

        p, div, span, li { color: #d0c9b5 !important; }
        .story { 
            background: rgba(20, 25, 40, 0.65) !important;
            border: 1px solid rgba(100, 180, 255, 0.25);
            box-shadow: 0 0 24px rgba(0, 180, 200, 0.18);
            color: #e8e0d0 !important;
            padding: 1.8rem;
            border-radius: 12px;
            font-size: 1.15em;
            line-height: 1.7;
        }

        .stExpander {
            background: rgba(15, 20, 35, 0.75) !important;
            border: 1px solid rgba(80, 140, 220, 0.35) !important;
            box-shadow: 0 0 16px rgba(80, 140, 220, 0.15);
            margin-bottom: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────
# Session state initialization
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
        st.error(f"Failed to load image: {str(e)}")

# ────────────────────────────────────────────────
# Analysis trigger
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

        # Parse final JSON
        try:
            json_str = full_response.strip()
            # Remove possible markdown code fences
            if json_str.startswith("```json"):
                json_str = json_str.split("```json", 1)[1].split("```", 1)[0].strip()
            result = json.loads(json_str)
            st.session_state.analysis_result = result
            stream_placeholder.empty()
            st.success("The echo has awakened.")
        except Exception as e:
            st.error("Failed to parse response as JSON.")
            stream_placeholder.markdown(f"**Raw output (debug):**\n\n{full_response}")

# ────────────────────────────────────────────────
# Display analysis results
# ────────────────────────────────────────────────
if st.session_state.analysis_result:
    res = st.session_state.analysis_result

    cols = st.columns([1, 3])
    with cols[0]:
        st.image(st.session_state.image, use_container_width=True)

    with cols[1]:
        with st.expander("Identification", expanded=True):
            st.markdown(res.get("identification", "Unknown"))

        with st.expander("Architecture"):
            st.markdown(res.get("architecture", "—"))

        with st.expander("Significance"):
            st.markdown(res.get("significance", "—"))

        with st.expander("Preservation Assessment"):
            pres = res.get("preservation", {})
            st.markdown(f"**Severity score:** {pres.get('severity_score', '—')}/100")

            damage_types = pres.get("damage_types", [])
            if damage_types:
                st.markdown("**Damage types:** " + ", ".join(damage_types))
            else:
                st.markdown("**Damage types:** None major visible")

            damaged_areas = pres.get("damaged_areas", [])
            if not damaged_areas:
                st.info("No significant damaged areas detected.")

        # Overlay image
        overlay = draw_damage_overlay(
            st.session_state.image,
            damaged_areas
        )
        st.image(overlay, caption="Preservation overlay", use_container_width=True)

    # Storytelling + audio
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

    # Share result
    st.download_button(
        "Download Echo (JSON)",
        json.dumps(res, indent=2, ensure_ascii=False),
        file_name="echo_of_eternity.json",
        mime="application/json"
    )

# ────────────────────────────────────────────────
# Ask the Echo chat
# ────────────────────────────────────────────────
st.markdown("## Ask the Echo")

question = st.text_input("Your question to the monument…", key="question_input")

if question and question.strip():
    st.session_state.chat_history.append({"role": "user", "content": question})

    with st.spinner("The monument answers..."):
        try:
            model = init_gemini("gemini-3-pro-preview")
        except:
            model = init_gemini("gemini-3-flash-preview")

        try:
            # Convert history to Gemini format
            history = [
                {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                for m in st.session_state.chat_history[:-1]
            ]
            chat = model.start_chat(history=history)
            response = chat.send_message(question)
            reply = response.text.strip()
        except Exception as e:
            st.warning("Chat connection issue. Trying again...")
            reply = "The winds carry my voice faintly... ask again in a moment."

    st.session_state.chat_history.append({"role": "monument", "content": reply})

# Show chat history
for msg in st.session_state.chat_history:
    role = "You" if msg["role"] == "user" else "Monument"
    st.markdown(f"**{role}:** {msg['content']}")
