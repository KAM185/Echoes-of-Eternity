import io
import json
from typing import List

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import google.generativeai as genai


# =================================================
# SYSTEM PROMPT
# =================================================
SYSTEM_PROMPT = """
You are a world-class architectural historian and monument recognition expert.

INSTRUCTIONS:
- Identify the monument shown in the image.
- If the monument is famous or widely recognizable, identify it confidently.
- Do NOT respond with "unknown" when there is strong visual evidence.
- Make a best-guess identification with a confidence score.
- The Taj Mahal in Agra, India MUST be identified correctly if visible.

OUTPUT:
Return VALID JSON ONLY. No markdown. No explanations.
"""


# =================================================
# GEMINI INITIALIZATION
# =================================================
def init_gemini(api_key: str) -> None:
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required.")
    genai.configure(api_key=api_key)


# =================================================
# MODEL DISCOVERY
# =================================================
def get_available_models() -> list[str]:
    models = genai.list_models()
    return [
        m.name.replace("models/", "")
        for m in models
        if "generateContent" in m.supported_generation_methods
    ]


def select_model() -> str:
    priority = [
        "gemini-3-pro",
        "gemini-3-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    available = get_available_models()

    for model in priority:
        if model in available:
            return model

    raise RuntimeError("No usable Gemini model available.")


# =================================================
# IMAGE ENHANCEMENT (DISPLAY ONLY)
# =================================================
def enhance_image_for_display(image: Image.Image) -> Image.Image:
    """
    Enhances the image ONLY for user viewing.
    This image must NOT be used for AI identification.
    """
    img = image.copy()

    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageEnhance.Brightness(img).enhance(1.05)
    img = ImageEnhance.Color(img).enhance(1.10)
    img = ImageEnhance.Sharpness(img).enhance(1.20)
    img = img.filter(ImageFilter.DETAIL)

    return img


# =================================================
# MONUMENT ANALYSIS (ORIGINAL IMAGE ONLY)
# =================================================
def analyze_monument(
    original_image_bytes: bytes,
    api_key: str,
) -> dict:
    """
    Uses the ORIGINAL uploaded image bytes for identification.
    Enhanced images must never be passed here.
    """
    init_gemini(api_key)

    try:
        image = Image.open(io.BytesIO(original_image_bytes)).convert("RGB")
    except Exception:
        return _fallback_response()

    try:
        model = genai.GenerativeModel(
            model_name=select_model(),
            system_instruction=SYSTEM_PROMPT,
        )

        response = model.generate_content(
            [
                image,
                "Identify the monument and return JSON exactly as specified."
            ],
            stream=False,
        )

        return json.loads(response.text)

    except Exception:
        return _fallback_response()


# =================================================
# DAMAGE OVERLAY (OPTIONAL)
# =================================================
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
        try:
            coords = [float(c.strip()) for c in region.split(",")]
            if len(coords) != 4:
                continue
        except Exception:
            continue

        x1 = int(coords[0] * width)
        y1 = int(coords[1] * height)
        x2 = int(coords[2] * width)
        y2 = int(coords[3] * height)

        draw.rectangle(
            [x1, y1, x2, y2],
            fill=(255, 0, 0, 90),
            outline=(255, 50, 50, 220),
            width=4,
        )

    return Image.alpha_composite(base, overlay)


# =================================================
# FALLBACK RESPONSE
# =================================================
def _fallback_response() -> dict:
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
            "summary": "unknown"
        },
        "visible_damage_assessment": [],
        "restoration_guidance": {
            "can_be_restored": "unknown",
            "recommended_methods": []
        }
    }

