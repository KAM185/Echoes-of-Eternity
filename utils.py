import io
import json
import time
from typing import Generator, List

import streamlit as st
from PIL import Image, ImageDraw
import google.generativeai as genai


# =================================================
# Gemini Initialization
# =================================================
@st.cache_resource
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found in Streamlit secrets. "
            "Add it to .streamlit/secrets.toml"
        )
    genai.configure(api_key=api_key)


# =================================================
# Discover models ACTUALLY available to this API key
# =================================================
@st.cache_resource
def get_available_models() -> list[str]:
    """
    Lists all models that support generateContent.
    Prevents calling non-existent or disabled models.
    """
    init_gemini()
    models = genai.list_models()

    available = []
    for m in models:
        if "generateContent" in m.supported_generation_methods:
            available.append(m.name.replace("models/", ""))

    return available


# =================================================
# Model selection (Gemini 3 first, safe fallback)
# =================================================
def select_models_by_priority() -> list[str]:
    """
    Prefer Gemini 3 if enabled.
    Fall back cleanly to Gemini 1.5.
    """
    available = get_available_models()

    priority_order = [
        # Gemini 3 (only if your project has access)
        "gemini-3-pro",
        "gemini-3-flash",

        # Stable & widely available
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    selected = [m for m in priority_order if m in available]

    # Absolute safety net
    if not selected:
        selected = available

    return selected


# =================================================
# Streaming analysis generator
# =================================================
def generate_analysis_stream(
    image_bytes: bytes,
    system_prompt: str,
) -> Generator[str, None, None]:
    """
    Streams analysis text from the best available Gemini model.
    Handles quota errors, unsupported models, and failures safely.
    """

    # ---- Image validation ----
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        st.error(f"Invalid image file: {e}")
        return

    models_to_try = select_models_by_priority()

    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
            )

            response = model.generate_content(
                [image, "Analyze this monument image and return JSON as specified."],
                stream=True,
            )

            for chunk in response:
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text

            return  # ✅ SUCCESS

        except Exception as e:
            error = str(e).lower()

            # Quota / billing errors → stop retrying
            if "quota" in error or "429" in error:
                st.error(
                    f"Quota exceeded for {model_name}. "
                    "Enable billing or use a different project."
                )
                break

            # Unsupported model → try next
            st.warning(f"Model {model_name} failed. Trying next...")
            time.sleep(0.5)

    # =================================================
    # Fallback JSON (guaranteed valid output)
    # =================================================
    st.error("All AI models failed. Using fallback analysis.")

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
                "Regular monitoring",
                "Environmental protection"
            ]
        },
        "first_person_narrative": {
            "story_from_monument_perspective": "I stand quietly, waiting to be understood."
        }
    }

    yield json.dumps(fallback, indent=2)


# =================================================
# Damage overlay drawing
# =================================================
def draw_damage_overlay(
    image: Image.Image,
    damages: List[dict]
) -> Image.Image:
    """
    Draws semi-transparent red overlays for damage regions.
    Accepts normalized [x1,y1,x2,y2] or 'x1,y1,x2,y2'.
    """

    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = base.size

    for dmg in damages:
        region = dmg.get("approximate_image_region", "")
        coords = None

        if isinstance(region, list) and len(region) == 4:
            coords = region

        elif isinstance(region, str):
            try:
                coords = [float(c.strip()) for c in region.split(",")]
                if len(coords) != 4:
                    coords = None
            except Exception:
                coords = None

        if coords:
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

