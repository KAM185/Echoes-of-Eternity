import streamlit as st
from PIL import Image
import io
import json

from utils import (
    generate_analysis_stream,
    draw_damage_overlay
)
from prompts import SYSTEM_PROMPT

# -------------------------------------------------
# Page config — force dark, icon, title
# -------------------------------------------------
st.set_page_config(
    page_title="Echoes of Eternity",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------
# Global CSS — dark mode + background + glass box
# -------------------------------------------------
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0b0e14;
        color: #f0f0f0;
    }

    .bg-layer {
        position: fixed;
        inset: 0;
        background-image: url("https://images.unsplash.com/photo-1588594276800-2de0522b3b73");
        background-size: cover;
        background-position: center;
        opacity: 0.25;
        z-index: -2;
    }

    .glass-box {
        background: rgba(20, 24, 38, 0.78);
        border-radius: 18px;
        padding: 2rem;
        margin-top: 2rem;
        box-shadow: 0 0 40px rgba(0,0,0,0.6);
    }

    h1, h2, h3 {
        font-family: "Georgia", serif;
    }
    </style>

    <div class="bg-layer"></div>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------
# Session state
# -------------------------------------------------
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None

# -------------------------------------------------
# Hero section
# -------------------------------------------------
st.markdown(
    """
    <div class="glass-box">
        <h1>Echoes of Eternity</h1>
        <h3><em>When ancient stones finally speak.</em></h3>
    </div>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------
# Upload section
# -------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload a monument image",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=False
)

if uploaded_file:
    image_bytes = uploaded_file.read()
    st.session_state.image_bytes = image_bytes
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    st.image(image, caption="Original uploaded image", use_container_width=True)

    if st.button("Awaken the Echo", use_container_width=False):
        with st.spinner("Listening to the stones…"):
            streamed_text = ""

            try:
                for chunk in generate_analysis_stream(
                    image_bytes=image_bytes,
                    system_prompt=SYSTEM_PROMPT
                ):
                    streamed_text += chunk

                result = json.loads(streamed_text)
                st.session_state.analysis_result = result
                st.success("The echo has awakened.")

            except Exception as e:
                st.error("The monument could not speak clearly. Please try another image.")
                st.session_state.analysis_result = None

# -------------------------------------------------
# Display analysis
# -------------------------------------------------
result = st.session_state.analysis_result

if result:
    st.markdown("<div class='glass-box'>", unsafe_allow_html=True)

    # ---------- Identification ----------
    st.header("Monument Identification")
    st.json(result.get("monument_identification", {}))

    # ---------- Architecture ----------
    st.header("Architecture")
    st.json(result.get("architectural_analysis", {}))

    # ---------- History ----------
    st.header("Historical Context")
    st.markdown(result.get("historical_facts", {}).get("summary", "unknown"))

    # ---------- Damage + overlay ----------
    st.header("Visible Damage Assessment")

    damage_list = result.get("visible_damage_assessment", [])

    if damage_list and st.session_state.image_bytes:
        base_img = Image.open(io.BytesIO(st.session_state.image_bytes)).convert("RGBA")
        overlay_img = draw_damage_overlay(base_img, damage_list)
        st.image(overlay_img, caption="Detected damage areas", use_container_width=True)

        for dmg in damage_list:
            with st.expander(dmg.get("damage_type", "Damage")):
                st.write(dmg)
    else:
        st.info("No visible major damage detected.")

    # ---------- Conservation ----------
    st.header("Conservation Issues")
    st.json(result.get("documented_conservation_issues", []))

    # ---------- Restoration ----------
    st.header("Restoration Guidance")
    st.json(result.get("restoration_guidance", {}))

    # ---------- Story ----------
    st.header("The Monument Speaks")
    st.markdown(
        f"""
        <blockquote style="font-size:1.1rem; font-family:Georgia,serif;">
        {result.get("first_person_narrative", {}).get("story_from_monument_perspective", "")}
        </blockquote>
        """
    )

    st.markdown("</div>", unsafe_allow_html=True)

