# app.py
import streamlit as st
from PIL import Image, ImageEnhance
import io
import json

from utils import generate_analysis_stream, draw_damage_overlay
from prompts import SYSTEM_PROMPT


# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Echoes of Eternity",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -------------------------------------------------
# BACKGROUND (YOUR ORIGINAL)
# -------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://github.com/KAM185/Echoes-of-Eternity/blob/main/bg_final.jpg?raw=true");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    .glass {
        background: rgba(10, 14, 24, 0.68);
        backdrop-filter: blur(12px);
        border-radius: 22px;
        padding: 3rem;
        margin: 2.5rem auto;
        max-width: 1200px;
        box-shadow: 0 25px 70px rgba(0,0,0,0.75);
        border: 1px solid rgba(255,255,255,0.12);
    }

    h1 {
        font-family: Georgia, serif;
        text-align: center;
        letter-spacing: 2px;
    }

    .story {
        font-family: Georgia, serif;
        font-size: 1.15rem;
        line-height: 1.9;
        background: rgba(255,255,255,0.06);
        padding: 2rem;
        border-radius: 18px;
        border-left: 4px solid rgba(255,215,150,0.7);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None


# -------------------------------------------------
# HERO
# -------------------------------------------------
st.markdown(
    """
    <div class="glass">
        <h1>Echoes of Eternity</h1>
        <p style="text-align:center;font-style:italic;">
        When ancient stones finally speak.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------
# IMAGE UPLOAD
# -------------------------------------------------
uploaded = st.file_uploader(
    "Upload a monument image (JPG / PNG)",
    type=["jpg", "jpeg", "png"]
)

enhance_toggle = st.checkbox("Enhance image for viewing (does NOT affect AI)")

if uploaded:
    st.session_state.image_bytes = uploaded.read()
    img = Image.open(io.BytesIO(st.session_state.image_bytes)).convert("RGB")

    if enhance_toggle:
        img = ImageEnhance.Contrast(img).enhance(1.15)
        img = ImageEnhance.Sharpness(img).enhance(1.2)

    st.image(img, caption="Uploaded Monument", use_container_width=True)

    if st.button("Awaken the Echo"):
        with st.spinner("Listening across centuries…"):
            text = ""
            for chunk in generate_analysis_stream(
                image_bytes=st.session_state.image_bytes,
                system_prompt=SYSTEM_PROMPT,
            ):
                text += chunk

            try:
                st.session_state.analysis = json.loads(text)
                st.success("The monument has spoken.")
            except Exception:
                st.error("Analysis could not be parsed.")


# -------------------------------------------------
# RESULTS
# -------------------------------------------------
res = st.session_state.analysis

if res:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)

    ident = res["monument_identification"]
    st.header("Monument Identification")
    st.write(f"**Name:** {ident['name']}")
    st.write(f"**Location:** {ident['city']}, {ident['country']}")
    st.write(f"**Confidence:** {ident['confidence_score']}")

    arch = res["architectural_analysis"]
    st.header("Architectural Analysis")
    st.write(f"**Style:** {arch['style']}")
    st.write(f"**Period:** {arch['period_or_dynasty']}")
    st.write("**Materials:**")
    st.write(arch["primary_materials"] or "unknown")

    hist = res["historical_facts"]
    st.header("Historical Context")
    st.write(hist["summary"])

    st.header("Visible Damage Assessment")
    damages = res["visible_damage_assessment"]

    if damages and damages[0]["damage_type"] != "none observed":
        base = Image.open(io.BytesIO(st.session_state.image_bytes)).convert("RGBA")
        overlay = draw_damage_overlay(base, damages)
        st.image(overlay, use_container_width=True)
    else:
        st.info("No visible major damage detected.")

    rest = res["restoration_guidance"]
    st.header("Restoration Guidance")
    st.write(f"**Can be restored:** {rest['can_be_restored']}")
    st.write("**Preventive Measures:**")
    st.write(rest["preventive_measures"])

    story = res["first_person_narrative"]["story_from_monument_perspective"]
    if story:
        st.header("The Monument Speaks")
        st.markdown(f"<div class='story'>{story}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

