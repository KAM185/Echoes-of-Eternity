import os
import json
import time
import tempfile
from typing import List

from PIL import Image, ImageEnhance, ImageFilter
from gtts import gTTS

import google.generativeai as genai
import streamlit as st

# -------------------------------------------------
# Gemini configuration
# -------------------------------------------------
@st.cache_resource
def init_gemini(model_name: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

# -------------------------------------------------
# Model cascade (7 models)
# -------------------------------------------------
MODEL_PRIORITY: List[str] = [
    "gemini-3-pro-preview",
    "gemini-3-pro",
    "gemini-3-flash-preview",
    "gemini-3-flash",
    "gemini-2.5-pro-preview",
    "gemini-2.0-pro",
    "gemini-1.5-pro",
]

# -------------------------------------------------
# Safe image enhancement (viewer-only)
# -------------------------------------------------
def enhance_for_viewing(image: Image.Image) -> Image.Image:
    enhanced = image.copy()

    enhanced = ImageEnhance.Contrast(enhanced).enhance(1.15)
    enhanced = ImageEnhance.Brightness(enhanced).enhance(1.05)

    enhanced = enhanced.filter(
        ImageFilter.UnsharpMask(
            radius=1,
            percent=80,
            threshold=3,
        )
    )

    return enhanced

# -------------------------------------------------
# Gemini analysis with cascade
# -------------------------------------------------
def generate_analysis(image: Image.Image, prompt: str) -> dict:
    last_error = None

    for model_name in MODEL_PRIORITY:
        try:
            model = init_gemini(model_name)
            response = model.generate_content(
                [prompt, image],
                generation_config={
                    "response_mime_type": "application/json"
                },
            )

            text = response.text.strip()

            if text.startswith("```"):
                text = text.split("```", 2)[1]

            return json.loads(text)

        except Exception as e:
            last_error = e
            time.sleep(0.6)

    raise RuntimeError(
        f"All Gemini models failed. Last error: {last_error}"
    )

# -------------------------------------------------
# Audio narration (TTS)
# -------------------------------------------------
def generate_audio(text: str) -> str | None:
    try:
        tts = gTTS(text=text, lang="en", slow=False)

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3"
        ) as f:
            tts.save(f.name)
            return f.name

    except Exception:
        return None
