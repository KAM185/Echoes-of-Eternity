# utils.py
import io
import json
import time
from typing import Generator, List

import streamlit as st
from PIL import Image, ImageDraw
import google.generativeai as genai


@st.cache_resource
def init_gemini():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])


MODEL_POOL = [
    "gemini-3-pro-preview",
    "gemini-3-flash-preview",
    "gemini-3-pro",
    "gemini-3-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-pro-vision",
    "gemini-1.5-flash-vision",
]


def _run(model_name, image, prompt):
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=prompt,
    )
    res = model.generate_content([image, prompt])
    if not res or not res.text:
        raise RuntimeError("Empty response")
    return res.text


def _failed(text):
    try:
        j = json.loads(text)
        i = j["monument_identification"]
        return i["name"] == "unknown" and i["confidence_score"] == 0
    except Exception:
        return True


def generate_analysis_stream(image_bytes: bytes, system_prompt: str) -> Generator[str, None, None]:
    init_gemini()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    for model in MODEL_POOL:
        try:
            text = _run(model, image, system_prompt)
            if _failed(text):
                raise RuntimeError("Image ignored")
            yield text
            return
        except Exception:
            time.sleep(0.5)

    yield json.dumps({
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
            "preventive_measures": ["Routine inspection"]
        },
        "first_person_narrative": {
            "story_from_monument_perspective": "Time rests quietly upon me."
        }
    })


def draw_damage_overlay(image: Image.Image, damages: List[dict]) -> Image.Image:
    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    w, h = base.size
    for d in damages:
        r = d.get("approximate_image_region", "")
        if "," in r:
            x1, y1, x2, y2 = [float(v) for v in r.split(",")]
            draw.rectangle(
                [x1*w, y1*h, x2*w, y2*h],
                fill=(255, 0, 0, 90),
                outline=(255, 60, 60, 200),
                width=4
            )

    return Image.alpha_composite(base, overlay)



