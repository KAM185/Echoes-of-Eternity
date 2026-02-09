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
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found. Please set it in environment variables or Streamlit secrets."
        )

    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


# -------------------------------------------------
# List of available fallback models
# -------------------------------------------------
PRIMARY_MODELS = [
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-3-pro-image-preview",
]

SECONDARY_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-image",
]


# -------------------------------------------------
# Gemini analysis with streaming + multi-model fallback
# -------------------------------------------------
def generate_analysis_stream(
    image: Image.Image,
    prompt: str,
) -> Tuple[Generator[str, None, None], dict]:
    """
    Stream Gemini analysis text using multiple fallback models and return parsed JSON.
    """
    accumulated_text = ""

    def stream_generator() -> Generator[str, None, None]:
        nonlocal accumulated_text

        # Try all primary + secondary models in order
        for model_name in PRIMARY_MODELS + SECONDARY_MODELS:
            try:
                model = init_gemini(model_name)
                response = model.generate_content(
                    [prompt, image],
                    stream=True,
                    generation_config={"response_mime_type": "application/json"},
                )
                for chunk in response:
                    if hasattr(chunk, "text") and chunk.text:
                        accumulated_text += chunk.text
                        yield chunk.text
                # Success — stop trying other models
                return
            except Exception as e:
                st.warning(f"Model {model_name} failed. Trying next model…")

        # If all models fail
        raise RuntimeError("All Gemini models failed to generate a response.")

    # Run the generator once to completion
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
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(tmp_file.name)
        return tmp_file.name
    except Exception:
        return ""


