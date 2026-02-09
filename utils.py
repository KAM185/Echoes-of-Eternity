import io
import json
from typing import List

import streamlit as st
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import google.generativeai as genai


# =================================================
# STREAMLIT PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="Monument Identifier",
    page_icon="🏛️",
    layout="wide",
)


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

JSON FORMAT:
{
  "monument_identification": {
    "name": "",
    "confidence_score": 0.0,
    "city": "",
    "country": "",
    "coordinates": ""
  },
  "architectural_analysis": {
    "style": "",
    "period_or_dynasty": "",
    "primary_materials": [],
    "distinct_features_visible": []
  },
  "historical_facts": {
    "summary": ""
  },
  "visible_damage_assessment": [
    {
      "damage_type": "",
      "description": "",
      "severity": "low | medium | high",
      "approximate_image_region": ""
    }
  ],
  "restoration_guidance": {
    "can_be_restored": "yes | no | unknown",
    "recommended_methods": []
  }
}
"""


# =================================================
# GEMINI INITIALIZATION
# =================================================
@st.cache_resource
def init_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found. "
            "Add it to .streamlit/secrets.toml"
        )
    genai.configure(api_key=api_key)


# =================================================
# MODEL DISCOVERY
# =================================================
@st.cache_resource
def get_available_models() -> list[str]:
    init_gemini()
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
    Enhances image ONLY for user viewing.
    NOT used for AI identification.
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
def analyze_monument(original_image_bytes: bytes) -> dict:
    try:
        original_image = Image.open(
            io.BytesIO(original_image_bytes)
        ).convert("RGB")
    except Exception as e:
        st.error(f"Invalid image: {e}")
        return {}

    model_name = select_model()

    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
        )

        response = model.generate_content(
            [
                original_image,
                "Identify the monument and return JSON exactly as specified."
            ],
            stream=False,
        )

        return json.loads(response.text)

    except Exception as e:
        st.error(f"AI analysis failed: {e}")

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
        "historical_facts": {"summary": "unknown"},
        "visible_damage_assessment": [],
        "restoration_guidance": {
            "can_be_restored": "unknown",
            "recommended_methods": []
        }
    }


# =================================================
# UI
# =================================================
st.title("🏛️ Monument Identification & Analysis")
st.write(
    "Upload a photo of a monument. "
    "The image will be enhanced for viewing, "
    "but the original image is used for AI analysis."
)

uploaded_file = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file:
    original_bytes = uploaded_file.read()
    original_image = Image.open(
        io.BytesIO(original_bytes)
    ).convert("RGB")

    enhanced_image = enhance_image_for_display(original_image)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Original Image")
        st.image(original_image, use_container_width=True)

    with col2:
        st.subheader("Enhanced View (Display Only)")
        st.image(enhanced_image, use_container_width=True)

    if st.button("🔍 Analyze Monument"):
        with st.spinner("Analyzing monument..."):
            result = analyze_monument(original_bytes)

        st.subheader("📄 Analysis Result")
        st.json(result)

else:
    st.info("Please upload a monument image to begin.")

