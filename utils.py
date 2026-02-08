import io
import time
import json
from PIL import Image
from openai import OpenAI  # Use OpenAI client pointed to Google API

# ------------------------
# Initialize Gemini models
# ------------------------

def init_gemini_models(api_key: str):
    """
    Returns a list of valid Gemini model names to try.
    You must replace GEMINI_API_KEY env var or pass via config.
    """
    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    # A set of reliable Gemini models based on current supported models
    models = [
        "gemini-3-pro-preview",           # high‑capacity multimodal model :contentReference[oaicite:2]{index=2}
        "gemini-3-flash-preview",         # balanced performance model :contentReference[oaicite:3]{index=3}
        "gemini-2.5-pro",                 # advanced reasoning model :contentReference[oaicite:4]{index=4}
        "gemini-2.5-flash",               # fast and smart model :contentReference[oaicite:5]{index=5}
        "gemini-2.5-flash-preview-09-2025",  # preview variant :contentReference[oaicite:6]{index=6}
        "gemini-2.0-flash",               # fallback older model :contentReference[oaicite:7]{index=7}
        "gemini-2.0-flash-lite",          # lightweight version :contentReference[oaicite:8]{index=8}
        "gemini-2.5-flash-lite"           # another cost‑efficient variant :contentReference[oaicite:9]{index=9}
    ]
    return client, models

# ------------------------
# Resize Image Utility
# ------------------------

def resize_image(image_bytes: bytes, max_dim: int = 1024) -> bytes:
    """
    Resizes the image to a max dimension (e.g., 1024x1024) to reduce
    API failure risk for large images.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image.thumbnail((max_dim, max_dim))
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()

# ------------------------
# Generate Analysis
# ------------------------

def generate_analysis(
    client,
    models: list[str],
    image_bytes: bytes,
    prompt: str,
    max_retries: int = 2
):
    """
    Tries multiple Gemini model names, retrying each on failure.
    Returns parsed JSON from the first successful model.
    """
    image_bytes = resize_image(image_bytes)

    for model_name in models:
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": "<image>"}
                    ],
                    modalities=["text", "image"],
                    image={"bytes": image_bytes}
                )

                raw = response.choices[0].message["content"]
                try:
                    return json.loads(raw)
                except Exception:
                    # Last‑ditch clean attempt to fix malformed JSON
                    cleaned = raw.strip().split("{", 1)[-1]
                    cleaned = "{" + cleaned
                    return json.loads(cleaned)
            except Exception as e:
                # Retry up to `max_retries`; break out only on last attempt
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    print(f"Model {model_name} failed: {e}")
                    break

    # If all models fail
    raise RuntimeError("All Gemini models failed after retries.")

# ------------------------
# Draw Damage Overlay
# ------------------------

def draw_damage_overlay(image: Image.Image, damages):
    overlay = image.copy()
    # Add drawing code if available
    return overlay

# ------------------------
# Chat with Monument
# ------------------------

def chat_with_monument(analysis, chat_history, question, chat_prompt):
    """
    Simple wrapper to ask follow‑up questions using any Gemini model.
    Can use the same ensemble logic or a specific chat model.
    """
    client, models = init_gemini_models(api_key="<YOUR_API_KEY_HERE>")
    prompt = chat_prompt + "\n" + question
    return generate_analysis(client, models, b"", prompt).get("reply", "No reply available.")
