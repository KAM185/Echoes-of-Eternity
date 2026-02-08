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

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Echoes of Eternity",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- GLOBAL CSS ----------------
st.markdown("""
<style>
/* Page background */
html, body, [data-testid="stAppViewContainer"] {
    background: url("https://github.com/KAM185/Echoes-of-Eternity/blob/main/bg_final.jpg?raw=true")
                no-repeat center center fixed;
    background-size: cover;
}

/* Remove Streamlit default header/footer */
[data-testid="stHeader"], footer {
    background: transparent;
}

/* Glass container - rectangular and transparent */
.glass {
    background: rgba(18, 22, 40, 0.25);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border-radius: 15px;
    padding: 2rem 3rem;
    margin: 2rem auto;
    max-width: 1200px;
    border: 1px solid rgba(255,255,255,0.15);
    box-shadow: 0 15px 50px rgba(0,0,0,0.4);
}

/* Ancient-looking title */
h1 {
    font-family: "Cinzel", serif;
    font-size: 4rem;
    text-align: center;
    color: #f6e8c9;
    text-shadow: 0 0 15px #ffd77f, 0 0 25px #f6e8c9;
}

/* Story block inside container */
.story {
    font-family: Georgia, serif;
    font-size: 1.25rem;
    line-height: 1.9;
    background: rgba(255,255,255,0.07);
    padding: 2rem;
    border-radius: 10px;
    box-shadow: inset 0 0 20px rgba(255,255,255,0.07);
}

/* Subtitles for sections */
h2, h3 {
    color: #ffeabf;
    text-shadow: 0 0 10px rgba(255,235,190,0.8);
}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None
if "chat" not in st.session_state:
    st.session_state.chat = []

# ---------------- HERO ----------------
st.markdown("""
<div class="glass">
<h1>Echoes of Eternity</h1>
<p style="text-align:center; font-size:1.5rem;">
<em>When ancient stones finally speak.</em>
</p>
</div>
""", unsafe_allow_html=True)

# ---------------- UPLOADER ----------------
file = st.file_uploader(
    "Upload or capture a monument image",
    type=["jpg", "jpeg", "png"]
)

if file:
    st.session_state.image_bytes = file.read()
    image = Image.open(io.BytesIO(st.session_state.image_bytes)).convert("RGB")
    st.image(image, use_container_width=True)

    if st.button("Awaken the Echo"):
        with st.spinner("Listening across centuries…"):
            model = init_gemini_model()

            raw = generate_analysis(
                model,
                st.session_state.image_bytes,
                SYSTEM_PROMPT + ANALYSIS_PROMPT
            )

            # ---------- SAFE JSON PARSING ----------
            try:
                parsed = json.loads(raw)
            except Exception:
                # last-resort cleanup
                raw = raw.strip().split("{", 1)[-1]
                raw = "{" + raw
                parsed = json.loads(raw)

            st.session_state.analysis = parsed
            st.session_state.chat = []

# ---------------- RESULTS ----------------
res = st.session_state.analysis

if res:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)

    st.subheader("🗿 Monument Identification")
    st.json(res["monument_identification"])

    st.subheader("🏛 Architecture")
    st.json(res["architectural_analysis"])

    st.subheader("📜 Historical Context")
    st.write(res["historical_facts"]["summary"])

    st.subheader("🛠 Preservation Condition")

    damages = res["visible_damage_assessment"]
    overlay = draw_damage_overlay(image, damages)
    st.image(overlay, use_container_width=True)

    st.subheader("🗣 The Monument Speaks")
    st.markdown(
        f"<div class='story'>{res['first_person_narrative']['story_from_monument_perspective']}</div>",
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- ASK THE ECHO ----------------
if res:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("🔮 Ask the Echo")

    q = st.text_input("Ask the monument a question…")

    if q:
        reply = chat_with_monument(
            res,
            st.session_state.chat,
            q,
            CHAT_PROMPT
        )
        st.session_state.chat.append({"role": "user", "content": q})
        st.session_state.chat.append({"role": "monument", "content": reply})

    for m in st.session_state.chat:
        speaker = "You" if m["role"] == "user" else "Monument"
        st.markdown(f"**{speaker}:** {m['content']}")

    st.markdown("</div>", unsafe_allow_html=True)
