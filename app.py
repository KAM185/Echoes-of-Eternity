import json
import os
import streamlit as st
from PIL import Image
from utils import init_gemini, generate_analysis, draw_damage_overlay, generate_audio
from prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT, CHAT_PROMPT

# ── FORCE DARK MODE ─────────────────────────────
st.set_page_config(
    page_title="Echoes of Eternity",
    page_icon="🔊",
    layout="centered",
)

init_gemini()

# ── BACKGROUND + GLASS UI ───────────────────────
bg_url = "https://raw.githubusercontent.com/KAM185/Echoes-of-Eternity/main/bg_final.jpg"
st.markdown(
    f"""
    <style>
    .stApp {{
        background: url('{bg_url}') no-repeat center center fixed;
        background-size: cover;
    }}
    .block-container {{
        background: rgba(10, 12, 20, 0.55);
        backdrop-filter: blur(14px);
        border-radius: 20px;
        padding: 3rem;
    }}
    h1 {{
        text-align: center;
        font-size: 4rem;
        font-family: Georgia, serif;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── TITLE ───────────────────────────────────────
st.markdown("<h1>Echoes of Eternity</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>When ancient stones finally speak.</p>", unsafe_allow_html=True)

# ── STATE ───────────────────────────────────────
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "image" not in st.session_state:
    st.session_state.image = None

# ── UPLOAD ──────────────────────────────────────
file = st.file_uploader("Upload a monument image", type=["jpg", "png", "jpeg"])
if file:
    img = Image.open(file).convert("RGB")
    st.session_state.image = img
    st.image(img, caption="Original uploaded image", use_container_width=True)

# ── ANALYZE ─────────────────────────────────────
if st.button("Awaken the Echo", disabled=st.session_state.image is None):
    with st.spinner("Listening across centuries..."):
        result = generate_analysis(
            st.session_state.image,
            SYSTEM_PROMPT + ANALYSIS_PROMPT
        )
        st.session_state.analysis = result

# ── DISPLAY ─────────────────────────────────────
res = st.session_state.analysis
if isinstance(res, dict) and "monument_identification" in res:
    st.success("The echo has awakened.")

    st.subheader("Monument Identification")
    st.json(res["monument_identification"])

    st.subheader("Architecture")
    st.json(res["architectural_analysis"])

    st.subheader("History")
    st.json(res["historical_facts"])

    st.subheader("Preservation")
    st.json(res["visible_damage_assessment"])

    overlay = draw_damage_overlay(
        st.session_state.image,
        res.get("visible_damage_assessment", [])
    )
    st.image(overlay, caption="Damage overlay", use_container_width=True)

    story = res["first_person_narrative"]["story_from_monument_perspective"]
    if story:
        st.markdown(f"> *{story}*")
        audio = generate_audio(story)
        if audio:
            st.audio(audio)
            os.unlink(audio)

    st.download_button(
        "Download JSON",
        json.dumps(res, indent=2),
        file_name="echoes_of_eternity.json",
    )
