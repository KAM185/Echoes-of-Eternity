# 🌌 Echoes of Eternity

**When ancient stones finally speak.**

An emotional AI-powered cultural heritage experience that lets monuments tell their own stories.

Upload a photo of any historical site, temple, statue or ruin → watch **Gemini 3** bring it to life:

- Deep multimodal visual analysis  
- Damage detection + preservation overlay  
- First-person poetic narration as if the monument is speaking  
- Voice narration (natural TTS + browser fallback)  
- Live conversation with the monument itself  

https://github.com/YOUR_USERNAME/echoes-of-eternity

![Hero preview](https://via.placeholder.com/800x400/1a1a1a/ffffff?text=Echoes+of+Eternity+—+Ancient+Stones+Speak)  
*(Replace this placeholder with a real screenshot after deployment)*

## ✨ Why It Matters

In a world racing forward, we risk forgetting the voices of the past.  
Echoes of Eternity uses cutting-edge AI to **listen** — and lets heritage speak again.

Perfect blend of:
- Multimodal Gemini 3 reasoning & vision  
- Emotional storytelling  
- Heritage preservation awareness  
- Accessible, mobile-friendly design

## 🔥 Key Features

| Feature                        | Description                                                                 |
|--------------------------------|-----------------------------------------------------------------------------|
| 📸 Photo Upload                | Drag & drop or camera (mobile friendly)                                     |
| 🪨 Awaken the Echo             | Streams structured analysis + emotional first-person story                  |
| 🩹 Damage Overlay              | Semi-transparent red highlights on cracked/eroded areas                     |
| 🎙️ Narration                   | gTTS audio + Web Speech Synthesis fallback                                  |
| 💬 Ask the Echo                | Real-time chat — talk directly to the monument                              |
| 🌙 Dark & Elegant Design       | Stone-inspired gradient, serif fonts, high contrast                         |
| 🔄 Graceful Fallbacks          | Model fallback, retry logic, error messages, rate-limit handling            |

## 🛠️ Tech Stack

- **Frontend** — Streamlit 1.40+  
- **AI** — Google Gemini 3 (pro-preview → flash-preview fallback)  
- **Vision & JSON** — Multimodal + structured output  
- **Image Processing** — Pillow (damage overlays)  
- **Voice** — gTTS + browser SpeechSynthesis  
- **Deployment** — Streamlit Cloud (zero-config secrets for API key)

## 🚀 Quick Start (Local)

```bash
# 1. Clone (or download ZIP)
git clone https://github.com/YOUR_USERNAME/echoes-of-eternity.git
cd echoes-of-eternity

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Gemini API key
export GEMINI_API_KEY="your-key-here"     # Mac/Linux
# or on Windows: set GEMINI_API_KEY=your-key-here

# 4. Run
streamlit run app.py
