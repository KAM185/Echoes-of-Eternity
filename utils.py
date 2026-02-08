import os
import io
import time
import json
from typing import Generator, List

import streamlit as st
from PIL import Image, ImageDraw

import google.generativeai as genai


# -------------------------------------------------
# Gemini initialization 
# -------------------------------------------------
@st.cache_resource
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in Streamlit secrets")
    genai.configure(api_key=api_key)


# -------------------------------------------------
# Gemini 3 model pool 
# -------------------------------------------------
GEMINI_3_MODELS = [
    "gemini-3-pro-preview",
    "gemini-3-pro-vision-preview",
    "gemini-3.0-pro",
    "gemini-3-flash-preview",
    "gemini-3-flash-vision-preview",
]


# -------------------------------------------------
# Streaming analysis generator
# -------------------------------------------------
def generate_analysis_stream(
    image_bytes: bytes,
    system_prompt: str,
) -> Generator[str, None, None]:
    """
    Streams analysis text from Gemini 3 models.
    Falls back safely across Gemini 3 variants.
    Never crashes the app.
    """

    init_gemini()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    last_error = None

    for model_name in GEMINI_3_MODELS:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )

            response = model.generate_content(
                [image, system_prompt],
                stream=True
            )

            for chunk in response:
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text

            return  # SUCCESS — stop trying models

        except Exception as e:
            last_error = f"{model_name}: {str(e)}"
            time.sleep(1)

    # If all models fail, yield a valid JSON fallback
    fallback = {
        "monument_identification": {
            "name": "unknown",
            "confidence_score": 0.0,
            "city": "unknown",
            "country": "unknown",
            "coordinates": "unknown"
        },
        "architectural_analysis": {
            "style": "unknown",
            "period_or_dynasty": "unknown",
            "primary_materials": [],
            "distinct_features_visible": []
        },
        "historical_facts": {
            "summary": "unknown",
            "timeline": [],
            "mysteries_or_lesser_known_facts": []
        },
        "visible_damage_assessment": [],
        "documented_conservation_issues": [],
        "restoration_guidance": {
            "can_be_restored": "unknown",
            "recommended_methods": [],
            "preventive_measures": []
        },
        "first_person_narrative": {
            "story_from_monument_perspective": "The echoes are faint today."
        }
    }

    yield json.dumps(fallback)


# -------------------------------------------------
# Damage overlay drawing (clearly visible)
# -------------------------------------------------
def draw_damage_overlay(
    image: Image.Image,
    damages: List[dict]
) -> Image.Image:
    """
    Draws semi-transparent red boxes over damaged areas.
    Expects normalized [x1,y1,x2,y2] coordinates.
    """

    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = base.size

    for dmg in damages:
        region = dmg.get("approximate_image_region")

        if isinstance(region, list) and len(region) == 4:
            x1 = int(region[0] * width)
            y1 = int(region[1] * height)
            x2 = int(region[2] * width)
            y2 = int(region[3] * height)

            draw.rectangle(
                [x1, y1, x2, y2],
                fill=(255, 0, 0, 90),
                outline=(255, 60, 60, 220),
                width=4
            )

    return Image.alpha_composite(base, overlay)

