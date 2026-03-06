"""
modules/emotion_detector.py
─────────────────────────────────────────────────────────────────────────────
Emotion detection with FULL NEGATION HANDLING.

THE BUG THIS FIXES:
  "I am not feeling good"  → was wrongly detected as Positive (saw "good")
  "I don't feel great"     → was wrongly detected as Positive (saw "great")
  "not happy at all"       → was wrongly detected as Positive (saw "happy")

HOW IT WORKS NOW:
  1. Tokenise text into (negated, word) pairs using a sliding negation window.
     Any word within 3 tokens after: not/no/never/don't/doesn't/didn't/
     can't/cannot/won't/hardly/barely/neither/nor  → is flagged as negated.
  2. Keyword matching checks the negated flag:
       - Negated positive keyword  → treated as Stress/negative signal
       - Negated negative keyword  → treated as positive signal (double negative)
  3. VADER compound score is still used as the primary numerical backbone
     (VADER already handles many negations internally).
  4. TextBlob polarity is blended in as a secondary signal.
  5. Custom keyword boost adjusts the blended score AFTER negation check.
─────────────────────────────────────────────────────────────────────────────
"""

import re
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

vader = SentimentIntensityAnalyzer()

# ── Negation trigger words ────────────────────────────────────────────────────
NEGATORS = {
    "not","no","never","none","nobody","nothing","nowhere","neither","nor",
    "dont","don't","doesnt","doesn't","didnt","didn't","wasnt","wasn't",
    "isnt","isn't","arent","aren't","cant","can't","cannot","wont","won't",
    "shouldnt","shouldn't","wouldnt","wouldn't","couldnt","couldn't",
    "hardly","barely","scarcely","rarely","without","lack","lacking",
    "n't",  # catches contractions like haven't, mustn't after splitting
}
NEGATION_WINDOW = 3   # words after a negator that are considered negated

# ── Keyword banks ─────────────────────────────────────────────────────────────
POSITIVE_KW = {
    "happy","happiness","great","good","well","fine","amazing","wonderful",
    "fantastic","excellent","awesome","excited","joy","joyful","love","loved",
    "calm","relaxed","confident","proud","motivated","energized","grateful",
    "hopeful","optimistic","peaceful","content","cheerful","glad","pleased",
    "better","best","enjoying","enjoy","enjoying","refreshed","positive",
    "strong","safe","okay","ok","alright",
}

STRESS_KW = {
    "stressed","stress","stressful","overwhelmed","overwhelm","pressure",
    "deadline","exam","exams","test","tests","assignment","assignments",
    "anxious","anxiety","worried","worry","worrying","panic","panicking",
    "nervous","fear","scared","tense","tension","overthinking","overthink",
    "struggling","struggle","difficult","hard","tough","burden",
}

BURNOUT_KW = {
    "burnout","burnt","exhausted","exhaustion","drained","drain","tired",
    "fatigue","fatigued","numb","hopeless","hopelessness","empty","emptiness",
    "meaningless","unmotivated","demotivated","give up","giving up","quit",
    "pointless","disconnected","worthless","useless","broken","lost",
    "depressed","depression","lonely","loneliness","alone","isolated",
    "crying","cried","cry","tears","sad","sadness","miserable","misery",
    "upset","unhappy","bad","terrible","awful","horrible","worse","worst",
}

EMERGENCY_KW = {
    "suicide","suicidal","kill myself","end my life","end it all",
    "don't want to live","don't want to be alive","want to die",
    "self harm","self-harm","hurt myself","cutting myself","no reason to live",
    "better off dead","can't go on",
}

EMOTION_EMOJI  = {"Positive":"😊","Neutral":"😐","Stress":"😰","Anxiety":"😟","Burnout":"😔"}
EMOTION_COLOR  = {"Positive":"#4CAF50","Neutral":"#9E9E9E","Stress":"#FF9800","Anxiety":"#F44336","Burnout":"#9C27B0"}


# ── Negation-aware tokeniser ──────────────────────────────────────────────────

def _tokenise_with_negation(text: str) -> list[tuple[bool, str]]:
    """
    Returns list of (is_negated: bool, word: str) for every token.

    Example:
      "I am not feeling good today"
      → [(F,"i"),(F,"am"),(F,"not"),(T,"feeling"),(T,"good"),(T,"today")]
    """
    # Normalise contractions so "don't" → "don t" etc. so "n't" is a token
    text = re.sub(r"n't", " n't", text, flags=re.IGNORECASE)
    words = re.findall(r"[a-z']+", text.lower())

    result = []
    neg_counter = 0          # countdown: how many more words are negated

    for w in words:
        if w in NEGATORS:
            neg_counter = NEGATION_WINDOW
            result.append((False, w))   # the negator itself is not negated
        else:
            is_neg = neg_counter > 0
            result.append((is_neg, w))
            if neg_counter > 0:
                neg_counter -= 1
            # Reset negation at clause boundaries
            if w in {",", "but", "however", "although", "though", "yet",
                     "because", "so", "and", "or"}:
                neg_counter = 0

    return result


def _keyword_signals(tokens: list[tuple[bool, str]]) -> dict:
    """
    Returns counts of positive/negative keyword hits, accounting for negation.

    A negated positive keyword  → counts as a negative signal (+1 to neg_hits)
    A negated negative keyword  → counts as a positive signal (+1 to pos_hits)
    """
    pos_hits = 0
    neg_hits = 0
    burnout_hits = 0
    stress_hits  = 0

    for negated, word in tokens:
        if word in POSITIVE_KW:
            if negated:
                neg_hits += 1        # "not good" → negative
            else:
                pos_hits += 1        # "feeling good" → positive

        elif word in BURNOUT_KW:
            if negated:
                pos_hits += 0.5      # "not sad" → weakly positive
            else:
                burnout_hits += 1

        elif word in STRESS_KW:
            if negated:
                pos_hits += 0.3      # "not stressed" → mildly positive
            else:
                stress_hits += 1

    return {
        "pos": pos_hits,
        "neg": neg_hits,
        "burnout": burnout_hits,
        "stress": stress_hits,
    }


# ── Main detection function ───────────────────────────────────────────────────

def detect_emotion(text: str) -> dict:
    """
    Analyses text and returns:
      score      : float -1.0 (very negative) to +1.0 (very positive)
      emotion    : "Positive" | "Neutral" | "Stress" | "Anxiety" | "Burnout"
      confidence : float 0.0–1.0
      emergency  : bool
    """
    if not text or not text.strip():
        return {"score": 0.0, "emotion": "Neutral", "confidence": 0.5, "emergency": False}

    tl = text.lower()

    # ── Emergency check (phrase-level, no negation flip needed) ──────────────
    emergency = any(phrase in tl for phrase in EMERGENCY_KW)

    # ── VADER (handles most negations well internally) ────────────────────────
    vs       = vader.polarity_scores(text)
    compound = vs["compound"]                    # -1 to +1

    # ── TextBlob ──────────────────────────────────────────────────────────────
    tb_polarity = TextBlob(text).sentiment.polarity   # -1 to +1

    # ── Blend: VADER 65% + TextBlob 35% ──────────────────────────────────────
    blended = 0.65 * compound + 0.35 * tb_polarity

    # ── Negation-aware keyword signals ───────────────────────────────────────
    tokens  = _tokenise_with_negation(text)
    signals = _keyword_signals(tokens)

    keyword_emotion = None

    if signals["burnout"] > 0:
        keyword_emotion = "Burnout"
        blended = min(blended - 0.25 * signals["burnout"], -0.5)

    elif signals["stress"] > 0:
        keyword_emotion = "Stress"
        blended = min(blended - 0.15 * signals["stress"], -0.3)

    elif signals["neg"] > 0 and signals["pos"] == 0:
        # Negated positives with no genuine positives → negative
        keyword_emotion = "Stress"
        blended = min(blended - 0.2 * signals["neg"], -0.25)

    elif signals["pos"] > 0 and signals["neg"] == 0:
        # Genuine positives with no negation
        keyword_emotion = "Positive"
        blended = max(blended + 0.1 * signals["pos"], 0.3)

    elif signals["pos"] > 0 and signals["neg"] > 0:
        # Mixed: e.g. "not good but not terrible"
        net = signals["pos"] - signals["neg"]
        if net > 0:
            keyword_emotion = "Positive"
            blended = max(blended + 0.08, 0.1)
        elif net < 0:
            keyword_emotion = "Stress"
            blended = min(blended - 0.08, -0.1)
        # net == 0 → leave blended as-is, no keyword_emotion

    # ── Classify from blended score ───────────────────────────────────────────
    if keyword_emotion:
        emotion = keyword_emotion
    elif blended >= 0.30:   emotion = "Positive"
    elif blended >= 0.05:   emotion = "Neutral"
    elif blended >= -0.30:  emotion = "Stress"
    elif blended >= -0.60:  emotion = "Anxiety"
    else:                   emotion = "Burnout"

    confidence = round(min(abs(blended) + 0.38, 1.0), 2)

    return {
        "score":      round(blended, 3),
        "emotion":    emotion,
        "confidence": confidence,
        "emergency":  emergency,
        "vader":      vs,
        # debug fields (handy for testing)
        "_signals":   signals,
    }


def get_emotion_emoji(e): return EMOTION_EMOJI.get(e, "🤔")
def get_emotion_color(e): return EMOTION_COLOR.get(e, "#607D8B")


# ── Quick self-test (run: python emotion_detector.py) ─────────────────────────
if __name__ == "__main__":
    tests = [
        # negated positives → should be Stress/Anxiety/Burnout
        ("I am not feeling good",           "Stress/negative"),
        ("I don't feel well today",         "Stress/negative"),
        ("I'm not okay",                    "Stress/negative"),
        ("Not happy at all",                "Stress/negative"),
        ("I can't feel good about anything","Stress/negative"),
        ("I don't feel great",              "Stress/negative"),
        # genuine positives → should be Positive
        ("I am feeling good today",         "Positive"),
        ("I feel great and happy",          "Positive"),
        ("Everything is going well",        "Positive"),
        # negated negatives → should be Positive/Neutral
        ("I'm not stressed anymore",        "Positive/Neutral"),
        ("Not feeling sad today",           "Positive/Neutral"),
        # plain negatives → should be negative
        ("I feel sad and lonely",           "Burnout/Anxiety"),
        ("I'm exhausted and burnt out",     "Burnout"),
        ("Exam stress is killing me",       "Stress"),
        # mixed
        ("Not bad but not great either",    "Neutral"),
    ]
    print(f"\n{'Input':<45} {'Expected':<22} {'Got':<10} {'Score':>7}")
    print("-"*90)
    for text, expected in tests:
        r = detect_emotion(text)
        ok = "✅" if any(e in r["emotion"] for e in expected.split("/")) else "❌"
        print(f"{ok} {text:<43} {expected:<22} {r['emotion']:<10} {r['score']:>7.3f}")
