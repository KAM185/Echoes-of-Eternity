import os
import json
import io
import streamlit as st
from PIL import Image

from utils import (
    init_gemini_model,
    generate_analysis,
    draw_damage_overlay,
    chat_with_monument
)
from prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT, CHAT_PROMPT

# -------------------------------------------------
# PAGE CONFIG — DARK MODE FORCED
# -------------------------------------------------
st.set_page_config(
    page_title="Echoes of Eternity",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------
# GLOBAL STYLES (HD BG + GLASS UI)
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
        color: #f0f0f0;
    }

    .glass {
        background: rgba(10, 14, 28, 0.72);
        backdrop-filter: blur(14px);
        border-radius: 22px;
        padding: 3rem;
        margin: 2.5rem auto;
        max-width: 1200px;
        box-shadow: 0 30px 80px rgba(0,0,0,0.75);
        border: 1px solid rgba(255,255,255,0.15);
    }

    h1 {
        font-family: Georgia, serif;
        font-size: clamp(2.8rem, 5.8vw, 4.4rem);
        text-align: center;
        letter-spacing: 3px;
        text-shadow:
            0 0 20px rgba(255,215,150,0.35),
            0 0 40px rgba(120,160,255,0.25);
    }

    .tagline {
        text-align: center;
        font-style: italic;
        opacity: 0.9;
        margin-bottom: 2.5rem;
    }

    .story {
        font-family: Georgia, serif;
        font-size: 1.2rem;
        line-height: 1.9;
        background: rgba(255,255,255,0.06);
        padding: 2rem;
        border-radius: 18px;
        border-left: 4px solid rgba(255,215,150,0.7);
        margin-top: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
for key in ["analysis", "image_bytes", "chat_history"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "chat_history" else []

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
    "Upload a monument image (jpg / png)",
    type=["jpg", "jpeg", "png"],
)

if uploaded:
    st.session_state.image_bytes = uploaded.read()
    image = Image.open(io.BytesIO(st.session_state.image_bytes)).convert("RGB")
    st.image(image, caption="Uploaded monument", use_container_width=True)

    if st.button("Awaken the Echo"):
        with st.spinner("Listening across centuries…"):
            try:
                model = init_gemini_model()
                result_text = generate_analysis(
                    model=model,
                    image_bytes=st.session_state.image_bytes,
                    prompt=SYSTEM_PROMPT + ANALYSIS_PROMPT,
                )
                st.session_state.analysis = json.loads(result_text)
                st.session_state.chat_history = []
                st.success("The monument has spoken.")
            except Exception as e:
                st.error("Unable to interpret this monument. Try another image.")
                st.session_state.analysis = None

# -------------------------------------------------
# RESULTS PRESENTATION
# -------------------------------------------------
res = st.session_state.analysis

if res:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)

    ident = res["monument_identification"]
    st.header("Monument Identification")
    st.markdown(f"**Name:** {ident['name']}")
    st.markdown(f"**Location:** {ident['city']}, {ident['country']}")
    st.markdown(f"**Confidence Score:** {ident['confidence_score']}")

    arch = res["architectural_analysis"]
    st.header("Architectural Analysis")
    st.markdown(f"**Style:** {arch['style']}")
    st.markdown(f"**Period / Dynasty:** {arch['period_or_dynasty']}")
    st.markdown("**Primary Materials:**")
    for m in arch["primary_materials"]:
        st.markdown(f"- {m}")
    st.markdown("**Distinct Features:**")
    for f in arch["distinct_features_visible"]:
        st.markdown(f"- {f}")

    hist = res["historical_facts"]
    st.header("Historical Context")
    st.markdown(hist["summary"])

    damages = res["visible_damage_assessment"]
    st.header("Visible Damage Assessment")

    if damages:
        base = Image.open(io.BytesIO(st.session_state.image_bytes)).convert("RGBA")
        overlay = draw_damage_overlay(base, damages)
        st.image(overlay, caption="Detected damage regions", use_container_width=True)

        for d in damages:
            st.markdown(
                f"""
                **Type:** {d['damage_type']}  
                **Severity:** {d['severity']}  
                **Cause:** {d['probable_cause']}
                """
            )
    else:
        st.info("No visible major damage detected.")

    rest = res["restoration_guidance"]
    st.header("Restoration Guidance")
    st.markdown(f"**Can be restored:** {rest['can_be_restored']}")
    for r in rest["recommended_methods"]:
        st.markdown(f"- {r}")

    story = res["first_person_narrative"]["story_from_monument_perspective"]
    if story:
        st.header("The Monument Speaks")
        st.markdown(f"<div class='story'>{story}</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# ASK THE ECHO (CHAT)
# -------------------------------------------------
if res:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.header("Ask the Echo")

    question = st.text_input("Ask a question to the monument…")

    if question:
        with st.spinner("The monument responds…"):
            reply = chat_with_monument(
                analysis=res,
                chat_history=st.session_state.chat_history,
                user_question=question,
                system_prompt=CHAT_PROMPT,
            )
            st.session_state.chat_history.append(
                {"role": "user", "content": question}
            )
            st.session_state.chat_history.append(
                {"role": "monument", "content": reply}
            )

    for msg in st.session_state.chat_history:
        speaker = "You" if msg["role"] == "user" else "Monument"
        st.markdown(f"**{speaker}:** {msg['content']}")

    st.markdown("</div>", unsafe_allow_html=True)
