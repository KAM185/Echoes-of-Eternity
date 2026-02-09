import os
import time
import json
import tempfile
from typing import Generator, Tuple
import threading

import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS

# -------------------------
# Gemini initialization
# -------------------------
@st.cache_resource
def init_gemini(model_name: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

# -------------------------
# Models fallback list
# -------------------------
PRIMARY_MODELS = [
    "gemma-3-27b-it",
    "gemma-3-12b-it",
    "gemma-3-4b-it",
    "gemma-3-1b-it",
]

SECONDARY_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-image",
]

ALL_MODELS = PRIMARY_MODELS + SECONDARY_MODELS

# -------------------------
# Safe JSON parsing
# -------------------------
def parse_json_safe(text: str, retries: int = 3) -> dict:
    parsed = {}
    for _ in range(retries):
        try:
            parsed = json.loads(text)
            break
        except json.JSONDecodeError:
            time.sleep(0.5)
    return parsed

# -------------------------
# Gemini analysis with fallback (silent)
# -------------------------
def generate_analysis_stream(image: Image.Image, prompt: str, timeout: int = 25) -> Tuple[Generator[str, None, None], dict]:
    accumulated_text = ""

    # Resize image
    max_size = (1024, 1024)
    if image.width > max_size[0] or image.height > max_size[1]:
        image = image.copy()
        image.thumbnail(max_size)

    def try_model(model_name: str, output_list: list):
        try:
            model = init_gemini(model_name)
            response = model.generate_content(
                [prompt, image],
                stream=True,
                generation_config={"response_mime_type": "application/json"},
            )
            for chunk in response:
                if hasattr(chunk, "text") and chunk.text:
                    output_list.append(chunk.text)
        except Exception:
            output_list.append(None)  # silently fail

    for model_name in ALL_MODELS:
        chunks = []
        thread = threading.Thread(target=try_model, args=(model_name, chunks))
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive() or not any(chunks):
            continue  # silent fallback

        def chunk_generator():
            nonlocal accumulated_text
            for c in chunks:
                accumulated_text += c
                yield c

        # Run once to fill accumulated_text
        for _ in chunk_generator():
            pass

        return chunk_generator(), parse_json_safe(accumulated_text)

    raise RuntimeError("All models failed or timed out.")

# -------------------------
# Draw damage overlay with labels
# -------------------------
def draw_damage_overlay(image: Image.Image, damaged_areas: list) -> Image.Image:
    if not damaged_areas:
        return image

    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    width, height = base.size

    # Optional: load default font
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()

    for area in damaged_areas:
        bbox = area.get("bbox")
        damage_type = area.get("type", "damage")
        if not bbox or len(bbox) != 4:
            continue
        x1, y1, x2, y2 = [int(v * w) for v, w in zip(bbox, [width, height, width, height])]
        # Draw semi-transparent rectangle
        draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0, 220), fill=(255, 0, 0, 80))
        # Draw damage type label
        draw.text((x1 + 5, y1 + 5), damage_type, fill=(255, 255, 255, 255), font=font)

    return Image.alpha_composite(base, overlay)

# -------------------------
# Text-to-Speech
# -------------------------
def generate_audio(text: str) -> str:
    if not text.strip():
        return ""
    try:
        tts = gTTS(text=text, lang="en")
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(tmp_file.name)
        return tmp_file.name
    except Exception:
        return ""

