import io
import json
from typing import List

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import google.generativeai as genai

from prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT


# =================================================
# GEMINI INIT
# =================================================
def init_gemini(api_key: str) -> None:
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY missing")
    genai.configure(api_key=api_key)


# =================================================
# MODEL SELECTION (Gemini 3 first)
# =================================================
def select_model() -> str:
    priority = [
        "gemini-3-pro",
        "gemini-3-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    available = [
        m.name.replace("models/", "")
        for m in genai.list_models()
        if "generateContent" in m.supported_generation_methods
    ]

    for model in priority:
        if model in available:
            return model

    raise RuntimeError("No supported Gemini model available")


# =================================================
# ANALYSIS (ORIGINAL IMAGE ONLY)
# =================================================
def analyze_monument(image_bytes: bytes, api_key: str) -> dict:
    init_gemini(api_key)

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return _fallback()

    try:
        model = genai.GenerativeModel(
            model_name=select_model(),
            system_instruction=SYSTEM_PROMPT,
        )

        response = model.generate_content(
            [image, ANALYSIS_PROMPT],
            stream=False,
        )

        return json.loads(response.text)

    except Exception:
        return _fallback()


# =================================================
# DISPLAY-ONLY IMAGE ENHANCEMENT
# =================================================
def enhance_image_for_display(image: Image.Image) -> Image.Image:
    img = image.copy()

    img = ImageEnhance.Contrast(img).enhance(1.10)
    img = ImageEnhance.Brightness(img).enhance(1.03)
    img = ImageEnhance.Color(img).enhance(1.08)
    img = ImageEnhance.Sharpness(img).enhance(1.15)
    img = img.filter(ImageFilter.DETAIL)

    return img


# =================================================
# DAMAGE OVERLAY
# =================================================
def draw_damage_overlay(image: Image.Image, damages: List[dict]) -> Image.Image:
    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    w, h = base.size

    for dmg in damages:
        region = dmg.get("approximate_image_region", "")
        try:
            x1, y1, x2, y2 = [float(c) for c in region.split(",")]
        except Exception:
            continue

        draw.rectangle(
            [x1 * w, y1 * h, x2 * w, y2 * h],
            fill=(255, 0, 0, 90),
            outline=(255, 50, 50, 220),
            width=4,
        )

    return Image.alpha_composite(base, overlay)


# =================================================
# FALLBACK
# =================================================
def _fallback() -> dict:
    return {
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
                "damage_type": "no visible damage observed",
                "description": "No visible damage observed",
                "probable_cause": "n/a",
                "severity": "low",
                "approximate_image_region": ""
            }
        ],
        "documented_conservation_issues": [],
        "restoration_guidance": {
            "can_be_restored": "unknown",
            "recommended_methods": [],
            "preventive_measures": []
        },
        "first_person_narrative": {
            "story_from_monument_perspective": ""
        }
    }


