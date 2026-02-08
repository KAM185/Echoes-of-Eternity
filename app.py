# app.py
import os
import json
import streamlit as st
from PIL import Image
import io

from utils import (
    generate_analysis_stream,
    draw_damage_overlay,
    generate_audio,
    init_gemini,
)
from prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT, CHAT_PROMPT

# ────────────────────────────────────────────────
# Page config
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="Echoes of Eternity",
    page_icon="🪨",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ────────────────────────────────────────────────
# Improved dark stone theme + better targeting
# ────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* Main app background */
        .stApp {
            background: radial-gradient(circle at top, #2b2b2b, #0f0f0f) !important;
        }
        section[data-testid="stAppViewContainer"] {
            background: transparent !important;
        }
        .block-container {
            background: transparent !important;
            padding-top: 2rem !important;
        }

        /* Text & typography */
        h1, h2, h3, h4, h5, h6, p, div, span, li {
            color: #f5f0e6 !important;
            font-family: "Georgia", serif;
        }

        /* Hero styling */
        h1 {
            text-align: center;
            font-size: 3.2rem;
            margin-bottom: 0.2rem;
        }
        h3 em {
            font-size: 1.4rem;
            opacity: 0.85;
            display: block;
            text-align: center;
        }

        /* Story narration */
        .story {
            font-family: "Georgia", serif;
            font-size: 1.15em;
            line-height: 1.7;
            color: #e0d8c3 !important;
            background: rgba(30, 30, 30, 0.6);
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid #444;
        }

        /* Expanders */
        .stExpander {
            background-color: rgba(40, 40, 40, 0.75) !important;
            border: 1px solid #555 !important;
            color: #f0e9d8 !important;
        }
        details summary {
            color: #e0d8c3 !important;
        }

        /* Fix uploader & buttons contrast */
        .stFileUploader label, .stButton > button {
            color: #111 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────
# Session state
# ────────────────────────────────────────────────
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "image" not in st.session_state:
    st.session_state.image = None
if "overlay_image" not in st.session_state:
    st.session_state.overlay_image = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ────────────────────────────────────────────────
# Hero
# ────────────────────────────────────────────────
st.markdown("<h1>Echoes of Eternity</h1>", unsafe_allow_html=True)
st.markdown(
    "<h3><em>When ancient stones finally speak.</em></h3>",
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────
# Image uploader
# ────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload or capture a monument image (jpg/png)",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file).convert("RGB")
        st.session_state.image = image
        st.image(image, caption="Uploaded image", use_container_width=True)
    except Exception as e:
        st.error(f"Could not load image: {e}")

# ────────────────────────────────────────────────
# Analysis button & logic
# ────────────────────────────────────────────────
if st.button("Awaken the Echo", type="primary", disabled=st.session_state.image is None):
    with st.spinner("Awakening the echo..."):
        st.session_state.analysis_result = None

        stream_placeholder = st.empty()

        full_response = ""
        for chunk in generate_analysis_stream(
            st.session_state.image,
            SYSTEM_PROMPT + ANALYSIS_PROMPT,
            primary_model="gemini-3-pro-preview",
            fallback_model="gemini-3-flash-preview",
        ):
            full_response += chunk
            stream_placeholder.markdown(full_response + "▌")

        # Final parse after stream completes
        try:
            # Clean up possible trailing garbage
            json_str = full_response.strip()
            if json_str.endswith("```"):  # sometimes models add markdown
                json_str = json_str.rsplit("```", 1)[0].strip()
            result = json.loads(json_str)
            st.session_state.analysis_result = result
            stream_placeholder.empty()  # remove streaming text
            st.success("The monument has spoken.")
        except Exception as e:
            st.error("Could not parse the response as valid JSON.")
            stream_placeholder.markdown(f"**Raw response (for debugging):**\n\n{full_response}")
            st.session_state.analysis_result = None

# ────────────────────────────────────────────────
# Display results if available
# ────────────────────────────────────────────────
if st.session_state.analysis_result:
    res = st.session_state.analysis_result

    with st.expander("Identification", expanded=True):
        st.markdown(res.get("identification", "Unknown"))

    with st.expander("Architecture"):
        st.markdown(res.get("architecture", "Not described"))

    with st.expander("Significance"):
        st.markdown(res.get("significance", "Not described"))

    with st.expander("Preservation Assessment"):
        pres = res.get("preservation", {})
        st.markdown(f"**Severity score:** {pres.get('severity_score', 'N/A')}/100")

        damage_types = pres.get("damage_types", [])
        if damage_types:
            st.markdown("**Damage types:** " + ", ".join(damage_types))
        else:
            st.markdown("**Damage types:** None major detected")

        damaged_areas = pres.get("damaged_areas", [])
        if damaged_areas:
            st.markdown(f"**Detected damaged areas:** {len(damaged_areas)}")
        else:
            st.info("No visible major damage detected in the provided photo.")

    # Damage overlay
    overlay = draw_damage_overlay(
        st.session_state.image,
        damaged_areas
    )
    st.session_state.overlay_image = overlay
    st.image(overlay, caption="Damage & preservation overlay", use_container_width=True)

    # Storytelling + audio
    story = res.get("storytelling", "")
    if story:
        st.markdown(f'<div class="story">{story}</div>', unsafe_allow_html=True)

        audio_path = generate_audio(story)
        if audio_path:
            st.audio(audio_path)
            # Cleanup after playback attempt
            try:
                os.unlink(audio_path)
            except:
                pass
        else:
            # Browser TTS fallback
            st.components.v1.html(
                f"""
                <script>
                const utterance = new SpeechSynthesisUtterance({json.dumps(story)});
                utterance.lang = 'en-US';
                utterance.rate = 0.9;
                speechSynthesis.speak(utterance);
                </script>
                """,
                height=0
            )

    # Download result
    st.download_button(
        label="Download full analysis (JSON)",
        data=json.dumps(res, indent=2, ensure_ascii=False),
        file_name="echo_analysis.json",
        mime="application/json"
    )

# ────────────────────────────────────────────────
# Chat section
# ────────────────────────────────────────────────
st.markdown("## Ask the Echo")

question = st.text_input("Your question to the monument...", key="chat_input")

if question and question.strip():
    st.session_state.chat_history.append({"role": "user", "content": question})

    with st.spinner("The monument reflects..."):
        try:
            model = init_gemini("gemini-3-pro-preview")
        except:
            model = init_gemini("gemini-3-flash-preview")

        try:
            chat = model.start_chat(history=[
                {"role": m["role"], "parts": [m["content"]]}
                for m in st.session_state.chat_history[:-1]
            ])
            response = chat.send_message(question)
            reply = response.text
        except Exception as e:
            st.error(f"Chat failed: {str(e)}")
            reply = "I am silent for now... the winds carry my voice away."

    st.session_state.chat_history.append({"role": "monument", "content": reply})

# Display chat history
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Monument:** {msg['content']}")
