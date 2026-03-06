# MindMate-AI
# 🧠 MindMate AI v2 — Intelligent Mental Wellness Assistant

> Hackathon-ready AI mental wellness app for students. Detects stress, provides empathetic support, tracks mood trends, and offers 4 interactive stress-relief activities.

---
## what's in it
| Feature | v2 Details |
|---|---|
| 🎨 **Mandala Art Therapy** | Interactive HTML5 Canvas color-filling with custom color picker |
| 🎯 **Bottle Shooting Game** | Easy & Medium levels, particle effects, zigzag bottles |
| 🎤 **Voice (Browser API)** | Works in Chrome/Edge — no PyAudio installation needed |
| 🎨 **New UI Theme** | Purple/violet palette with Playfair Display + Outfit fonts |

---

## 🚀 Quick Start

```bash
# 1. Unzip and enter folder
unzip mindmate_ai_v2.zip && cd mindmate_v2

# 2. Install dependencies (< 1 minute)
pip install -r requirements.txt

# 3. Run!
streamlit run app.py
# Opens at http://localhost:8501
```

**Optional:** Paste your Anthropic API key in the sidebar for Claude-powered responses. Without it, a rich rule-based fallback handles everything — fully functional for demos.

---

## 📁 Folder Structure

```
mindmate_v2/
├── app.py                        ← Main Streamlit app (8 pages)
├── requirements.txt
├── .streamlit/config.toml        ← Dark violet theme
├── modules/
│   ├── emotion_detector.py       ← VADER + TextBlob NLP
│   ├── ai_chat.py                ← Anthropic API + fallback
│   ├── mood_tracker.py           ← Plotly charts + wellness score
│   ├── multilingual.py           ← EN/HI/GU detection + translation
│   ├── voice_input.py            ← Browser Web Speech API
│   ├── emergency.py              ← Crisis detection + helplines
│   └── games.py                  ← 4 mini-games (Breathing, Memory, Mandala, Shooting)
└── data/
    └── mood_log.json             ← Auto-created mood history
```

---

## 🎮 Games Guide

### 🌬️ Breathing Exercise
- Science: 4-7-8 technique activates parasympathetic nervous system
- Choose 1–5 rounds; animated countdown guides each phase

### 🧠 Memory Match  
- 4×4 emoji grid; find all 8 pairs
- Trains focus and provides cognitive distraction from stress

### 🎨 Mandala Art Therapy
- Interactive HTML5 Canvas with 65+ colorable sections
- Pick any color with the color picker; save your art as PNG
- Science: reduces cortisol as effectively as mindfulness meditation

### 🎯 Bottle Shooting
- **Easy Mode:** Slower bottles, 60s timer — gentle decompression
- **Medium Mode:** Fast + zigzag bottles, 45s timer — sharp focus training
- Particle explosion effects on hit; grade at end of round

---

## 🏆 2-Minute Hackathon Demo Flow

| Time | Action |
|---|---|
| 0:00–0:15 | Dashboard → wellness score + chart |
| 0:15–0:45 | AI Chat → type "I feel stressed about exams" → show emotion badge + response |
| 0:45–1:05 | Voice → speak a message → transcript + AI reply |
| 1:05–1:25 | Games → Mandala (color 3 sections) → switch to Bottle Shooting (Easy, 15s) |
| 1:25–1:45 | Mood Tracker → show trend chart |
| 1:45–2:00 | Emergency Help → highlight helplines |

---

## 📱 Mobile Conversion

Deploy to **Streamlit Community Cloud** (free), then wrap in Android WebView:

```kotlin
webView.settings.javaScriptEnabled = true
webView.loadUrl("https://your-app.streamlit.app")
```

---

## 🛠 Troubleshooting

| Issue | Fix |
|---|---|
| Voice not working | Use Chrome or Edge; allow mic in browser permissions |
| Translation fails | `pip install deep-translator langdetect` |
| Slow first start | Normal — TextBlob downloads NLTK data once |
| Games not rendering | Ensure JavaScript is enabled in browser |

---

*Built with ❤️ for student mental health awareness. Designed to win hackathons.*
