"""
modules/voice_input.py
─────────────────────────────────────────────────────────────────────────────
Full conversational voice assistant using:
  • Web Speech API (SpeechRecognition)  → mic → text
  • Anthropic API (via fetch inside JS)  → text → AI response text
  • Web Speech Synthesis API (TTS)       → text → spoken voice

The entire listen → think → speak loop runs inside the browser component.
Supports English (en-IN), Hindi (hi-IN), Gujarati (gu-IN).
Works in Chrome / Edge without any Python audio dependencies.
─────────────────────────────────────────────────────────────────────────────
"""
import streamlit.components.v1 as components

LANG_CODES   = {"en": "en-IN", "hi": "hi-IN", "gu": "gu-IN"}
LANG_NAMES   = {"en": "English", "hi": "Hindi", "gu": "Gujarati"}

# Friendly opening lines MindMate says when the page loads (per language)
GREETINGS = {
    "en": "Hi! I'm MindMate. How are you feeling today? Tell me anything — I'm here for you.",
    "hi": "नमस्ते! मैं MindMate हूँ। आज आप कैसा महसूस कर रहे हैं? मुझे बताइए — मैं यहाँ हूँ।",
    "gu": "નમસ્તે! હું MindMate છું. આજે તમે કેવું અનુભવો છો? મને કહો — હું અહીં છું.",
}

# System prompt per language — close friend tone, listen-first
SYSTEM_PROMPTS = {
    "en": """You are MindMate — a close, caring friend (not a therapist).
Speak exactly like a warm friend texting someone they care about.

RULES — follow these strictly:
- Turn 1 (first message): NEVER give advice. Just ask what's wrong in a warm, casual way.
  Examples: "Aww, what's wrong? Tell me what's going on 💙"
            "Oh no, that doesn't sound good. What happened?"
            "Hey, I'm here. What's been going on with you?"
- Turn 2 (they explain): Validate their feelings first. Then ask one gentle follow-up.
  Examples: "Ugh, that sounds so hard. Anyone would feel that way."
            "That's a lot to deal with. How long has this been going on?"
- Turn 3+: Continue supporting. Offer ONE soft suggestion only if it feels natural.
- Keep EVERY reply to 2-3 sentences max. This is voice — short is better.
- NO bullet points. NO markdown. Plain speech only.
- Use emojis the way a friend would in WhatsApp — naturally, not excessively.""",

    "hi": """तुम MindMate हो — एक करीबी, प्यार करने वाला दोस्त (therapist नहीं)।
WhatsApp पर बात करने वाले दोस्त की तरह बोलो।

नियम — इन्हें ज़रूर follow करो:
- पहला message: कभी advice मत दो। बस प्यार से पूछो क्या हुआ।
  जैसे: "अरे यार, क्या हुआ? बताओ मुझे 💙"
        "अरे नहीं, ठीक नहीं लगा सुनकर। क्या हुआ?"
        "मैं हूँ यहाँ। क्या चल रहा है तुम्हारे साथ?"
- दूसरा message: पहले feelings validate करो, फिर एक gentle सवाल पूछो।
- तीसरा+ message: support करते रहो। एक soft suggestion दे सकते हो।
- हर जवाब 2-3 sentences से ज़्यादा नहीं। यह voice है — short बेहतर है।
- कोई bullet points नहीं। Plain बातचीत की भाषा।""",

    "gu": """તમે MindMate છો — એક ઘનિષ્ઠ, કાળજી રાખતા મિત્ર (therapist નહીં).
WhatsApp પર વાત કરતા મિત્રની જેમ બોલો.

નિયમો — આ ચોક્કસ follow કરો:
- પ્રથમ message: ક્યારેય advice ન આપો. માત્ર પ્રેમથી પૂછો શું થયું.
  જેમ કે: "અરે, શું થયું? મને કહો 💙"
          "અરે ના, આ સાંભળી ચિંતા થઈ. શું બન્યું?"
          "હું અહીં છું. તમારી સાથે શું ચાલી રહ્યું છે?"
- બીજો message: પહેલા feelings validate કરો, પછી એક gentle પ્રશ્ન પૂછો.
- ત્રીજો+ message: support ચાલુ રાખો. એક soft suggestion આપી શકો.
- દરેક જવાબ 2-3 sentences થી વધારે નહીં. Voice છે — ટૂંકું સારું.
- કોઈ bullet points નહીં. Plain વાતચીતની ભાષા.""",
}


def render_voice_component(language: str = "en", api_key: str = "") -> str | None:
    """
    Renders a fully self-contained voice conversation widget.
    
    The component:
    1. Greets the user with TTS on first load
    2. Records mic input with Web Speech Recognition
    3. Sends transcript + history to Anthropic API (or uses local fallback)
    4. Speaks the AI response aloud with Web Speech Synthesis
    5. Shows a scrollable chat transcript inside the widget
    6. Passes the latest user transcript to Streamlit for mood logging
    
    Parameters
    ----------
    language : str   "en" | "hi" | "gu"
    api_key  : str   Anthropic API key (optional — fallback used if empty)
    
    Returns
    -------
    str | None  Latest user utterance (for mood tracking in app.py)
    """
    lc         = LANG_CODES.get(language, "en-IN")
    lang_name  = LANG_NAMES.get(language, "English")
    greeting   = GREETINGS.get(language, GREETINGS["en"])
    sys_prompt = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en"])

    # Escape for JS string embedding
    greeting_js   = greeting.replace('"', '\\"').replace('\n', ' ')
    sys_prompt_js = sys_prompt.replace('`', '\\`').replace('\\n', '\\\\n')

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
/* ── Reset & base ── */
*{{box-sizing:border-box;margin:0;padding:0}}
body{{
  background:transparent;
  font-family:'Segoe UI',sans-serif;
  display:flex;flex-direction:column;align-items:center;
  gap:10px;padding:14px 10px;
  color:#E2E8F0;
}}

/* ── Avatar ring ── */
#avatar-wrap{{
  position:relative;width:100px;height:100px;
  display:flex;align-items:center;justify-content:center;
}}
#avatar{{
  width:90px;height:90px;border-radius:50%;
  background:linear-gradient(135deg,#7C3AED,#5B21B6);
  display:flex;align-items:center;justify-content:center;
  font-size:2.5rem;
  box-shadow:0 4px 24px rgba(124,58,237,0.45);
  transition:all .3s;z-index:2;position:relative;
}}
#avatar.listening{{
  background:linear-gradient(135deg,#C53030,#9B2C2C);
  box-shadow:0 4px 28px rgba(197,48,48,0.6);
  animation:avatarPulse 1s infinite;
}}
#avatar.speaking{{
  background:linear-gradient(135deg,#276749,#22543D);
  box-shadow:0 4px 28px rgba(52,211,153,0.6);
  animation:speakPulse 0.6s infinite alternate;
}}
@keyframes avatarPulse{{
  0%,100%{{transform:scale(1)}} 50%{{transform:scale(1.06)}}
}}
@keyframes speakPulse{{
  from{{transform:scale(1)}} to{{transform:scale(1.08)}}
}}

/* ── Sound wave bars (visible when speaking) ── */
#waves{{
  display:flex;gap:3px;align-items:center;height:24px;
  opacity:0;transition:opacity .3s;
}}
#waves.active{{opacity:1}}
.bar{{
  width:4px;border-radius:3px;
  background:linear-gradient(180deg,#A78BFA,#7C3AED);
  animation:wave 0.8s ease-in-out infinite alternate;
}}
.bar:nth-child(1){{height:8px;animation-delay:0s}}
.bar:nth-child(2){{height:16px;animation-delay:.1s}}
.bar:nth-child(3){{height:22px;animation-delay:.2s}}
.bar:nth-child(4){{height:16px;animation-delay:.3s}}
.bar:nth-child(5){{height:8px;animation-delay:.4s}}
@keyframes wave{{from{{transform:scaleY(1)}} to{{transform:scaleY(0.4)}}}}

/* ── Status label ── */
#status{{
  font-size:.78rem;color:#A0AEC0;text-align:center;
  min-height:1.2em;max-width:280px;
}}
#status.err{{color:#FC8181}}
#status.ok{{color:#68D391}}
#status.speak{{color:#A78BFA}}

/* ── Language badge ── */
#badge{{
  font-size:.68rem;color:#7C3AED;
  background:rgba(124,58,237,.1);
  border:1px solid rgba(124,58,237,.25);
  border-radius:20px;padding:2px 10px;
}}

/* ── Chat transcript ── */
#transcript{{
  width:100%;max-width:340px;
  max-height:220px;overflow-y:auto;
  display:flex;flex-direction:column;gap:6px;
  padding:4px 2px;
  scrollbar-width:thin;
  scrollbar-color:rgba(124,58,237,.3) transparent;
}}
.bubble{{
  padding:7px 12px;border-radius:12px;
  font-size:.82rem;line-height:1.5;
  max-width:90%;word-break:break-word;
  animation:fadeIn .3s ease;
}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(4px)}} to{{opacity:1;transform:translateY(0)}}}}
.bubble.user{{
  background:linear-gradient(135deg,rgba(91,33,182,.6),rgba(76,29,149,.5));
  border:1px solid rgba(124,58,237,.3);
  align-self:flex-end;color:#E2E8F0;
}}
.bubble.ai{{
  background:rgba(255,255,255,.05);
  border:1px solid rgba(124,58,237,.2);
  align-self:flex-start;color:#CBD5E0;
}}
.bubble.ai .speaker{{
  color:#A78BFA;font-size:.7rem;font-weight:600;
  margin-bottom:3px;display:block;
}}

/* ── Controls ── */
#controls{{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}}
#micBtn{{
  width:60px;height:60px;border-radius:50%;border:none;
  cursor:pointer;font-size:1.6rem;
  background:linear-gradient(135deg,#7C3AED,#5B21B6);
  color:#fff;box-shadow:0 3px 16px rgba(124,58,237,.4);
  transition:all .2s;outline:none;
}}
#micBtn:hover{{transform:scale(1.08)}}
#micBtn.on{{
  background:linear-gradient(135deg,#C53030,#9B2C2C);
  animation:avatarPulse 1s infinite;
}}
#stopSpeakBtn{{
  padding:7px 14px;border-radius:8px;border:none;
  background:rgba(255,255,255,.08);color:#E2E8F0;
  font-size:.75rem;cursor:pointer;display:none;
}}
#clearBtn{{
  padding:7px 14px;border-radius:8px;border:none;
  background:rgba(255,255,255,.06);color:#718096;
  font-size:.75rem;cursor:pointer;
}}

/* ── No support ── */
#nosup{{color:#FC8181;font-size:.82rem;text-align:center;max-width:280px;display:none;line-height:1.6}}
</style>
</head>
<body>

<div id="badge">🌐 {lang_name} ({lc})</div>

<div id="avatar-wrap">
  <div id="avatar">🧠</div>
</div>

<div id="waves">
  <div class="bar"></div><div class="bar"></div><div class="bar"></div>
  <div class="bar"></div><div class="bar"></div>
</div>

<div id="status">Tap the mic to start talking</div>

<div id="transcript"></div>

<div id="controls">
  <button id="micBtn" onclick="toggleMic()" title="Tap to speak">🎤</button>
  <button id="stopSpeakBtn" onclick="stopSpeaking()">⏹ Stop speaking</button>
  <button id="clearBtn" onclick="clearChat()">🗑 Clear</button>
</div>

<div id="nosup">⚠️ Please use <strong>Google Chrome</strong> or <strong>Microsoft Edge</strong> for voice.</div>

<script>
/* ════════════════════════════════════════════════════════
   CONFIG
   ════════════════════════════════════════════════════════ */
const LANG_CODE   = "{lc}";
const API_KEY     = "{api_key}";
const SYS_PROMPT  = `{sys_prompt_js}`;
const GREETING    = "{greeting_js}";

/* ════════════════════════════════════════════════════════
   STATE
   ════════════════════════════════════════════════════════ */
let recognition  = null;
let listening    = false;
let speaking     = false;
let finalText    = "";
let convHistory  = [];   // {{role:"user"|"assistant", content:str}}
let greeted      = false;

/* ════════════════════════════════════════════════════════
   DOM REFS
   ════════════════════════════════════════════════════════ */
const avatar      = document.getElementById("avatar");
const waves       = document.getElementById("waves");
const statusEl    = document.getElementById("status");
const transcriptEl= document.getElementById("transcript");
const micBtn      = document.getElementById("micBtn");
const stopBtn     = document.getElementById("stopSpeakBtn");
const nosup       = document.getElementById("nosup");

/* ════════════════════════════════════════════════════════
   BROWSER SUPPORT CHECK
   ════════════════════════════════════════════════════════ */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const SS = window.speechSynthesis;

if (!SR || !SS) {{
  micBtn.style.display  = "none";
  nosup.style.display   = "block";
  statusEl.style.display= "none";
}} else {{
  setupRecognition();
  // Greet after a short delay (browsers need user interaction for TTS first click)
  setTimeout(()=>{{ if(!greeted) greetUser(); }}, 800);
}}

/* ════════════════════════════════════════════════════════
   SPEECH RECOGNITION SETUP
   ════════════════════════════════════════════════════════ */
function setupRecognition() {{
  recognition = new SR();
  recognition.lang            = LANG_CODE;
  recognition.interimResults  = true;
  recognition.continuous      = false;
  recognition.maxAlternatives = 1;

  recognition.onstart = () => {{
    listening = true;
    micBtn.classList.add("on");
    micBtn.textContent = "⏹";
    avatar.classList.add("listening");
    avatar.textContent = "👂";
    setStatus("🔴 Listening… speak now", "");
    finalText = "";
  }};

  recognition.onresult = (e) => {{
    let interim = "";
    finalText = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {{
      const t = e.results[i][0].transcript;
      e.results[i].isFinal ? finalText += t : interim += t;
    }}
    // Show live interim in status
    if (interim) setStatus("🎤 " + interim.slice(0,60) + (interim.length>60?"…":""), "");
  }};

  recognition.onend = () => {{
    listening = false;
    micBtn.classList.remove("on");
    micBtn.textContent = "🎤";
    avatar.classList.remove("listening");
    avatar.textContent = "🧠";

    if (finalText.trim()) {{
      setStatus("🤔 MindMate is thinking…", "ok");
      addBubble(finalText, "user");
      // Send to Streamlit for mood logging
      window.parent.postMessage({{ type:"streamlit:setComponentValue", value:finalText }}, "*");
      // Get AI response
      getAIResponse(finalText);
    }} else {{
      setStatus("Nothing heard — tap mic and try again", "err");
    }}
  }};

  recognition.onerror = (e) => {{
    listening = false;
    micBtn.classList.remove("on");
    micBtn.textContent = "🎤";
    avatar.classList.remove("listening");
    avatar.textContent = "🧠";
    const msgs = {{
      "not-allowed"  : "❌ Mic blocked — allow access in browser settings",
      "no-speech"    : "🔇 No speech — try speaking louder",
      "network"      : "🌐 Network error — check internet connection",
      "audio-capture": "🎙️ No microphone found",
    }};
    setStatus(msgs[e.error] || "Error: " + e.error, "err");
  }};
}}

/* ════════════════════════════════════════════════════════
   MIC TOGGLE
   ════════════════════════════════════════════════════════ */
function toggleMic() {{
  if (speaking) stopSpeaking();
  if (!recognition) return;
  if (listening) {{
    recognition.stop();
  }} else {{
    try {{ recognition.start(); }}
    catch(e) {{ setStatus("Busy — wait a moment", "err"); }}
  }}
}}

/* ════════════════════════════════════════════════════════
   AI RESPONSE  (Anthropic API → friendly fallback)
   ════════════════════════════════════════════════════════ */
async function getAIResponse(userText) {{
  convHistory.push({{ role:"user", content:userText }});
  const turn = convHistory.filter(m => m.role === "user").length;

  let reply = "";

  if (API_KEY && API_KEY.length > 10) {{
    try {{
      // Inject turn context into system prompt
      const turnNote = turn === 1
        ? "\\n\\nThis is their FIRST message. Do NOT give any advice. Just gently ask what is wrong, like a caring friend."
        : turn === 2
        ? "\\n\\nThey have shared more now. Validate their feelings warmly first, then ask one gentle follow-up question."
        : "\\n\\nYou have been talking for a while. Continue supporting them. A soft suggestion is okay if it feels natural.";

      const res = await fetch("https://api.anthropic.com/v1/messages", {{
        method: "POST",
        headers: {{
          "Content-Type":      "application/json",
          "x-api-key":         API_KEY,
          "anthropic-version": "2023-06-01",
        }},
        body: JSON.stringify({{
          model:      "claude-sonnet-4-20250514",
          max_tokens: 200,
          system:     SYS_PROMPT + turnNote,
          messages:   convHistory.slice(-8),
        }}),
      }});
      const data = await res.json();
      if (data.content && data.content[0]) {{
        reply = data.content[0].text.trim();
      }}
    }} catch(err) {{
      reply = "";
    }}
  }}

  // ── Fallback: turn-aware empathetic responses ──
  if (!reply) {{
    reply = buildFallback(userText, turn);
  }}

  // Clean reply for TTS (strip markdown)
  const cleanReply = reply.replace(/\*\*/g,"").replace(/\*/g,"").replace(/#+/g,"").replace(/•/g,"").trim();

  convHistory.push({{ role:"assistant", content:cleanReply }});
  addBubble(cleanReply, "ai");
  speak(cleanReply);
}}

/* ════════════════════════════════════════════════════════
   NEGATION ENGINE  (mirrors Python emotion_detector logic)
   ════════════════════════════════════════════════════════ */

// English negation triggers
const NEG_EN = new Set([
  "not","no","never","none","nobody","nothing","nowhere","neither","nor",
  "dont","don't","doesnt","doesn't","didnt","didn't","wasnt","wasn't",
  "isnt","isn't","arent","aren't","cant","can't","cannot","wont","won't",
  "shouldnt","shouldn't","wouldnt","wouldn't","couldnt","couldn't",
  "hardly","barely","scarcely","rarely","without","n't"
]);

// Hindi negation words
const NEG_HI = ["नहीं","न","मत","कभी नहीं","बिल्कुल नहीं","नही","नहि"];

// Gujarati negation words
const NEG_GU = ["નહીં","નથી","ન","નહિ","ક્યારેય નહીં","બિલ્કુલ નહીં","નહી"];

const NEG_WINDOW = 3;   // tokens after a negator that are "negated"

/**
 * Tokenise text into [{{negated:bool, word:str}}] pairs.
 * Works for English (space-split + NEG_EN set).
 * For Hindi/Gujarati uses phrase-level negation detection instead.
 */
function tokeniseEn(text) {{
  // expand n't so "don't" → "do n't"
  const norm = text.toLowerCase().replace(/n't/g, " n't");
  const words = norm.match(/[a-z']+/g) || [];
  const result = [];
  let negCount = 0;
  for (const w of words) {{
    if (NEG_EN.has(w)) {{
      negCount = NEG_WINDOW;
      result.push({{negated: false, word: w}});
    }} else {{
      result.push({{negated: negCount > 0, word: w}});
      if (negCount > 0) negCount--;
      // reset at clause boundary
      if (["but","however","although","because","so","and","or"].includes(w))
        negCount = 0;
    }}
  }}
  return result;
}}

// Positive keywords (English)
const POS_KW_EN = new Set([
  "good","well","great","fine","okay","ok","alright","happy","glad","excited",
  "amazing","wonderful","fantastic","awesome","excellent","calm","relaxed",
  "confident","proud","motivated","grateful","hopeful","optimistic","peaceful",
  "better","best","refreshed","positive","enjoying","safe","content","cheerful"
]);
// Negative/burnout keywords (English)
const NEG_KW_EN = new Set([
  "bad","sad","terrible","awful","horrible","miserable","depressed","lonely",
  "crying","cry","tears","upset","unhappy","down","hopeless","empty","drained",
  "exhausted","tired","numb","lost","broken","worthless","useless","hurt","pain"
]);
// Stress keywords (English)
const STRESS_KW_EN = new Set([
  "stressed","stress","overwhelmed","pressure","exam","exams","test","deadline",
  "assignment","anxious","anxiety","worried","worry","panic","nervous","scared",
  "struggling","difficult","hard","tough","burden","overthinking"
]);

/**
 * Detect sentiment from tokens (English).
 * Returns: "bad" | "stress" | "anxious" | "tired" | "good" | "neutral"
 */
function detectSentimentEn(text) {{
  const tokens = tokeniseEn(text);
  let posHits = 0, negHits = 0, stressHits = 0,
      burnHits = 0, anxHits  = 0, tiredHits = 0;

  for (const {{negated, word}} of tokens) {{
    if (POS_KW_EN.has(word)) {{
      negated ? negHits++   : posHits++;
    }} else if (NEG_KW_EN.has(word)) {{
      negated ? posHits += 0.5 : burnHits++;
    }} else if (STRESS_KW_EN.has(word)) {{
      negated ? posHits += 0.3 : stressHits++;
    }}
    // Specific sub-categories
    if (!negated) {{
      if (/^(anxious|anxiety|panic|nervous|scared|fear|worry|worried)$/.test(word)) anxHits++;
      if (/^(tired|exhaust|burnout|burnt|drain|fatigue)$/.test(word))               tiredHits++;
    }}
  }}

  // Decision tree
  if (burnHits  > 0)                          return "bad";
  if (stressHits > 0)                          return "stress";
  if (anxHits   > 0)                          return "anxious";
  if (tiredHits > 0)                          return "tired";
  if (negHits   > 0 && posHits === 0)         return "bad";     // negated positive = bad
  if (posHits   > 0 && negHits  === 0)        return "good";    // genuine positive
  if (posHits   > 0 && negHits  > 0)          return "neutral"; // mixed
  return "neutral";
}}

/**
 * Hindi sentiment — phrase-level negation.
 * Checks for negator words directly adjacent to positive/negative phrases.
 */
function detectSentimentHi(text) {{
  const t = text;
  // Does any negator appear near a positive word?
  const posHi  = ["अच्छा","ठीक","खुश","बढ़िया","शानदार","मस्त","खुशी","अच्छी","ओके"];
  const negHi  = ["बुरा","दुखी","परेशान","थका","टूटा","उदास","रो","रोना","दर्द","खराब","बेकार","अकेला"];
  const stressHi=["तनाव","परीक्षा","चिंता","घबराहट","डर","दबाव","थकान","निराश"];
  const negWords=["नहीं","न","मत","नही","नहि"];

  // Build token list (split by spaces)
  const words = t.split(/\s+/);
  let posHits=0, negHits=0, stressHits=0, burnHits=0;
  let negActive=0;

  for (const w of words) {{
    if (negWords.some(n => w.includes(n))) {{ negActive=NEG_WINDOW; continue; }}
    const isNeg = negActive > 0;
    if (negActive > 0) negActive--;

    if (posHi.some(p => w.includes(p)))    isNeg ? negHits++   : posHits++;
    if (negHi.some(p => w.includes(p)))    isNeg ? posHits+=0.5: burnHits++;
    if (stressHi.some(p => w.includes(p))) isNeg ? posHits+=0.3: stressHits++;
  }}

  if (burnHits  > 0)                return "bad";
  if (stressHits > 0)               return "stress";
  if (negHits   > 0 && posHits===0) return "bad";
  if (posHits   > 0 && negHits ===0)return "good";
  // Fallback: check for raw negative phrases without negation context
  if (/परेशान|दुखी|उदास|थका|रो|दर्द|बुरा|अकेला|निराश/.test(t)) return "bad";
  if (/चिंता|परीक्षा|तनाव|घबराहट|डर/.test(t))                   return "stress";
  if (/अच्छा|ठीक|खुश|बढ़िया|मस्त/.test(t))                     return "good";
  return "neutral";
}}

/**
 * Gujarati sentiment — phrase-level negation.
 */
function detectSentimentGu(text) {{
  const t = text;
  const posGu  = ["સારું","ઠીક","ખુશ","સરસ","મજ્જાનું","આનંદ","સારી","ઓકે"];
  const negGu  = ["ખરાબ","દુઃખી","પરેશાન","થાક","તૂટેલ","ઉદાસ","રડ","દર્દ","નકામ","એકલ"];
  const stressGu=["તણાવ","પરીક્ષા","ચિંતા","ગભરાહટ","ડર","દબાણ","થાક","નિરાશ"];
  const negWords=["નહીં","નથી","ન","નહિ","નહી"];

  const words = t.split(/\s+/);
  let posHits=0, negHits=0, stressHits=0, burnHits=0;
  let negActive=0;

  for (const w of words) {{
    if (negWords.some(n => w.includes(n))) {{ negActive=NEG_WINDOW; continue; }}
    const isNeg = negActive > 0;
    if (negActive > 0) negActive--;

    if (posGu.some(p => w.includes(p)))    isNeg ? negHits++    : posHits++;
    if (negGu.some(p => w.includes(p)))    isNeg ? posHits+=0.5 : burnHits++;
    if (stressGu.some(p => w.includes(p))) isNeg ? posHits+=0.3 : stressHits++;
  }}

  if (burnHits  > 0)                return "bad";
  if (stressHits > 0)               return "stress";
  if (negHits   > 0 && posHits===0) return "bad";
  if (posHits   > 0 && negHits ===0)return "good";
  if (/પરેશાન|દુઃખી|ઉદાસ|થાક|રડ|દર્દ|ખરાબ|એકલ|નિરાશ/.test(t)) return "bad";
  if (/ચિંતા|પરીક્ષા|તણાવ|ગભરાહટ|ડર/.test(t))                   return "stress";
  if (/સારું|ઠીક|ખુશ|સરસ|મજ્જાનું/.test(t))                     return "good";
  return "neutral";
}}

/* ════════════════════════════════════════════════════════
   FALLBACK RESPONSES  (turn-aware + negation-aware, EN+HI+GU)

   Turn 1  → ask what's wrong  (NEVER give advice)
   Turn 2  → validate feelings + gentle follow-up question
   Turn 3+ → validate + optional soft suggestion
   ════════════════════════════════════════════════════════ */
function buildFallback(text, turn) {{
  const lang = LANG_CODE.split("-")[0];
  let sentiment;
  if      (lang === "hi") sentiment = detectSentimentHi(text);
  else if (lang === "gu") sentiment = detectSentimentGu(text);
  else                    sentiment = detectSentimentEn(text);

  const bucket = (sentiment==="bad")     ? "bad"
               : (sentiment==="stress")  ? "stress"
               : (sentiment==="anxious") ? "anxious"
               : (sentiment==="tired")   ? "tired"
               : (sentiment==="good")    ? "good"
               :                          "neutral";

  const R = {{
    en: {{
      ask: {{
        bad:     [
          "Aww, what's wrong? If you're comfortable, tell me what's hurting 💙",
          "Oh no, that doesn't sound good at all. Want to tell me what happened?",
          "Hey, talk to me. What's been going on with you?",
          "I'm here for you. What's wrong — you can tell me everything or just a little, whatever feels okay.",
        ],
        stress:  [
          "Oh no, what's been stressing you out? Tell me what's going on.",
          "Hey, what happened? Is it studies or something else weighing on you?",
          "That sounds like a lot. What's weighing on you the most right now?",
        ],
        anxious: [
          "Aww, what's been making you anxious? Tell me what's running through your head.",
          "Hey, I'm listening. What's been worrying you lately?",
        ],
        tired:   [
          "Oh no, you sound exhausted. What's been draining you — how long has this been going on?",
          "That kind of tiredness is more than just sleep. What's been happening?",
        ],
        good:    [
          "That's so good to hear! What's been going well?",
          "Aw yay! Tell me more — what made things feel good today?",
        ],
        neutral: [
          "I'm here! What's on your mind?",
          "Hey, what's been going on with you lately? Tell me.",
        ],
      }},
      validate: {{
        bad:     [
          "Ugh, that sounds really painful. I'm sorry you're going through that. How long have you been feeling this way?",
          "That makes total sense — anyone would feel that way. Has something specific happened, or has it been building up?",
          "I hear you, and I'm really glad you told me. What's been the hardest part of it all?",
        ],
        stress:  [
          "Ugh, that does sound overwhelming. It makes total sense you're feeling this way. What feels like the hardest part?",
          "That's a lot to deal with at once. Anyone would feel crushed by that. Have you been able to talk to anyone?",
        ],
        anxious: [
          "That sounds genuinely exhausting — when anxiety takes over it's so hard. What's the scariest part?",
          "I totally get why your mind is going there. Has anything helped you before when you felt this way?",
        ],
        tired:   [
          "That kind of exhaustion is so deep — not just tired but empty. How long have you been feeling like this?",
          "I hear you. You've clearly been pushing through a lot. What would feel like rest to you right now?",
        ],
        good:    [
          "I love that for you! What made it feel that way?",
          "That's genuinely so nice to hear. What happened?",
        ],
        neutral: [
          "Got it. I'm here — what's been on your mind?",
          "Okay, keep going. What else is going on?",
        ],
      }},
      support: {{
        bad:     [
          "You don't have to figure this all out right now. Sometimes just saying it out loud already helps. Is there one small thing that might feel slightly better?",
          "I'm really glad you're talking about this. If it ever feels too much, talking to someone you trust can really help.",
        ],
        stress:  [
          "When everything feels too big, try writing it all down — even messily. Gets it out of your head.",
          "Even a short walk can shift things. Your body needs a break even when your mind won't stop.",
        ],
        anxious: [
          "When anxiety spikes, try naming 5 things you can see right now. It pulls your brain back to the present.",
          "Sometimes talking about it — even here — takes away some of anxiety's power.",
        ],
        tired:   [
          "Rest isn't a reward — it's what you need right now. Even 20 minutes of doing nothing. You've earned it.",
          "Is there one small thing that would feel good — not productive, just good?",
        ],
        good:    ["Keep holding onto that feeling — you deserve it. What made things click today?"],
        neutral: ["I'm always here when you want to talk. What's been going on?"],
      }},
    }},
    hi: {{
      ask: {{
        bad:     [
          "अरे यार, क्या हुआ? अगर बताना हो तो बताओ, मैं यहाँ हूँ 💙",
          "ये सुनकर दिल दुखा। क्या हुआ? मुझे बताओ।",
          "मैं हूँ यहाँ। क्या परेशानी है — थोड़ा या सब, जितना सही लगे।",
        ],
        stress:  [
          "अरे, क्या stress हो रहा है? बताओ।",
          "क्या हुआ? College की बात है या कुछ और?",
        ],
        anxious: ["क्या चिंता हो रही है? मन में क्या चल रहा है?"],
        tired:   ["अरे, बहुत थके लग रहे हो। कब से ऐसा है?"],
        good:    ["वाह! क्या हुआ अच्छा?"],
        neutral: ["मैं यहाँ हूँ! क्या बात करनी है?"],
      }},
      validate: {{
        bad:     [
          "यार, ये सुनकर बहुत बुरा लगा। कोई भी ऐसा ही feel करता। कब से है?",
          "मैं समझ सकता हूँ। सबसे मुश्किल क्या लग रहा है?",
        ],
        stress:  ["यार, ये बहुत overwhelming है। क्या सबसे impossible लग रहा है?"],
        anxious: ["चिंता में mind control बहुत मुश्किल होता है। सबसे scary क्या है?"],
        tired:   ["ये थकान बस नींद की नहीं है। कब से feel हो रहा है?"],
        good:    ["बहुत अच्छा लगा सुनकर! क्या हुआ?"],
        neutral: ["बताते रहो, मैं सुन रहा हूँ।"],
      }},
      support: {{
        bad:     [
          "तुम्हें अभी सब solve नहीं करना है। बस बात करना भी काफी है।",
          "अगर बहुत ज़्यादा हो जाए, किसी भरोसेमंद से बात करना help करता है।",
        ],
        stress:  ["जब सब बड़ा लगे, सब लिख दो — chaotic भी चलेगा। हल्का लगेगा।"],
        anxious: ["जब anxiety बढ़े, 5 चीज़ें देखो सामने। Mind को present में लाता है।"],
        tired:   ["Rest reward नहीं है — अभी ज़रूरत है। 20 minutes कुछ नहीं करना ठीक है।"],
        good:    ["ये feeling बनाए रखो। आज क्या खास था?"],
        neutral: ["जब भी बात करनी हो, मैं यहाँ हूँ।"],
      }},
    }},
    gu: {{
      ask: {{
        bad:     [
          "અરે, શું થયું? જો comfortable હો તો કહો, હું અહીં છું 💙",
          "આ સાંભળી ચિંતા થઈ. શું ચાલી રહ્યું છે?",
          "હું અહીં છું. શું પરેશાની છે — ગમે તેટલું કહો.",
        ],
        stress:  ["અરે, શું stress છે? શું ચાલી રહ્યું છે?"],
        anxious: ["શું ચિંતા છે? મનમાં શું ચાલે છે?"],
        tired:   ["ઘણું થાકેલા લાગો છો. ક્યારથી?"],
        good:    ["વાહ! શું સારું થયું?"],
        neutral: ["હું અહીં છું! શું વાત?"],
      }},
      validate: {{
        bad:     [
          "આ સાંભળી ઘણું દુઃખ થયું. ક્યારથી ચાલી રહ્યું છે?",
          "સૌથી કઠિન ભાગ કયો છે?",
        ],
        stress:  ["ઘણું overwhelming છે. સૌથી impossible શું લાગે છે?"],
        anxious: ["ચિંતામાં mind control ઘણો મુશ્કેલ. Scary ભાગ કયો?"],
        tired:   ["આ થાક ઊંઘ કરતાં ઊંડો છે. ક્યારથી?"],
        good:    ["ખૂબ સારું! શું થયું?"],
        neutral: ["કહેતા રહો, સાંભળું છું."],
      }},
      support: {{
        bad:     [
          "હમણાં બધું solve ન કરો. અહીં વાત કરવી પણ ઘણી મદદ.",
          "ઘણું થઈ જાય ત્યારે, ભરોસાના સાથે વાત ઘણી મદદ કરે.",
        ],
        stress:  ["બધું ઘણું મોટું લાગે ત્યારે, બધું લખી નાખો. હળવું લાગે."],
        anxious: ["ચિંતા વધે ત્યારે, 5 વસ્તુ જુઓ. Mind present આવે."],
        tired:   ["Rest reward નથી — જરૂર છે. 20 min કંઈ ન કરો — ઠીક."],
        good:    ["આ feeling રાખો. ખાસ શું હતું?"],
        neutral: ["ગમે ત્યારે, હું અહીં."],
      }},
    }},
  }};

  const L = R[lang] || R.en;

  if (turn <= 1) {{
    return pick(L.ask[bucket] || L.ask.neutral || L.ask.bad);
  }} else if (turn === 2) {{
    return pick(L.validate[bucket] || L.validate.neutral);
  }} else {{
    const base = pick(L.validate[bucket] || L.validate.neutral);
    const sugg = L.support[bucket] || null;
    if (sugg && Math.random() > 0.45) return base + " " + pick(sugg);
    return base;
  }}
}}

function pick(arr) {{ return arr[Math.floor(Math.random() * arr.length)]; }}

/* ════════════════════════════════════════════════════════
   TEXT-TO-SPEECH
   ════════════════════════════════════════════════════════ */
function speak(text) {{
  if (!SS) return;
  SS.cancel();

  // Strip to plain text for TTS
  const plain = text.replace(/[*_`#]/g, "").trim();

  const utterance       = new SpeechSynthesisUtterance(plain);
  utterance.lang        = LANG_CODE;
  utterance.rate        = 0.92;   // slightly slower = more natural
  utterance.pitch       = 1.05;
  utterance.volume      = 1.0;

  // Try to find a native voice for the language
  const voices = SS.getVoices();
  const match  = voices.find(v => v.lang.startsWith(LANG_CODE.split("-")[0]) && !v.name.toLowerCase().includes("compact"));
  if (match) utterance.voice = match;

  utterance.onstart = () => {{
    speaking = true;
    avatar.classList.add("speaking");
    avatar.textContent = "🗣️";
    waves.classList.add("active");
    stopBtn.style.display = "inline-block";
    setStatus("🔊 MindMate is speaking…", "speak");
  }};

  utterance.onend = () => {{
    speaking = false;
    avatar.classList.remove("speaking");
    avatar.textContent = "🧠";
    waves.classList.remove("active");
    stopBtn.style.display = "none";
    setStatus("Tap mic to reply", "ok");
  }};

  utterance.onerror = () => {{
    speaking = false;
    avatar.classList.remove("speaking");
    avatar.textContent = "🧠";
    waves.classList.remove("active");
    stopBtn.style.display = "none";
    setStatus("Tap mic to speak", "");
  }};

  SS.speak(utterance);
}}

function stopSpeaking() {{
  SS.cancel();
  speaking = false;
  avatar.classList.remove("speaking");
  avatar.textContent = "🧠";
  waves.classList.remove("active");
  stopBtn.style.display = "none";
  setStatus("Tap mic to speak", "");
}}

/* ════════════════════════════════════════════════════════
   GREETING ON LOAD
   ════════════════════════════════════════════════════════ */
function greetUser() {{
  greeted = true;
  const bubble = document.createElement("div");
  bubble.className = "bubble ai";
  bubble.innerHTML = `<span class='speaker'>🧠 MindMate</span>${{GREETING}}`;
  transcriptEl.appendChild(bubble);
  transcriptEl.scrollTop = transcriptEl.scrollHeight;
  // Speak greeting (may be blocked until user clicks — that's fine)
  speak(GREETING);
}}

/* ════════════════════════════════════════════════════════
   UI HELPERS
   ════════════════════════════════════════════════════════ */
function addBubble(text, role) {{
  const div = document.createElement("div");
  div.className = "bubble " + role;
  if (role === "ai") {{
    div.innerHTML = `<span class='speaker'>🧠 MindMate</span>${{text}}`;
  }} else {{
    div.innerHTML = `<span class='speaker' style='color:#C4B5FD;'>🧑‍🎓 You</span>${{text}}`;
  }}
  transcriptEl.appendChild(div);
  transcriptEl.scrollTop = transcriptEl.scrollHeight;
}}

function clearChat() {{
  transcriptEl.innerHTML = "";
  convHistory = [];
  SS.cancel();
  setStatus("Tap mic to start", "");
  greetUser();
}}

function setStatus(msg, cls) {{
  statusEl.textContent = msg;
  statusEl.className   = cls || "";
}}

/* ════════════════════════════════════════════════════════
   Voices load asynchronously in some browsers
   ════════════════════════════════════════════════════════ */
if (SS && SS.onvoiceschanged !== undefined) {{
  SS.onvoiceschanged = () => {{}};
}}
</script>
</body>
</html>"""

    result = components.html(html, height=560, scrolling=False)
    return result if isinstance(result, str) and result.strip() else None


def is_available() -> bool:
    return True
