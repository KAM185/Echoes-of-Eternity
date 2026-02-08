import os
import json
import streamlit as st
from PIL import Image

from utils import (
    generate_analysis_stream,
    init_gemini,
)

from prompts import SYSTEM_PROMPT


# ────────────────────────────────────────────────
# Force dark mode + page config
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="Echoes of Eternity",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ────────────────────────────────────────────────
# Dark mode enforcement
# ────────────────────────────────────────────────
st.markdown(
    """
    <script>
    document.documentElement.setAttribute('data-theme', 'dark');
    </script>
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────
# Background + translucent container
# ────────────────────────────────────────────────
BG_URL = "https://raw.githubusercontent.com/KAM185/Echoes-of-Eternity/main/bg_final.jpg"

st.markdown(
    f"""
    <style>
    .stApp {{
        background: url("{BG_URL}") center/cover no-repeat fixed;
        background-color: #050814;
    }}

    .block-container {{
        background: rgba(10, 14, 30, 0.35);
        backdrop-filter: blur(18px);
        border-radius: 26px;
        padding: 3rem;
        margin-top: 2rem;
        box-shadow: 0 0 80px rgba(0,0,0,0.7);
        border: 1px solid rgba(200,180,255,0.25);
        max-width: 1200px;
    }}

    h1 {{
        text-align: center;
        font-size: 4.5rem;
        background: linear-gradient(90deg,#7aa2ff,#cdb4ff,#ffd6a5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 40px rgba(200,180,255,0.8);
        letter-spacing: 4px;
    }}

    h3 {{
        text-align: center;
        color: #e6d8b8;
        margin-bottom: 2rem;
    }}

    p, span, div {{
        color: #e9e3d0;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────
# Title
# ────────────────────────────────────────────────
st.markdown("<h1>Echoes of Eternity</h1>", unsafe_allow_html=True)
st.markdown("<h3><em>Whispers of history in every stone</em></h3>", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# Session state
# ────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None

if "image" not in st.session_state:
    st.session_state.image = None


# ────────────────────────────────────────────────
# Image uploader
# ────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload a monument image (jpg / png)",
    type=["jpg", "jpeg", "png"],
)

if uploaded:
    img = Image.open(uploaded).convert("RGB")
    st.session_state.image = img
    st.image(img, caption="Original uploaded image", use_container_width=True)


# ────────────────────────────────────────────────
# Analysis trigger
# ────────────────────────────────────────────────
if st.button("Awaken the Echo", type="primary", disabled=st.session_state.image is None):
    st.session_state.result = None

    with st.spinner("Listening across centuries…"):
        placeholder = st.empty()
        full_text = ""

        for chunk in generate_analysis_stream(
            st.session_state.image,
            SYSTEM_PROMPT,
        ):
            full_text += chunk
            placeholder.markdown(full_text + " ▌")

        try:
            cleaned = full_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```", 1)[-1].rsplit("```", 1)[0]

            st.session_state.result = json.loads(cleaned)
            placeholder.empty()
            st.success("The echo has awakened.")

        except Exception:
            st.error("Model output was not valid JSON.")
            st.code(full_text)


# ────────────────────────────────────────────────
# Results rendering (SAFE)
# ────────────────────────────────────────────────
res = st.session_state.result

if res:
    st.markdown("## Monument Identification")
    st.json(res.get("monument_identification", {}))

    st.markdown("## Architectural Analysis")
    st.json(res.get("architectural_analysis", {}))

    st.markdown("## Historical Facts")
    st.json(res.get("historical_facts", {}))

    st.markdown("## Visible Damage Assessment")
    st.json(res.get("visible_damage_assessment", []))

    st.markdown("## Documented Conservation Issues")
    st.json(res.get("documented_conservation_issues", []))

    st.markdown("## Restoration Guidance")
    st.json(res.get("restoration_guidance", {}))

    story = (
        res.get("first_person_narrative", {})
        .get("story_from_monument_perspective", "")
    )

    if story:
        st.markdown("## Voice of the Monument")
        st.markdown(
            f"""
            <div style="
                background: rgba(20,25,45,0.5);
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 0 40px rgba(200,180,255,0.3);
            ">
            {story}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.download_button(
        "Download Full Analysis (JSON)",
        json.dumps(res, indent=2, ensure_ascii=False),
        file_name="echoes_of_eternity.json",
        mime="application/json",
    )
