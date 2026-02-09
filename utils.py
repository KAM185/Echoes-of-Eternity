# utils.py

import os
import time
import json
import tempfile
from typing import Generator, Tuple, List

import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw
from gtts import gTTS


# =================================================
# Gemini model priority (Gemini 3 first)
# =================================================
GEMINI_MODELS: List[str] = [
    # 🔥 Gemini 3 (try first)
    "gemini-3.0-pro",
    "gemini-3.0-flash",
    "gemini-3.0-flash-lite",

    # Gemini 1.5
    "gemini-1.5-pro",
    "gemini-1.5-pro-002",
    "gemini-1.5-flash",
    "gemini-1.5-flash-002",

    # Gemini 1.0
    "gemini-1.0-pro-vision",
    "gemini-1.0-pro",
]


# =================================================
# Gemini initialization (cached)
# =================================================
@st.cache_resource
def init_gemini(model_name: str):
    """
    Initialize and cache a Gemini model.
    API key is read from environment variable.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found. "
            "Set it as an environment variable or Streamlit secret."
        )

    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


# =================================================
# Gemini image analysis with streaming + fallback
# =================================================
def generate_analysis_stream(
    image: Image.Image,
    prompt: str,
) -> Tuple[Generator[str, None, None], dict]:
    """
    Stream Gemini analysis text with multi-model fallback.
    Returns:
      - A generator yielding text chunks (Streamlit-safe)
      - A parsed JSON dict (empty if parsing fails)
    """

    accumulated_text = ""
    streamed_chunks: List[str] = []
    parsed: dict = {}
    last_error: Exception | None = None

    for model_name in GEMINI_MODELS:
        try:
            model = init_gemini(model_name)

            response = model.generate_content(
                [prompt, image],
                stream=True,
                generation_config={
                    "response_mime_type": "application/json"
                },
            )

            # Consume stream ONCE
            for chunk in response:
                text = getattr(chunk, "text", "")
                if isinstance(text, str) and text:
                    accumulated_text += text
                    streamed_chunks.append(text)

            # Attempt JSON parsing
            try:
                parsed = json.loads(accumulated_text)
            except json.JSONDecodeError:
                parsed = {}

            # Success — stop trying models
            break

        except Exception as e:
            last_error = e
            accumulated_text = ""
            streamed_chunks.clear()
            continue

    if not streamed_chunks:
        st.error("All Gemini models failed to generate a response.")
        if last_error:
            st.exception(last_error)

    # Replayable generator (Streamlit-safe)
    def stream_generator():
        for chunk in streamed_chunks:
            yield chunk

    return stream_generator(), parsed


# =================================================
# Draw damage overlay on image
# =================================================
def draw_damage_overlay(
    image: Image.Image,
    damaged_areas: list,
) -> Image.Image:
    """
    Draw semi-transparent red overlays for damaged areas.
    Expects bbox values normalized between 0–1.
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


# =================================================
# Text-to-Speech generation
# =================================================
def generate_audio(text: str) -> str:
    """
    Generate narration audio using gTTS.
    Returns path to a temporary mp3 file, or empty string on failure.
    """

    if not text or not text.strip():
        return ""

    try:
        tts = gTTS(text=text, lang="en")
        tmp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp3",
        )
        tts.save(tmp_file.name)
        return tmp_file.name
    except Exception:
        return ""

