import os
import time
import json
import tempfile
from typing import Generator, Tuple

import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw
from gtts import gTTS


# -------------------------------------------------
# Gemini model initialization (cached)
# -------------------------------------------------
@st.cache_resource
def init_gemini(model_name: str):
    """
    Initialize and cache a Gemini model.
    API key is read securely from environment variable.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found. Please set it in environment variables or Streamlit secrets."
        )

    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


# -------------------------------------------------
# Gemini image analysis with streaming + fallback
# -------------------------------------------------
def generate_analysis_stream(
    image: Image.Image,
    prompt: str,
    primary_model: str,
    fallback_model: str,
) -> Tuple[Generator[str, None, None], dict]:
    """
    Stream Gemini analysis text and return parsed JSON result.
    """
    accumulated_text = ""

    def stream_generator():
        nonlocal accumulated_text

        try:
            model = init_gemini(primary_model)
            response = model.generate_content(
                [prompt, image],
                stream=True,
                generation_config={
                    "response_mime_type": "application/json"
                },
            )
        except Exception:
            st.warning("Primary model unavailable. Falling back to faster model…")
            model = init_gemini(fallback_model)
            response = model.generate_content(
                [prompt, image],
                stream=True,
                generation_config={
                    "response_mime_type": "application/json"
                },
            )

        for chunk in response:
            if hasattr(chunk, "text") and chunk.text:
                accumulated_text += chunk.text
                yield chunk.text

    # Run stream once to completion
    for _ in stream_generator():
        pass

    # Attempt JSON parsing with retries
    parsed = {}
    for attempt in range(3):
        try:
            parsed = json.loads(accumulated_text)
            break
        except json.JSONDecodeError:
            time.sleep(0.6)

    return stream_generator(), parsed


# -------------------------------------------------
# Draw damage overlay on image
# -------------------------------------------------
def draw_damage_overlay(
    image: Image.Image,
    damaged_areas: list,
) -> Image.Image:
    """
    Draw semi-transparent overlays for damaged areas.
    """
    if not damaged_areas:
        return image

    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (255, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = base.size

    for area in damaged_areas:
        bbox = area.get("bbox")
        if not bbox or len(bbox) != 4:
            continue

        x1, y1, x2, y2 = bbox
        rect = [
            int(x1 * width),
            int(y1 * height),
            int(x2 * width),
            int(y2 * height),
        ]

        draw.rectangle(
            rect,
            outline=(255, 0, 0, 200),
            fill=(255, 0, 0, 80),
        )

    return Image.alpha_composite(base, overlay)


# -------------------------------------------------
# Text-to-Speech generation
# -------------------------------------------------
def generate_audio(text: str) -> str:
    """
    Generate narration audio using gTTS.
    Returns path to temporary mp3 file, or empty string on failure.
    """
    if not text.strip():
        return ""

    try:
        tts = gTTS(text=text, lang="en")
        tmp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=".mp3"
        )
        tts.save(tmp_file.name)
        return tmp_file.name
    except Exception:
        return ""
