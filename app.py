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
/* Page background - slightly darker */
html, body, [data-testid="stAppViewContainer"] {
    background: url("https://github.com/KAM185/Echoes-of-Eternity/blob/main/bg_final.jpg?raw=true")
                no-repeat center center fixed;
    background-size: cover;
    filter: brightness(0.75);  /* darken the background slightly */
}

/* Remove Streamlit default header/footer */
[data-testid="stHeader"], footer {
    background: transparent;
}

/* Title container - fully transparent glass */
.title-glass {
    background: rgba(18, 22, 40, 0.25);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 15px;
    padding: 2rem 3rem;
    margin: 2rem auto;
    max-width: 1000px;
    border: 1px solid rgba(255,215,0,0.15);
    box-shadow: 0 15px 50px rgba(0,0,0,0.4);
    text-align: center;
}

/* Ancient, imposing, golden title */
.title-glass h1 {
    font-family: "Uncial Antiqua", "Cinzel Decorative", "Cinzel", serif;  /* ancient fonts */
    font-size: 5rem;
    color: #ffd700;  /* gold */
    text-shadow: 
        0 0 10px #ffd700,
        0 0 20px #ffec99,
        0 0 30px #ffd700,
        0 0 40px rgba(255,215,0,0.5);
    margin: 0;
}

/* Subtitle below title */
.title-glass p {
    font-family: "Cardo", Georgia, serif;
    font-size: 1.5rem;
    color: rgba(255,223,0,0.85);
    text-shadow: 0 0 5px rgba(255,223,0,0.4);
}

/* Glass container - rectangular */
.glass {
    background: rgba(18, 22, 40, 0.25);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border-radius: 15px;
    padding: 2rem 3rem;
    margin: 2rem auto;
    max-width: 1200px;
    border: 1px solid rgba(255,215,0,0.15);
    box-shadow: 0 15px 50px rgba(0,0,0,0.4);
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

/* Section subtitles */
h2, h3 {
    color: #ffd700;  /* gold */
    text-shadow: 0 0 10px rgba(255,215,0,0.6);
}

/* Chat box scroll */
.chat-container {
    max-height: 300px;
    overflow-y: auto;
    padding: 1rem;
    border-radius: 12px;
    background: rgba(255,255,255,0.05);
    margin-bottom: 1rem;
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
<div class="title-glass">
<h1>Echoes of Eternity</h1>
<p><em>When ancient stones finally speak.</em></p>
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
        if not st.session_state.image_bytes:
            st.error("No image uploaded. Please upload a monument image first.")
        else:
            with st.spinner("Listening across centuries…"):
                model = init_gemini_model()
                try:
                    raw = generate_analysis(
                        model,
                        st.session_state.image_bytes,
                        SYSTEM_PROMPT + ANALYSIS_PROMPT
                    )
                    # Safe JSON parsing
                    try:
                        parsed = json.loads(raw)
                    except Exception:
                        raw = raw.strip().split("{", 1)[-1]
                        raw = "{" + raw
                        parsed = json.loads(raw)

                    st.session_state.analysis = parsed
                    st.session_state.chat = []

                except Exception as e:
                    st.error("The monument could not speak. Please try again later.")
                    st.error(f"Debug info: {str(e)}")  # Remove in production

# ---------------- RESULTS ----------------
res = st.session_state.analysis

if res:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)

    st.subheader("🗿 Monument Identification")
    st.json(res.get("monument_identification", {}))

    st.subheader("🏛 Architecture")
    st.json(res.get("architectural_analysis", {}))

    st.subheader("📜 Historical Context")
    st.write(res.get("historical_facts", {}).get("summary", ""))

    st.subheader("🛠 Preservation Condition")
    damages = res.get("visible_damage_assessment", [])
    overlay = draw_damage_overlay(image, damages)
    st.image(overlay, use_container_width=True)

    st.subheader("🗣 The Monument Speaks")
    st.markdown(
        f"<div class='story'>{res.get('first_person_narrative', {}).get('story_from_monument_perspective', '')}</div>",
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- ASK THE ECHO ----------------
if res:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.subheader("🔮 Ask the Echo")

    q = st.text_input("Ask the monument a question…")

    if q:
        try:
            reply = chat_with_monument(
                res,
                st.session_state.chat,
                q,
                CHAT_PROMPT
            )
            st.session_state.chat.append({"role": "user", "content": q})
            st.session_state.chat.append({"role": "monument", "content": reply})
        except Exception as e:
            st.error("The echo could not respond. Try again later.")
            st.error(f"Debug info: {str(e)}")  # remove in production

    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for m in st.session_state.chat:
        speaker = "You" if m["role"] == "user" else "Monument"
        st.markdown(f"**{speaker}:** {m['content']}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

