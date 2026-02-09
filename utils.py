# utils.py
import io
import json
import time
from typing import Generator, List

import streamlit as st
from PIL import Image, ImageDraw
import google.generativeai as genai


# -------------------------------------------------
# INIT GEMINI
# -------------------------------------------------
@st.cache_resource
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in Streamlit secrets")
    genai.configure(api_key=api_key)


# -------------------------------------------------
# MODEL POOL (ORDER MATTERS)
# Gemini-3 FIRST (hackathon priority)
# Vision models LAST (guaranteed fallback)
# -------------------------------------------------
MODEL_POOL = [
    # Gemini 3 (experimental vision / reasoning)
    "gemini-3-pro-preview",
    "gemini-3-pro",
    "gemini-3-flash-preview",
    "gemini-3-flash",

    # Gemini 1.5 (strong reasoning)
    "gemini-1.5-pro",
    "gemini-1.5-flash",

    # Vision-guaranteed fallback (ALWAYS WORKS)
    "gemini-1.5-pro-vision",
    "gemini-1.5-flash-vision",
]


# -------------------------------------------------
# INTERNAL HELPERS
# -------------------------------------------------
def _run_model(model_name: str, image: Image.Image, prompt: str) -> str:
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=prompt,
    )

    response = model.generate_content(
        [image, prompt],
        stream=False,
    )

    if not response or not response.text:
        raise RuntimeError("Empty response")

    return response.text.strip()


def _looks_like_image_ignored(text: str) -> bool:
    """
    Detect cases where the model ignored the image
    and defaulted to unknown everywhere.
    """
    try:
        data = json.loads(text)
    except Exception:
        return True

    ident = data.get("monument_identification", {})
    name = ident.get("name", "").lower()
    score = float(ident.get("confidence_score", 0))

    if name in ("", "unknown") and score == 0:
        return True

    return False


# -------------------------------------------------
# MAIN ANALYSIS STREAM
# -------------------------------------------------
def generate_analysis_stream(
    image_bytes: bytes,
    system_prompt: str,
) -> Generator[str, None, None]:

    init_gemini()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    last_error = None

    for model_name in MODEL_POOL:
        try:
            text = _run_model(model_name, image, system_prompt)

            # Detect silent image failure
            if _looks_like_image_ignored(text):
                raise RuntimeError("Image ignored by model")

            yield text
            return  # SUCCESS

        except Exception as e:
            last_error = f"{model_name}: {e}"
            st.warning(f"{model_name} failed — trying next model")
            time.sleep(0.6)

    # -------------------------------------------------
    # HARD FALLBACK (should almost never happen)
    # -------------------------------------------------
    st.error("All Gemini models failed. Returning safe fallback.")

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
        "visible_damage_assessment": [
            {
                "damage_type": "none observed",
                "description": "no visible damage observed",
                "probable_cause": "n/a",
                "severity": "low",
                "approximate_image_region": ""
            }
        ],
        "documented_conservation_issues": [],
        "restoration_guidance": {
            "can_be_restored": "unknown",
            "recommended_methods": [],
            "preventive_measures": [
                "Routine visual inspections",
                "Environmental monitoring",
                "Visitor impact management"
            ]
        },
        "first_person_narrative": {
            "story_from_monument_perspective": "Time moves quietly around me."
        }
    }

    yield json.dumps(fallback)


# -------------------------------------------------
# DAMAGE OVERLAY
# -------------------------------------------------
def draw_damage_overlay(
    image: Image.Image,
    damages: List[dict]
) -> Image.Image:
    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = base.size

    for dmg in damages:
        region = dmg.get("approximate_image_region", "")
        coords = None

        if isinstance(region, list) and len(region) == 4:
            coords = region
        elif isinstance(region, str) and "," in region:
            try:
                coords = [float(x.strip()) for x in region.split(",")]
            except Exception:
                coords = None

        if coords and len(coords) == 4:
            x1 = int(coords[0] * width)
            y1 = int(coords[1] * height)
            x2 = int(coords[2] * width)
            y2 = int(coords[3] * height)

            draw.rectangle(
                [x1, y1, x2, y2],
                fill=(255, 0, 0, 90),
                outline=(255, 80, 80, 220),
                width=4
            )

    return Image.alpha_composite(base, overlay)

