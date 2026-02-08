import os
import time
import json
from typing import List, Dict

import google.generativeai as genai
from PIL import Image, ImageDraw
import streamlit as st

# -------------------------------------------------
# GEMINI CONFIG
# -------------------------------------------------
@st.cache_resource
def init_gemini_model():
    """
    Initialize Gemini 3 with multiple safe fallbacks.
    Gemini 3 is mandatory (hackathon rule).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment.")

    genai.configure(api_key=api_key)

    # Ordered by preference
    model_names = [
        "gemini-3-pro-preview",
        "gemini-3-pro-vision-preview",
        "gemini-3-flash-preview",
        "gemini-3-flash-vision-preview",
        "gemini-3-pro"
    ]

    last_error = None
    for name in model_names:
        try:
            return genai.GenerativeModel(name)
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Failed to initialize Gemini models: {last_error}")


# -------------------------------------------------
# IMAGE ANALYSIS
# -------------------------------------------------
def generate_analysis(model, image_bytes: bytes, prompt: str) -> str:
    """
    Sends image + prompt to Gemini and returns raw JSON text.
    Includes retry + backoff.
    """
    image = Image.open(io := bytes_to_image(image_bytes))

    for attempt in range(3):
        try:
            response = model.generate_content(
                [prompt, image],
                generation_config={
                    "temperature": 0.3,
                    "response_mime_type": "application/json",
                }
            )
            return response.text.strip()

        except Exception:
            time.sleep(2 ** attempt)

    raise RuntimeError("Gemini analysis failed after retries.")


def bytes_to_image(image_bytes: bytes):
    from io import BytesIO
    return BytesIO(image_bytes)


# -------------------------------------------------
# DAMAGE OVERLAY DRAWING
# -------------------------------------------------
def draw_damage_overlay(
    base_image: Image.Image,
    damages: List[Dict]
) -> Image.Image:
    """
    Draws semi-transparent red overlays for damaged regions.
    Uses approximate regions (text-based) safely.
    """
    img = base_image.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = img.size

    for d in damages:
        region = d.get("approximate_image_region", "").lower()

        # Very conservative region mapping (no hallucinated bounding boxes)
        if "left" in region:
            box = (0, 0, width * 0.3, height)
        elif "right" in region:
            box = (width * 0.7, 0, width, height)
        elif "upper" in region or "top" in region:
            box = (0, 0, width, height * 0.3)
        elif "lower" in region or "bottom" in region:
            box = (0, height * 0.7, width, height)
        else:
            continue

        draw.rectangle(
            box,
            fill=(255, 0, 0, 90),
            outline=(255, 80, 80, 160),
            width=3,
        )

    return Image.alpha_composite(img, overlay)


# -------------------------------------------------
# ASK THE ECHO (CHAT)
# -------------------------------------------------
def chat_with_monument(
    analysis: Dict,
    chat_history: List[Dict],
    user_question: str,
    system_prompt: str,
) -> str:
    """
    Chat with the monument using Gemini 3.
    Injects analysis context + preserves memory.
    """
    model = init_gemini_model()

    # Build context summary for the model
    context = {
        "name": analysis["monument_identification"]["name"],
        "location": f"{analysis['monument_identification']['city']}, {analysis['monument_identification']['country']}",
        "architecture": analysis["architectural_analysis"],
        "history": analysis["historical_facts"]["summary"],
        "condition": analysis["visible_damage_assessment"],
    }

    messages = [
        {"role": "user", "parts": [system_prompt]},
        {"role": "user", "parts": [f"Context about you:\n{json.dumps(context, indent=2)}"]},
    ]

    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        messages.append({"role": role, "parts": [msg["content"]]})

    messages.append({"role": "user", "parts": [user_question]})

    try:
        response = model.generate_content(messages, generation_config={"temperature": 0.4})
        return response.text.strip()
    except Exception:
        return "My voice fades for a moment… ask me again."
