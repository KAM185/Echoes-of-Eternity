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
# BACKGROUND + GLASS PANEL
# -------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1604079628040-94301bb21b91");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    .glass {
        background: rgba(18, 22, 35, 0.72);
        backdrop-filter: blur(14px);
        border-radius: 20px;
        padding: 2.5rem;
        margin: 2rem auto;
        max-width: 1200px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.65);
    }

    h1 {
        font-family: Georgia, serif;
        font-size: 4rem;
        text-align: center;
    }

    h2 {
        margin-top: 2rem;
        border-bottom: 1px solid rgba(255,255,255,0.15);
        padding-bottom: 0.4rem;
    }

    .label {
        font-weight: 600;
        color: #e8d8b0;
    }

    ul {
        padding-left: 1.2rem;
    }

    .story {
        font-family: Georgia, serif;
        font-size: 1.15rem;
        line-height: 1.9;
        background: rgba(255,255,255,0.05);
        padding: 1.8rem;
        border-radius: 16px;
        margin-top: 1.5rem;
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
        <p style="text-align:center; font-style:italic;">
            When ancient stones finally speak.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# UPLOAD
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
                st.error("The monument’s voice was unclear. Please try another image.")
                st.session_state.analysis = None

# -------------------------------------------------
# RESULTS — BEAUTIFUL FORMAT
# -------------------------------------------------
res = st.session_state.analysis

if res:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)

    # ---------------- Identification ----------------
    ident = res.get("monument_identification", {})
    st.header("Monument Identification")
    st.markdown(f"**Name:** {ident.get('name', 'unknown')}")
    st.markdown(f"**Location:** {ident.get('city', 'unknown')}, {ident.get('country', 'unknown')}")
    st.markdown(f"**Confidence Score:** {ident.get('confidence_score', 0.0)}")

    # ---------------- Architecture ----------------
    arch = res.get("architectural_analysis", {})
    st.header("Architectural Analysis")

    st.markdown(f"**Style:** {arch.get('style', 'unknown')}")
    st.markdown(f"**Period / Dynasty:** {arch.get('period_or_dynasty', 'unknown')}")
    st.markdown("**Primary Materials:**")
    st.markdown(
        "- " + "\n- ".join(arch.get("primary_materials", []))
        if arch.get("primary_materials") else "unknown"
    )

    st.markdown("**Notable Visible Features:**")
    st.markdown(
        "- " + "\n- ".join(arch.get("distinct_features_visible", []))
        if arch.get("distinct_features_visible") else "unknown"
    )

    # ---------------- History ----------------
    hist = res.get("historical_facts", {})
    st.header("Historical Context")
    st.markdown(hist.get("summary", "unknown"))

    if hist.get("timeline"):
        st.markdown("**Timeline:**")
        for t in hist["timeline"]:
            st.markdown(f"- {t}")

    # ---------------- Damage ----------------
    st.header("Visible Damage Assessment")
    damages = res.get("visible_damage_assessment", [])

    if damages:
        base = Image.open(io.BytesIO(st.session_state.image_bytes)).convert("RGBA")
        overlay = draw_damage_overlay(base, damages)
        st.image(overlay, caption="Detected damage zones", use_container_width=True)

        for d in damages:
            st.markdown(
                f"""
                **Damage Type:** {d.get("damage_type","unknown")}  
                **Severity:** {d.get("severity","unknown")}  
                **Cause:** {d.get("probable_cause","unknown")}
                """
            )
    else:
        st.info("No visible major damage detected.")

    # ---------------- Conservation ----------------
    st.header("Conservation Issues")
    for issue in res.get("documented_conservation_issues", []):
        st.markdown(
            f"- **{issue.get('issue','unknown')}** — {issue.get('historical_or_environmental_reason','')}"
        )

    # ---------------- Restoration ----------------
    rest = res.get("restoration_guidance", {})
    st.header("Restoration Guidance")
    st.markdown(f"**Can be restored:** {rest.get('can_be_restored','unknown')}")
    st.markdown("**Recommended Methods:**")
    st.markdown(
        "- " + "\n- ".join(rest.get("recommended_methods", []))
        if rest.get("recommended_methods") else "unknown"
    )

    # ---------------- Story ----------------
    story = res.get("first_person_narrative", {}).get("story_from_monument_perspective", "")
    if story:
        st.header("The Monument Speaks")
        st.markdown(f"<div class='story'>{story}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


