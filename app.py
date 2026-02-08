import os
import json
import streamlit as st
from PIL import Image

from utils import (
    generate_analysis,
    generate_audio,
    enhance_for_viewing,
)
from prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Echoes of Eternity",
    page_icon="🏛️",
    layout="centered",
)

# -------------------------------------------------
# Background (FULL image visible)
# -------------------------------------------------
bg_url = "https://raw.githubusercontent.com/KAM185/Echoes-of-Eternity/main/bg_final.jpg"

st.markdown(
    f"""
    <style>
        .stApp {{
            background: url('{bg_url}') no-repeat center center fixed;
            background-size: contain;
            background-color: #0b0e1a;
        }}

        /* Central translucent rectangular panel */
        .block-container {{
            background: rgba(15, 18, 35, 0.45);
            backdrop-filter: blur(16px);
            border-radius: 18px;
            padding: 3rem 2.5rem;
            max-width: 1100px;
            margin: 3rem auto;
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 20px 60px rgba(0,0,0,0.6);
        }}

        /* Title styling */
        h1 {{
            font-family: 'Georgia', serif;
            font-size: 4.5rem !important;
            color: #f5e6c8;
            text-align: center;
            text-shadow:
                0 0 12px rgba(0,0,0,0.9),
                0 0 30px rgba(212,179,122,0.6);
            margin-bottom: 0.5rem;
        }}

        h3 {{
            text-align: center;
            font-style: italic;
            color: #d4b37a;
            text-shadow: 0 0 10px rgba(0,0,0,0.8);
            margin-bottom: 2rem;
        }}

        /* Text readability */
        p, div, span, label {{
            color: #f0e8d0 !important;
            text-shadow: 0 1px 6px rgba(0,0,0,0.85);
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Title
# -------------------------------------------------
st.markdown("<h1>Echoes of Eternity</h1>", unsafe_allow_html=True)
st.markdown(
    "<h3>When ancient stones finally speak.</h3>",
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Session state
# -------------------------------------------------
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "image" not in st.session_state:
    st.session_state.image = None

# -------------------------------------------------
# Image upload
# -------------------------------------------------
uploaded = st.file_uploader(
    "Upload or capture a monument image (jpg / png)",
    type=["jpg", "jpeg", "png"],
)

if uploaded:
    try:
        image = Image.open(uploaded).convert("RGB")
        st.session_state.image = image

        enhance_view = st.toggle(
            "Enhance image for viewing (no details added)",
            value=False,
            help="Photometric enhancement only. Analysis uses the original image.",
        )

        display_image = (
            enhance_for_viewing(image) if enhance_view else image
        )

        st.image(
            display_image,
            caption=(
                "Enhanced for visibility only (no detail changes)"
                if enhance_view
                else "Original uploaded image"
            ),
            use_container_width=True,
        )

    except Exception as e:
        st.error(f"Could not load image: {e}")

# -------------------------------------------------
# Analysis button
# -------------------------------------------------
if st.button(
    "Awaken the Echo",
    type="primary",
    disabled=st.session_state.image is None,
):
    with st.spinner("Listening across centuries…"):
        try:
            st.session_state.analysis = generate_analysis(
                st.session_state.image,
                SYSTEM_PROMPT + ANALYSIS_PROMPT,
            )
            st.success("The echo has awakened.")
        except Exception as e:
            st.error(str(e))

# -------------------------------------------------
# Results
# -------------------------------------------------
result = st.session_state.analysis

if result:
    st.subheader("Monument Identification")
    st.json(result["monument_identification"])

    st.subheader("Architectural Analysis")
    st.json(result["architectural_analysis"])

    st.subheader("Historical Facts")
    st.json(result["historical_facts"])

    st.subheader("Visible Damage Assessment")
    if result["visible_damage_assessment"]:
        st.json(result["visible_damage_assessment"])
    else:
        st.info("No visible damage confidently identified.")

    st.subheader("Documented Conservation Issues")
    st.json(result["documented_conservation_issues"])

    st.subheader("Restoration Guidance")
    st.json(result["restoration_guidance"])

    story = result["first_person_narrative"]["story_from_monument_perspective"]

    if story:
        st.markdown("### The Monument Speaks")
        st.markdown(story)

        audio_path = generate_audio(story)
        if audio_path:
            st.audio(audio_path)
            try:
                os.unlink(audio_path)
            except Exception:
                pass

    st.download_button(
        "Download Scientific Report (JSON)",
        json.dumps(result, indent=2, ensure_ascii=False),
        file_name="echoes_of_eternity_report.json",
        mime="application/json",
    )

