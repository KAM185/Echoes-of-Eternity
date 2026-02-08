import os
import json
import time
import tempfile
from typing import List
from PIL import Image, ImageDraw, ImageEnhance
import google.generativeai as genai
from gtts import gTTS
import streamlit as st

MODEL_POOL = [
    "gemini-3-pro-preview",
    "gemini-3-pro-vision-preview",
    "gemini-3.0-pro",
    "gemini-3-flash-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
]


@st.cache_resource
def init_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment.")
    genai.configure(api_key=api_key)


def safe_json_extract(text: str) -> dict:
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {}


def generate_analysis(image: Image.Image, prompt: str) -> dict:
    last_error = None
    for model_name in MODEL_POOL:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                [prompt, image],
                generation_config={"response_mime_type": "application/json"},
            )
            data = safe_json_extract(response.text)
            if data:
                return data
        except Exception as e:
            last_error = str(e)
            time.sleep(1)
    return {
        "error": "analysis_failed",
        "details": last_error or "unknown"
    }


def draw_damage_overlay(image: Image.Image, areas: List[dict]) -> Image.Image:
    overlay = image.convert("RGBA")
    draw = ImageDraw.Draw(overlay, "RGBA")
    for area in areas:
        region = area.get("approximate_image_region", "")
        if isinstance(region, list) and len(region) == 4:
            w, h = image.size
            box = [
                int(region[0] * w),
                int(region[1] * h),
                int(region[2] * w),
                int(region[3] * h),
            ]
            draw.rectangle(box, fill=(255, 0, 0, 90))
    return overlay


def generate_audio(text: str):
    try:
        tts = gTTS(text)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(tmp.name)
        return tmp.name
    except Exception:
        return None

