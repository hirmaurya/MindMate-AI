"""
modules/ai_chat.py
─────────────────────────────────────────────────────────────────────────────
AI response engine: Anthropic API (primary) + warm friend-like fallback.

KEY DESIGN — respond like a close friend, NOT a therapist:
  Turn 0  — FIRST message  → ask what's wrong, invite them to open up
  Turn 1  — they explain   → validate their feelings, ask one follow-up
  Turn 2+ — deeper chat    → keep validating, offer gentle suggestion only if natural
  NEVER jump straight to advice on the first message.
─────────────────────────────────────────────────────────────────────────────
"""
import requests, random

# ── Anthropic system prompt ───────────────────────────────────────────────────
SYSTEM_PROMPT = """You are MindMate — a close, caring friend who happens to understand mental wellness.
You are talking to a student. Speak EXACTLY like a warm, concerned friend texting — casual, real, human.

STRICT RULES:
1. Turn 1 (first message from them): NEVER give advice. NEVER list tips. Just gently ask what's going on.
   Say things like:
   - "Aww, what's wrong? If you're comfortable, tell me what's hurting 💙"
   - "Oh no, that doesn't sound good. What happened?"
   - "Hey I'm here — what's been going on with you?"

2. Turn 2 (they explain more): Validate their feelings first, THEN ask one caring follow-up.
   Say things like:
   - "Ugh that sounds so hard, anyone would feel that way. How long has this been going on?"
   - "That makes so much sense. What's the hardest part of it all?"

3. Turn 3+: Keep listening and validating. You can gently offer ONE soft suggestion if it feels right —
   frame it as "maybe..." or "sometimes it helps to..." not "you should".

4. Keep every reply to 2–3 sentences MAX. This is a chat, not an essay.

5. ZERO bullet points. ZERO headers. ZERO markdown. Plain conversational sentences only.

6. Use emojis the way a close friend would in WhatsApp — naturally, not excessively.

7. NEVER say "As an AI" or anything clinical. You're a friend, not a bot.

8. If someone mentions feeling hopeless or very dark thoughts, gently ask if they're okay and
   softly mention that talking to someone they trust can really help."""


# ── TURN 0: First contact — just ask, never advise ───────────────────────────
FIRST_CONTACT = {
    "Stress": [
        "Hey, that doesn't sound good 😟 What's been stressing you out? Tell me what's going on.",
        "Aww, stress is the worst. What happened? I'm here if you want to talk about it.",
        "Oh no, what's going on? Something with college or is it something else weighing on you?",
        "That sounds really tough. If you're okay with sharing — what's been getting to you?",
        "I'm listening. What's been making things feel so heavy lately?",
    ],
    "Anxiety": [
        "Anxiety is so exhausting 💙 What's been making you feel this way? Tell me what's running through your head.",
        "Aww, I'm sorry you're feeling like that. What's been worrying you the most lately?",
        "That sounds really hard. What is it that's been making you anxious? I'm listening.",
        "Hey, I'm here. What's been going on? You don't have to figure it out alone.",
        "That kind of worry is so draining. What's the thing that keeps coming back to your mind?",
    ],
    "Burnout": [
        "Oh no 😔 You sound really drained. What's been happening — has it just been too much for too long?",
        "That's really tough to hear. How long have you been feeling this way? What's been going on?",
        "Burnt out is such a hard place to be in. Want to tell me what's been piling up?",
        "Hey, I can hear you're struggling. What's been wearing you down the most?",
        "That emptiness sounds so real. What's been draining you — work, people, everything at once?",
    ],
    "Negative": [
        "Aww, what's wrong? 💙 If you're comfortable, tell me what's hurting — I'm here and I'm listening.",
        "Oh no, I'm sorry to hear that. What happened? You don't have to go through this alone.",
        "Hey, talk to me. What's going on with you today?",
        "That sounds really hard. What's been going on — do you want to share what you're feeling?",
        "I'm here for you. What's wrong? You can tell me everything or just a little — whatever feels okay.",
        "Aww no, I hate that you're feeling that way. What happened? Tell me.",
    ],
    "Positive": [
        "That's so lovely to hear! 😊 What's been going well for you?",
        "Aw yay, I love that! Tell me more — what made today feel good?",
        "That genuinely makes me happy to hear. What's been lifting your spirits?",
        "Oh nice!! What happened? I want to hear everything 🌟",
    ],
    "Neutral": [
        "I'm here! What's been on your mind? You can talk to me about anything.",
        "Hey, what's going on with you lately? I've got time — tell me.",
        "I'm all ears 😊 What would you like to get off your chest?",
        "What's up? Whatever's on your mind, I'm listening.",
    ],
}

# ── TURN 1+: Validate feelings, then gentle follow-up ────────────────────────
FOLLOWUP = {
    "Stress": [
        "Ugh, that does sound really overwhelming 😔 It makes total sense you're feeling this way. Have you been able to take even a small break from it all?",
        "That's a lot to carry all at once. Honestly, anyone would feel stressed by that. What feels like the hardest part right now?",
        "I hear you — that kind of pressure is so real. Have you talked to anyone about this, or have you been carrying it alone?",
        "That sounds genuinely exhausting. You're dealing with a lot. What's been the thing that keeps getting to you the most?",
        "God that does sound like a lot. Anyone would crack under that pressure. Is there anyone around you who knows what you're going through?",
    ],
    "Anxiety": [
        "That sounds genuinely scary to sit with. The way anxiety just hijacks your thoughts... it's so exhausting. Has anything helped you calm down before when it got this bad?",
        "I totally get why your mind is going there. Anxiety makes everything feel so much bigger. What does it feel like — like is it more thoughts racing, or does it hit you physically too?",
        "Ugh, that kind of worry is so hard to shake. You're definitely not alone in feeling that way. What's the one thing that keeps coming back the most?",
        "That sounds really overwhelming. Anxiety is so sneaky — it just takes over. What triggered it this time, if you know?",
        "I hear you, and I'm really glad you told me. That kind of anxiety is genuinely hard to live with. What's been the worst moment today?",
    ],
    "Burnout": [
        "That sounds genuinely exhausting — not just tired but like... empty. Have you been able to do anything recently that felt even slightly good for you?",
        "When everything feels pointless, that's such a heavy thing to carry. You've been pushing really hard. What would feel like rest to you right now?",
        "I hear you. That kind of depletion doesn't happen overnight — you've been carrying a lot for a long time. What's been the biggest drain?",
        "That's so real. Burnout is more than just being tired — it's like your whole system is saying enough. When did things start feeling this way?",
        "Ugh that sounds so heavy. You deserve to feel better than this. What's one thing that actually used to bring you joy before everything got like this?",
    ],
    "Negative": [
        "I'm really glad you told me that 💙 That sounds genuinely painful. How long have you been feeling this way?",
        "That makes total sense — anyone would feel that way. Has something specific happened, or has it been slowly building up?",
        "Ugh, I hear you. That sounds really hard. What's been the hardest part of it all?",
        "I'm so sorry you're going through that. You didn't deserve that. What happened?",
        "That sounds really painful and I'm glad you're talking about it. What's been sitting heaviest on you?",
        "I hear you completely. That kind of hurt is real. Has anyone else in your life known you've been feeling this way?",
    ],
    "Positive": [
        "That's so great to hear!! 🌟 Seriously, tell me more — what's been going well?",
        "Aw yay, I love that for you! What made today feel good?",
        "That makes me so happy to hear 😊 What happened — I want all the details!",
        "Oh I love this!! What's been different lately that's making things feel better?",
    ],
    "Neutral": [
        "I'm all ears 😊 What's been on your mind lately?",
        "Got it! Sometimes just talking helps. What do you want to get off your chest?",
        "I'm here — what's going on with you? How has everything been?",
        "Tell me more. What's the thing you've been sitting with the most lately?",
    ],
}

# ── TURN 2+: Gentle suggestions (added only sometimes, only after listening) ──
SOFT_SUGGESTIONS = {
    "Stress": [
        "If things feel too big right now, sometimes just writing everything down — even messily — helps get it out of your head a bit.",
        "Even a 10-minute walk can shift things slightly. Not a fix, but sometimes your body needs a break even when your brain won't stop.",
        "Sometimes saying it out loud — like you're doing right now — already makes it a tiny bit smaller. You don't have to solve it all today.",
    ],
    "Anxiety": [
        "When anxiety spikes, try naming 5 things you can see right now. It sounds simple but it genuinely pulls your brain back to the present moment.",
        "Sometimes anxiety feeds on silence — talking about it (even to me) can take away some of its grip.",
        "Slow breathing really does help physiologically — breathe in for 4 counts, out for 6. Your nervous system responds to it.",
    ],
    "Burnout": [
        "Rest isn't a reward you have to earn — it's what you actually need right now. Even 20 minutes of doing absolutely nothing is okay.",
        "Is there one tiny thing that would feel good — not productive, just good? A song, food you like, something that makes you feel like yourself?",
        "Burnout often means you've been giving so much and getting very little back. What's one thing you could stop doing, even temporarily?",
    ],
    "Negative": [
        "You don't have to have it figured out right now. Sometimes just saying things out loud — like you are — already helps a little.",
        "If it ever starts feeling like too much to carry alone, talking to someone you really trust — a friend, a family member — can make such a difference.",
    ],
}

QUOTES = [
    '"The secret of getting ahead is getting started." — Mark Twain',
    '"You don\'t have to be great to start, but you have to start to be great." — Zig Ziglar',
    '"Believe you can and you\'re halfway there." — Theodore Roosevelt',
    '"Small progress is still progress. Celebrate every step forward."',
    '"Your only limit is your mind."',
    '"Every expert was once a beginner. Every pro was once an amateur."',
    '"You are allowed to be both a masterpiece and a work in progress."',
    '"It\'s okay to not be okay — as long as you don\'t give up."',
    '"Healing is not linear. Be patient with yourself."',
    '"You\'ve survived every hard day so far. That\'s a 100% track record."',
]


def get_ai_response(user_message: str, emotion_data: dict, history: list, api_key: str = None) -> str:
    emotion = emotion_data.get("emotion", "Neutral")
    score   = emotion_data.get("score", 0.0)
    # Count how many user turns are already in history (before this new message)
    turn    = len([m for m in history if m["role"] == "user"])

    if api_key:
        try:
            return _call_anthropic(user_message, emotion, score, turn, history, api_key)
        except Exception:
            pass

    return _fallback(emotion, score, turn)


def _call_anthropic(msg: str, emotion: str, score: float, turn: int, history: list, api_key: str) -> str:
    turn_context = (
        "This is their VERY FIRST message. Do NOT give any advice at all. "
        "Just warmly ask what's going on, like a caring friend who just got a worrying text."
        if turn == 0 else
        "They've now shared more. Validate their feelings first — make them feel genuinely heard. "
        "Then ask one gentle follow-up question."
        if turn == 1 else
        "You've been talking for a while now. Keep validating. "
        "You can offer one soft suggestion if it feels natural, but don't push it."
    )

    sys = f"""{SYSTEM_PROMPT}

Detected emotion: {emotion} (score: {score:.2f})
Turn number: {turn + 1}
What to do this turn: {turn_context}"""

    messages = [{"role": m["role"], "content": m["content"]} for m in history[-8:]]
    messages.append({"role": "user", "content": msg})

    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model":      "claude-sonnet-4-20250514",
            "max_tokens": 300,
            "system":     sys,
            "messages":   messages,
        },
        timeout=15,
    )
    return r.json()["content"][0]["text"]


def _fallback(emotion: str, score: float, turn: int) -> str:
    """
    Turn-aware fallback with genuine friend-like responses.
    Turn 0 → only ask what's wrong, never advise
    Turn 1 → validate + follow-up question
    Turn 2+ → validate + optional soft suggestion
    """
    # Map to bucket
    if   emotion == "Burnout":                          bucket = "Burnout"
    elif emotion == "Anxiety":                          bucket = "Anxiety"
    elif emotion == "Stress":                           bucket = "Stress"
    elif emotion == "Positive" or score > 0.25:         bucket = "Positive"
    elif score < -0.15 or emotion in ("Neutral",) and score < 0:
                                                        bucket = "Negative"
    else:                                               bucket = "Neutral"

    if turn == 0:
        pool = FIRST_CONTACT.get(bucket) or FIRST_CONTACT["Negative"]
        return random.choice(pool)

    elif turn == 1:
        pool = FOLLOWUP.get(bucket) or FOLLOWUP["Neutral"]
        return random.choice(pool)

    else:
        # Pick from FOLLOWUP but avoid repeating if possible
        pool = FOLLOWUP.get(bucket) or FOLLOWUP["Neutral"]
        base = random.choice(pool)
        # Sometimes add a gentle suggestion (only for negative states)
        if bucket in SOFT_SUGGESTIONS and random.random() > 0.45:
            tip = random.choice(SOFT_SUGGESTIONS[bucket])
            return f"{base}\n\n{tip}"
        return base


def get_motivational_quote() -> str:
    return random.choice(QUOTES)

