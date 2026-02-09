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
# Styling: light gray title with faint glow & soft pulse
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

        /* Light gray / almost white title with faint glow & soft pulse */
        h1 {{
            font-family: 'Georgia', serif;
            font-size: 5rem !important;
            font-weight: bold;
            text-align: center;
            color: #e0e0e0;
            text-shadow:
                0 0 10px rgba(255,255,255,0.3),
                0 0 20px rgba(200,200,200,0.25),
                0 0 30px rgba(180,180,180,0.2);
            animation: fadeGlow 10s ease-in-out infinite alternate;
            letter-spacing: 3px;
            margin: 0.5rem 0 1.2rem 0;
        }}
        @keyframes fadeGlow {{
            0% {{
                text-shadow:
                    0 0 5px rgba(255,255,255,0.15),
                    0 0 10px rgba(200,200,200,0.10);
                color: #d9d9d9;
            }}
            50% {{
                text-shadow:
                    0 0 12px rgba(255,255,255,0.4),
                    0 0 25px rgba(220,220,220,0.25);
                color: #e0e0e0;
            }}
            100% {{
                text-shadow:
                    0 0 5px rgba(255,255,255,0.15),
                    0 0 10px rgba(200,200,200,0.10);
                color: #d9d9d9;
            }}
        }}

        h3 em {{
            font-size: 2rem;
            color: #aaa68c !important;
            text-align: center;
            display: block;
            opacity: 0.85;
            text-shadow: 0 2px 15px #000;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────
# Page title
# ────────────────────────────────────────────────
st.markdown("<h1>Echoes of Eternity</h1>", unsafe_allow_html=True)
st.markdown('<h3><em>Whispers of history in every stone</em></h3>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Session state
# ────────────────────────────────────────────────
for key in ["analysis_result", "image", "overlay_image", "chat_history"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "chat_history" else []

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
            gen_stream, parsed_result = generate_analysis_stream(
                st.session_state.image,
                SYSTEM_PROMPT + ANALYSIS_PROMPT,
            )
            for chunk in gen_stream:
                full_response += chunk
                stream_placeholder.markdown(full_response + " ▌")
            st.session_state.analysis_result = parsed_result
            stream_placeholder.empty()
            st.success("The echo has awakened.")
        except Exception:
            st.error("Failed to interpret the echo.")

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
        st.markdown("**Damage types:** " + (", ".join(damage_types) if damage_types else "None major visible"))
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
        reply = "The winds carry my voice faintly... ask again."
        try:
            for model_name in ["gemma-3-27b-it","gemma-3-12b-it","gemma-3-4b-it","gemma-3-1b-it",
                               "gemini-2.5-flash","gemini-2.5-pro","gemini-2.0-flash"]:
                try:
                    model = init_gemini(model_name)
                    response = model.generate_content(question)
                    if hasattr(response, "text") and response.text.strip():
                        reply = response.text.strip()
                        break
                except:
                    continue
        except:
            pass

        st.session_state.chat_history.append({"role": "monument", "content": reply})

for msg in st.session_state.chat_history:
    role = "You" if msg["role"] == "user" else "Monument"
    st.markdown(f"**{role}:** {msg['content']}")
