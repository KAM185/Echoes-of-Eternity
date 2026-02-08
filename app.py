import streamlit as st
from PIL import Image
import io
import json

from utils import generate_analysis_stream, draw_damage_overlay
from prompts import SYSTEM_PROMPT

# -------------------------------------------------
# PAGE CONFIG — DARK MODE ALWAYS
# -------------------------------------------------
st.set_page_config(
    page_title="Echoes of Eternity",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------
# HD BACKGROUND + GLASS UI + TITLE EFFECTS
# -------------------------------------------------
st.markdown(
    """
    <style>
    /* Full-screen HD background */
    .stApp {
        background-image: url("https://github.com/KAM185/Echoes-of-Eternity/blob/main/bg_final.jpg?raw=true");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    /* Fade-in animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Glass content box */
    .glass {
        background: rgba(10, 14, 24, 0.68);
        backdrop-filter: blur(12px);
        border-radius: 22px;
        padding: 3rem;
        margin: 2.5rem auto;
        max-width: 1200px;
        box-shadow: 0 25px 70px rgba(0,0,0,0.75);
        border: 1px solid rgba(255,255,255,0.12);
        animation: fadeIn 1.2s ease-out;
    }

    /* Title styling — eye-catching but elegant */
    h1 {
        font-family: Georgia, serif;
        font-size: clamp(2.8rem, 6vw, 4.3rem);
        text-align: center;
        margin-bottom: 0.4rem;
        letter-spacing: 2px;
        text-shadow:
            0 0 20px rgba(255, 215, 150, 0.35),
            0 0 40px rgba(120, 160, 255, 0.25);
    }

    .tagline {
        text-align: center;
        font-style: italic;
        opacity: 0.9;
        margin-bottom: 2.2rem;
    }

    h2 {
        margin-top: 2.2rem;
        border-bottom: 1px solid rgba(255,255,255,0.18);
        padding-bottom: 0.4rem;
    }

    ul {
        padding-left: 1.4rem;
    }

    .story {
        font-family: Georgia, serif;
        font-size: 1.18rem;
        line-height: 1.9;
        background: rgba(255,255,255,0.06);
        padding: 2rem;
        border-radius: 18px;
        margin-top: 1.8rem;
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
        <p class="tagline">When ancient stones finally speak.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# IMAGE UPLOAD
# -------------------------------------------------
uploaded = st.file_uploader(
    "Upload a monument image",
    type=["jpg", "jpeg", "png"]
)

if uploaded:
    st.session_state.image_bytes = uploaded.read()
    img = Image.open(io.BytesIO(st.session_state.image_bytes)).convert("RGB")
    st.image(img, caption="Uploaded monument", use_container_width=True)

    if st.button("Awaken the Echo"):
        with st.spinner("Listening across centuries…"):
            text = ""
            for chunk in generate_analysis_stream(
                image_bytes=st.session_state.image_bytes,
                system_prompt=SYSTEM_PROMPT
            ):
                text += chunk

            try:
                st.session_state.analysis = json.loads(text)
                st.success("The echo has awakened.")
            except Exception:
                st.error("The monument’s voice was unclear. Try another image.")
                st.session_state.analysis = None

# -------------------------------------------------
# RESULTS — CLEAN, CURATED PRESENTATION
# -------------------------------------------------
res = st.session_state.analysis

if res:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)

    # Identification
    ident = res.get("monument_identification", {})
    st.header("Monument Identification")
    st.markdown(f"**Name:** {ident.get('name','unknown')}")
    st.markdown(f"**Location:** {ident.get('city','unknown')}, {ident.get('country','unknown')}")
    st.markdown(f"**Confidence Score:** {ident.get('confidence_score',0.0)}")

    # Architecture
    arch = res.get("architectural_analysis", {})
    st.header("Architectural Analysis")
    st.markdown(f"**Style:** {arch.get('style','unknown')}")
    st.markdown(f"**Period / Dynasty:** {arch.get('period_or_dynasty','unknown')}")

    st.markdown("**Primary Materials:**")
    if arch.get("primary_materials"):
        for m in arch["primary_materials"]:
            st.markdown(f"- {m}")
    else:
        st.markdown("unknown")

    st.markdown("**Notable Features:**")
    if arch.get("distinct_features_visible"):
        for f in arch["distinct_features_visible"]:
            st.markdown(f"- {f}")
    else:
        st.markdown("unknown")

    # History
    hist = res.get("historical_facts", {})
    st.header("Historical Context")
    st.markdown(hist.get("summary","unknown"))

    # Damage
    st.header("Visible Damage Assessment")
    damages = res.get("visible_damage_assessment", [])

    if damages:
        base = Image.open(io.BytesIO(st.session_state.image_bytes)).convert("RGBA")
        overlay = draw_damage_overlay(base, damages)
        st.image(overlay, caption="Detected damage zones", use_container_width=True)

        for d in damages:
            st.markdown(
                f"""
                **Damage Type:** {d.get('damage_type','unknown')}  
                **Severity:** {d.get('severity','unknown')}  
                **Probable Cause:** {d.get('probable_cause','unknown')}
                """
            )
    else:
        st.info("No visible major damage detected.")

    # Restoration
    rest = res.get("restoration_guidance", {})
    st.header("Restoration Guidance")
    st.markdown(f"**Can be restored:** {rest.get('can_be_restored','unknown')}")

    if rest.get("recommended_methods"):
        st.markdown("**Recommended Methods:**")
        for r in rest["recommended_methods"]:
            st.markdown(f"- {r}")

    # Story
    story = res.get("first_person_narrative", {}).get("story_from_monument_perspective","")
    if story:
        st.header("The Monument Speaks")
        st.markdown(f"<div class='story'>{story}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)



