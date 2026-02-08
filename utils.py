import io
import time
import json
from PIL import Image
from openai import OpenAI

# ---------------- Initialize 8 Gemini models ----------------
def init_gemini_models(api_key: str):
    """
    Returns OpenAI client and list of 8 Gemini models.
    """
    client = OpenAI(api_key=api_key)
    models = [
        "gemini-3-pro-preview",
        "gemini-3-flash-preview",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-preview-09-2025",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash-lite"
    ]
    return client, models

# ---------------- Resize Image ----------------
def resize_image(image_bytes: bytes, max_dim: int = 1024) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image.thumbnail((max_dim, max_dim))
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()

# ---------------- Generate Analysis ----------------
def generate_analysis(client, models, image_bytes: bytes, prompt: str, max_retries: int = 2):
    image_bytes = resize_image(image_bytes)
    last_exception = None

    for model_name in models:
        for attempt in range(max_retries):
            try:
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": "<image>"}
                    ],
                    modalities=["text", "image"],
                    image={"bytes": image_bytes}
                )
                raw = resp.choices[0].message["content"]
                try:
                    return json.loads(raw)
                except Exception:
                    cleaned = raw.strip().split("{", 1)[-1]
                    cleaned = "{" + cleaned
                    return json.loads(cleaned)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                print(f"Model {model_name} attempt {attempt+1} failed: {e}")
                break

    raise RuntimeError(f"All Gemini models failed after retries. Last error: {last_exception}")

# ---------------- Draw Damage Overlay ----------------
def draw_damage_overlay(image: Image.Image, damages):
    overlay = image.copy()
    # Add drawing code if needed
    return overlay

# ---------------- Chat With Monument ----------------
def chat_with_monument(analysis, chat_history, question, chat_prompt):
    # For simplicity, reuse Gemini ensemble for chat
    client, models = init_gemini_models("<YOUR_API_KEY_HERE>")
    prompt = chat_prompt + "\n" + question
    result = generate_analysis(client, models, b"", prompt)
    return result.get("reply", "The monument remains silent.")
