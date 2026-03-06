"""
app.py — MindMate AI v2: Intelligent Mental Wellness Assistant
Run:  streamlit run app.py
"""
import streamlit as st, sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from modules.emotion_detector import detect_emotion, get_emotion_emoji, get_emotion_color
from modules.ai_chat          import get_ai_response, get_motivational_quote
from modules.mood_tracker     import log_mood, get_records, get_wellness_score, build_mood_chart, build_emotion_pie
from modules.multilingual     import detect_language, translate_to_english, translate_from_english, get_ui, SUPPORTED_LANGUAGES
from modules.voice_input      import render_voice_component
from modules.emergency        import is_emergency, get_helplines, get_safety_message
from modules.games            import breathing_game, memory_game, mandala_art_game, bottle_shooting_game

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="MindMate AI", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

html,body,[class*="css"]{font-family:'Outfit',sans-serif;}
.stApp{background:radial-gradient(ellipse at 20% 20%,#0F0626 0%,#0A0A18 40%,#060D1F 100%)!important;min-height:100vh;}

/* ── Sidebar ── */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F0626 0%,#0A0A18 100%)!important;border-right:1px solid rgba(124,58,237,.15)!important;}
[data-testid="stSidebar"] .stRadio label{color:#A0AEC0!important;font-size:.88rem!important;padding:.35rem 0!important;}
[data-testid="stSidebar"] .stRadio label:hover{color:#C4B5FD!important;}

/* ── Cards ── */
.mm-card{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:16px;padding:1.25rem 1.5rem;margin-bottom:.9rem;}
.mm-glow{box-shadow:0 0 30px rgba(124,58,237,.1);}
.mm-purple{border-color:rgba(124,58,237,.3);}

/* ── Chat bubbles ── */
.chat-user{background:linear-gradient(135deg,#5B21B6,#4C1D95);color:#fff;border-radius:18px 18px 4px 18px;padding:.75rem 1rem;margin:.5rem 0;max-width:80%;margin-left:auto;font-size:.93rem;line-height:1.55;}
.chat-ai{background:rgba(255,255,255,.04);border:1px solid rgba(124,58,237,.2);color:#E2E8F0;border-radius:18px 18px 18px 4px;padding:.75rem 1rem;margin:.5rem 0;max-width:82%;font-size:.93rem;line-height:1.65;}

/* ── Metric cards ── */
.metric-card{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:1.1rem;text-align:center;transition:all .2s;}
.metric-card:hover{border-color:rgba(124,58,237,.35);transform:translateY(-2px);}

/* ── Buttons ── */
.stButton>button{background:linear-gradient(135deg,#7C3AED,#5B21B6)!important;color:#fff!important;border:none!important;border-radius:10px!important;font-family:'Outfit',sans-serif!important;font-weight:500!important;transition:all .2s!important;}
.stButton>button:hover{transform:translateY(-1px)!important;box-shadow:0 4px 18px rgba(124,58,237,.35)!important;}

/* ── Emergency ── */
.emer-card{background:linear-gradient(135deg,rgba(245,101,101,.12),rgba(197,48,48,.08));border:2px solid rgba(245,101,101,.35);border-radius:14px;padding:1.1rem;margin:.4rem 0;}

/* ── Typography ── */
h1,h2,h3{font-family:'Playfair Display',serif!important;color:#E2E8F0!important;}
h4,h5,h6{color:#A0AEC0!important;}
p,li{color:#CBD5E0!important;}
.sec-title{font-family:'Playfair Display',serif;font-size:1.7rem;color:#E2E8F0;}
.sec-sub{color:#718096;font-size:.88rem;margin-bottom:1.4rem;}

/* ── Progress ── */
.stProgress>div>div>div{background:linear-gradient(90deg,#7C3AED,#A78BFA)!important;}

/* ── Misc ── */
#MainMenu,footer,header{visibility:hidden;}
.stDeployButton{display:none;}
.stSelectbox label,.stRadio>label{color:#A0AEC0!important;}
div[data-testid="stHorizontalBlock"]{gap:.75rem;}

/* ── Onboarding ── */
.onboard-card{
  background:rgba(255,255,255,.03);
  border:1px solid rgba(124,58,237,.25);
  border-radius:20px;padding:2rem 2.5rem;
  max-width:560px;margin:0 auto;
}
.onboard-chip{
  display:inline-block;padding:.45rem 1.1rem;
  border-radius:20px;border:1px solid rgba(124,58,237,.3);
  background:rgba(124,58,237,.08);color:#C4B5FD;
  font-size:.82rem;cursor:pointer;margin:.25rem;
  transition:all .15s;
}
.onboard-chip:hover{background:rgba(124,58,237,.2);}
.onboard-chip.selected{background:rgba(124,58,237,.35);border-color:#7C3AED;color:#fff;}
</style>
""", unsafe_allow_html=True)

# ── Session defaults ───────────────────────────────────────────────────────────
for k,v in {
    "chat_history":[],"current_emotion":{"score":0,"emotion":"Neutral","confidence":0.5,"emergency":False},
    "language":"en","api_key":"","sessions":0,
    # Onboarding
    "onboarded":False,"user_name":"","user_stressor":"","user_goal":"",
}.items():
    if k not in st.session_state: st.session_state[k]=v


# ══════════════════════════════════════════════════════════════════════════════
# ONBOARDING — shown once, fullscreen, before anything else
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.onboarded:
    # Hide sidebar during onboarding
    st.markdown("""<style>[data-testid="stSidebar"]{display:none!important;}
    [data-testid="collapsedControl"]{display:none!important;}</style>""", unsafe_allow_html=True)

    # ── Step tracker in session ──
    if "onboard_step" not in st.session_state:
        st.session_state.onboard_step = 1

    step = st.session_state.onboard_step

    # ── Centered layout ──
    _, col, _ = st.columns([1, 2, 1])
    with col:

        # ── Progress dots ──
        dots = ""
        for i in range(1, 4):
            color = "#7C3AED" if i == step else ("#4ADE80" if i < step else "rgba(255,255,255,.15)")
            dots += f"<span style='display:inline-block;width:10px;height:10px;border-radius:50%;background:{color};margin:0 4px;transition:all .3s;'></span>"
        st.markdown(f"<div style='text-align:center;margin-bottom:1.5rem;padding-top:2rem;'>{dots}</div>", unsafe_allow_html=True)

        # ══ STEP 1 — Welcome + Name ══════════════════════════════════════════
        if step == 1:
            st.markdown("""
            <div style='text-align:center;margin-bottom:1.8rem;'>
              <div style='font-size:4rem;animation:none;'>🧠</div>
              <div style='font-family:Playfair Display,serif;font-size:2.2rem;color:#E2E8F0;margin:.5rem 0;'>
                Meet MindMate
              </div>
              <div style='color:#A78BFA;font-size:1rem;margin-bottom:.3rem;'>Your personal mental wellness companion</div>
              <div style='color:#718096;font-size:.85rem;'>AI-powered · Multilingual · Always here for you</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div class='onboard-card'>", unsafe_allow_html=True)
            st.markdown("<div style='color:#E2E8F0;font-weight:600;font-size:1.05rem;margin-bottom:.8rem;'>👋 First, what should I call you?</div>", unsafe_allow_html=True)

            name = st.text_input("", placeholder="Enter your name…", label_visibility="collapsed", key="ob_name_input")

            st.markdown("<div style='color:#718096;font-size:.78rem;margin-top:.4rem;'>Your name stays on your device — never shared.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2 = st.columns([1,1])
            with c2:
                if st.button("Continue →", use_container_width=True, key="ob_next1"):
                    st.session_state.user_name = name.strip() if name.strip() else "Friend"
                    st.session_state.onboard_step = 2
                    st.rerun()

        # ══ STEP 2 — Biggest stressor ════════════════════════════════════════
        elif step == 2:
            name = st.session_state.user_name
            st.markdown(f"""
            <div style='text-align:center;margin-bottom:1.8rem;'>
              <div style='font-size:3rem;'>🌱</div>
              <div style='font-family:Playfair Display,serif;font-size:1.8rem;color:#E2E8F0;margin:.5rem 0;'>
                Nice to meet you, {name}!
              </div>
              <div style='color:#718096;font-size:.88rem;'>Let me understand you a little better</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div class='onboard-card'>", unsafe_allow_html=True)
            st.markdown("<div style='color:#E2E8F0;font-weight:600;font-size:1rem;margin-bottom:.8rem;'>What's been your biggest challenge lately?</div>", unsafe_allow_html=True)
            st.markdown("<div style='color:#718096;font-size:.8rem;margin-bottom:.8rem;'>Pick one that feels most true right now:</div>", unsafe_allow_html=True)

            stressors = [
                "😰 Exam / study pressure",
                "😔 Feeling low or sad",
                "😟 Anxiety or overthinking",
                "😴 Exhaustion / burnout",
                "😤 Anger or frustration",
                "😶 Feeling lonely",
                "😵 Too much to handle",
                "😊 I'm actually doing okay!",
            ]
            if "ob_stressor" not in st.session_state:
                st.session_state.ob_stressor = ""

            cols = st.columns(2)
            for i, s in enumerate(stressors):
                with cols[i % 2]:
                    selected = st.session_state.ob_stressor == s
                    btn_style = "background:rgba(124,58,237,.35)!important;border:1px solid #7C3AED!important;" if selected else ""
                    if st.button(s, key=f"ob_s_{i}", use_container_width=True):
                        st.session_state.ob_stressor = s
                        st.rerun()

            if st.session_state.ob_stressor:
                st.markdown(f"<div style='color:#A78BFA;font-size:.8rem;margin-top:.6rem;'>✓ Selected: {st.session_state.ob_stressor}</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2 = st.columns([1,1])
            with c1:
                if st.button("← Back", use_container_width=True, key="ob_back2"):
                    st.session_state.onboard_step = 1; st.rerun()
            with c2:
                if st.button("Continue →", use_container_width=True, key="ob_next2"):
                    st.session_state.user_stressor = st.session_state.ob_stressor or "general stress"
                    st.session_state.onboard_step = 3; st.rerun()

        # ══ STEP 3 — Goal + Launch ═══════════════════════════════════════════
        elif step == 3:
            name = st.session_state.user_name
            stressor = st.session_state.user_stressor

            st.markdown(f"""
            <div style='text-align:center;margin-bottom:1.8rem;'>
              <div style='font-size:3rem;'>🎯</div>
              <div style='font-family:Playfair Display,serif;font-size:1.8rem;color:#E2E8F0;margin:.5rem 0;'>
                Almost there, {name}!
              </div>
              <div style='color:#718096;font-size:.88rem;'>One last thing</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div class='onboard-card'>", unsafe_allow_html=True)
            st.markdown("<div style='color:#E2E8F0;font-weight:600;font-size:1rem;margin-bottom:.8rem;'>What would you most like MindMate to help you with?</div>", unsafe_allow_html=True)

            goals = [
                "💬 Someone to talk to when I feel low",
                "📊 Track my mood and understand patterns",
                "🧘 Calm down and relax",
                "🎮 Distract myself and have fun",
                "🌐 All of the above!",
            ]
            if "ob_goal" not in st.session_state:
                st.session_state.ob_goal = ""

            for i, g in enumerate(goals):
                selected = st.session_state.ob_goal == g
                if st.button(g, key=f"ob_g_{i}", use_container_width=True):
                    st.session_state.ob_goal = g; st.rerun()
            if st.session_state.ob_goal:
                st.markdown(f"<div style='color:#A78BFA;font-size:.8rem;margin-top:.4rem;'>✓ {st.session_state.ob_goal}</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            c1, c2 = st.columns([1,1])
            with c1:
                if st.button("← Back", use_container_width=True, key="ob_back3"):
                    st.session_state.onboard_step = 2; st.rerun()
            with c2:
                ready = bool(st.session_state.ob_goal)
                if st.button("🚀 Let's go!" if ready else "Skip & Enter →", use_container_width=True, key="ob_finish"):
                    st.session_state.user_goal = st.session_state.ob_goal
                    st.session_state.onboarded = True
                    # Pre-load a personalised first AI chat message
                    name   = st.session_state.user_name
                    stress = st.session_state.user_stressor.split(" ",1)[-1] if st.session_state.user_stressor else "things"
                    opening = (
                        f"Hey {name}! 👋 I'm MindMate — really glad you're here. "
                        f"I saw you mentioned {stress.lower()} — that's something a lot of students deal with and it's totally okay to talk about it. "
                        f"Whenever you're ready, just tell me what's going on. I'm all ears 💙"
                    )
                    st.session_state.chat_history = [{"role":"assistant","content":opening}]
                    st.rerun()

    st.stop()   # Don't render anything else until onboarding is done

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""<div style='padding:1.2rem 0 1.6rem;text-align:center;'>
    <div style='font-size:2.6rem;'>🧠</div>
    <div style='font-family:Playfair Display,serif;font-size:1.45rem;color:#E2E8F0;margin-top:.3rem;'>MindMate AI</div>
    <div style='color:#6B46C1;font-size:.72rem;margin-top:.2rem;letter-spacing:.08em;text-transform:uppercase;'>Mental Wellness • v2.0</div>
    </div>""", unsafe_allow_html=True)

    # Show user name if onboarded
    if st.session_state.get("user_name"):
        st.markdown(f"""<div style='background:rgba(124,58,237,.1);border:1px solid rgba(124,58,237,.2);
        border-radius:10px;padding:.5rem .8rem;margin-bottom:.8rem;text-align:center;'>
        <span style='color:#A78BFA;font-size:.8rem;'>👤 </span>
        <span style='color:#E2E8F0;font-size:.85rem;font-weight:600;'>{st.session_state.user_name}</span>
        </div>""", unsafe_allow_html=True)

    page = st.radio("Navigate", [
        "🏠 Dashboard","💬 AI Chat","🎤 Voice Assistant","📊 Mood Tracker",
        "🎮 Stress Relief Games","🧘 Meditation","🆘 Emergency Help"
    ], label_visibility="collapsed")

    st.markdown("---")
    lang_inv = {v:k for k,v in SUPPORTED_LANGUAGES.items()}
    lang_sel = st.selectbox("🌐 Language", list(SUPPORTED_LANGUAGES.values()),
                             index=list(SUPPORTED_LANGUAGES.keys()).index(st.session_state.language))
    st.session_state.language = lang_inv[lang_sel]

    st.markdown("---")
    ak = st.text_input("🔑 Anthropic API Key", type="password", value=st.session_state.api_key, placeholder="sk-ant-...")
    st.session_state.api_key = ak
    st.success("✅ AI enhanced") if ak else st.info("📝 Smart fallback mode")

    st.markdown("---")
    st.markdown("<div style='color:#4A5568;font-size:.72rem;text-align:center;'>Built for Hackathon Excellence 🏆<br>Designed with ❤️ for students</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    lang = st.session_state.language

    st.markdown(f"""<div style='text-align:center;padding:2.5rem 1rem 1.2rem;'>
    <div style='font-family:Playfair Display,serif;font-size:3rem;color:#E2E8F0;line-height:1.15;'>
        {get_ui("welcome",lang)}</div>
    <div style='color:#6B46C1;font-size:.95rem;margin-top:.5rem;'>{get_ui("subtitle",lang)}</div>
    </div>""", unsafe_allow_html=True)

    # Quote
    st.markdown(f"""<div class='mm-card mm-purple' style='text-align:center;padding:1.2rem 2rem;'>
    <div style='color:#A78BFA;font-size:1.3rem;margin-bottom:.4rem;'>✨</div>
    <div style='color:#E2E8F0;font-style:italic;font-size:.95rem;'>{get_motivational_quote()}</div>
    </div>""", unsafe_allow_html=True)

    # Metrics
    df    = get_records(7)
    wdata = get_wellness_score(df)
    emo   = st.session_state.current_emotion

    c1,c2,c3,c4 = st.columns(4)
    with c1:
        sc = wdata["score"]
        col = "#4ADE80" if sc>=70 else ("#FBBF24" if sc>=40 else "#F87171")
        st.markdown(f"""<div class='metric-card'><div style='font-size:1.8rem;'>💚</div>
        <div style='font-size:2rem;font-weight:700;color:{col};'>{sc}</div>
        <div style='color:#718096;font-size:.78rem;'>Wellness Score</div>
        <div style='color:#A78BFA;font-size:.73rem;margin-top:.2rem;'>{wdata["label"]}</div></div>""", unsafe_allow_html=True)
    with c2:
        emoji=get_emotion_emoji(emo["emotion"]); color=get_emotion_color(emo["emotion"])
        st.markdown(f"""<div class='metric-card'><div style='font-size:1.8rem;'>{emoji}</div>
        <div style='font-size:1.1rem;font-weight:600;color:{color};'>{emo["emotion"]}</div>
        <div style='color:#718096;font-size:.78rem;'>Current Emotion</div>
        <div style='color:#718096;font-size:.73rem;margin-top:.2rem;'>Conf: {int(emo["confidence"]*100)}%</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='metric-card'><div style='font-size:1.8rem;'>📈</div>
        <div style='font-size:2rem;font-weight:700;color:#A78BFA;'>{len(df)}</div>
        <div style='color:#718096;font-size:.78rem;'>Mood Logs (7d)</div>
        <div style='color:#A78BFA;font-size:.73rem;margin-top:.2rem;'>{wdata["trend"]}</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class='metric-card'><div style='font-size:1.8rem;'>🔥</div>
        <div style='font-size:2rem;font-weight:700;color:#FBBF24;'>{st.session_state.sessions}</div>
        <div style='color:#718096;font-size:.78rem;'>Chat Sessions</div>
        <div style='color:#FBBF24;font-size:.73rem;margin-top:.2rem;'>Keep going!</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    ca, cb = st.columns([2,1])
    with ca: st.plotly_chart(build_mood_chart(df), use_container_width=True, config={"displayModeBar":False})
    with cb: st.plotly_chart(build_emotion_pie(df), use_container_width=True, config={"displayModeBar":False})

    # Feature cards
    st.markdown("<br><h3>✨ Explore MindMate</h3>", unsafe_allow_html=True)
    fc = st.columns(4)
    for col, (icon, title, desc) in zip(fc, [
        ("💬","AI Chat","Empathetic conversations & coping strategies"),
        ("🎮","Stress Games","Breathing, Memory, Mandala & Shooting"),
        ("📊","Mood Tracker","Visualise your emotional journey"),
        ("🧘","Meditation","Guided breathing & relaxation sessions"),
    ]):
        with col:
            st.markdown(f"""<div class='mm-card' style='text-align:center;'>
            <div style='font-size:1.8rem;'>{icon}</div>
            <div style='font-weight:600;color:#E2E8F0;margin-top:.4rem;font-size:.92rem;'>{title}</div>
            <div style='color:#718096;font-size:.78rem;margin-top:.2rem;'>{desc}</div></div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AI CHAT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💬 AI Chat":
    name = st.session_state.get("user_name","Friend")
    st.markdown(f"<div class='sec-title'>💬 Hey {name}! 👋</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Tell me what's on your mind — I'm here to listen, not judge.</div>", unsafe_allow_html=True)

    lang = st.session_state.language

    # Chat history
    if not st.session_state.chat_history:
        st.markdown("""<div class='mm-card' style='text-align:center;padding:2rem;'>
        <div style='font-size:2.5rem;'>👋</div>
        <div style='color:#CBD5E0;margin-top:.5rem;'>Start by telling me how you're feeling today.</div>
        <div style='color:#718096;font-size:.83rem;margin-top:.3rem;'>I'll detect your emotion and offer tailored support.</div>
        </div>""", unsafe_allow_html=True)
    else:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                e = msg.get("emotion","Neutral")
                col = get_emotion_color(e); emj = get_emotion_emoji(e)
                st.markdown(f"""<div style='display:flex;justify-content:flex-end;align-items:flex-end;gap:.5rem;margin:.6rem 0;'>
                <div><div style='text-align:right;margin-bottom:.2rem;'>
                  <span style='background:{col}22;color:{col};padding:.12rem .6rem;border-radius:12px;font-size:.73rem;'>{emj} {e}</span>
                </div><div class='chat-user'>{msg["content"]}</div></div>
                <div style='font-size:1.4rem;'>🧑‍🎓</div></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div style='display:flex;align-items:flex-end;gap:.5rem;margin:.6rem 0;'>
                <div style='font-size:1.4rem;'>🧠</div>
                <div class='chat-ai'>{msg["content"]}</div></div>""", unsafe_allow_html=True)

    if is_emergency(st.session_state.current_emotion):
        st.markdown("""<div class='emer-card'><h4 style='color:#FC8181;margin:0;'>🆘 We're concerned about you</h4>
        <p style='color:#FEB2B2;margin:.4rem 0 0;font-size:.85rem;'>Please visit Emergency Help in the sidebar or call Kiran: 1800-599-0019 (24/7 free).</p></div>""", unsafe_allow_html=True)

    # Input
    st.markdown("<br>", unsafe_allow_html=True)
    ci, cb = st.columns([5,1])
    with ci: user_input = st.text_input("", placeholder=get_ui("placeholder",lang), label_visibility="collapsed", key="chat_in")
    with cb: send = st.button(get_ui("send",lang), use_container_width=True)

    # Suggested prompts
    st.markdown("<div style='color:#4A5568;font-size:.77rem;margin:.4rem 0 .2rem;'>💡 Try:</div>", unsafe_allow_html=True)
    prompts = ["I feel overwhelmed with exams 😰","I can't focus at all today","I'm feeling great today! 😊","I'm totally burnt out"]
    pc = st.columns(4)
    for col, p in zip(pc, prompts):
        with col:
            if st.button(p, key=f"p_{p[:8]}"):
                user_input = p; send = True

    if send and user_input.strip():
        dl = detect_language(user_input)
        if dl in SUPPORTED_LANGUAGES: st.session_state.language = dl
        en = translate_to_english(user_input, dl)
        ed = detect_emotion(en)
        st.session_state.current_emotion = ed
        log_mood(ed["score"], ed["emotion"], en[:80])
        resp = get_ai_response(en, ed, [{"role":m["role"],"content":m["content"]} for m in st.session_state.chat_history], st.session_state.api_key or None)
        if dl != "en": resp = translate_from_english(resp, dl)
        st.session_state.chat_history += [{"role":"user","content":user_input,"emotion":ed["emotion"]},{"role":"assistant","content":resp}]
        st.session_state.sessions += 1
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear conversation"): st.session_state.chat_history=[]; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: VOICE ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎤 Voice Assistant":
    st.markdown("<div class='sec-title'>🎤 Voice Assistant</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Talk to MindMate like a real friend — it listens, understands, and speaks back to you.</div>", unsafe_allow_html=True)

    # Init voice chat history (for mood logging sidebar)
    if "voice_history" not in st.session_state:
        st.session_state.voice_history = []

    # ── How-to banner ──────────────────────────────────────────────────────
    lang_lbl = SUPPORTED_LANGUAGES.get(st.session_state.language, "English")
    st.markdown(f"""
    <div style='display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:.8rem;'>
      <div style='background:rgba(124,58,237,.08);border:1px solid rgba(124,58,237,.2);border-radius:10px;
           padding:.55rem 1rem;font-size:.8rem;color:#A0AEC0;flex:1;'>
        🌐 <b style='color:#A78BFA;'>Language:</b> {lang_lbl} — change in sidebar
      </div>
      <div style='background:rgba(74,222,128,.07);border:1px solid rgba(74,222,128,.2);border-radius:10px;
           padding:.55rem 1rem;font-size:.8rem;color:#A0AEC0;flex:1;'>
        🔊 <b style='color:#4ADE80;'>Voice replies</b> enabled — MindMate will speak back to you!
      </div>
      <div style='background:rgba(251,191,36,.07);border:1px solid rgba(251,191,36,.2);border-radius:10px;
           padding:.55rem 1rem;font-size:.8rem;color:#A0AEC0;flex:1;'>
        🌐 <b style='color:#FBBF24;'>Chrome / Edge only</b> — required for mic + speech
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Main layout ────────────────────────────────────────────────────────
    col_voice, col_info = st.columns([1.6, 1])

    with col_voice:
        # The component handles EVERYTHING: listen → AI → speak
        # It also posts the transcript back via postMessage for mood logging
        transcript = render_voice_component(
            language=st.session_state.language,
            api_key=st.session_state.api_key or ""
        )

    with col_info:
        # ── Usage guide ────────────────────────────────────────────────
        st.markdown("""<div class='mm-card mm-purple' style='padding:1.2rem;'>
        <div style='font-weight:600;color:#E2E8F0;margin-bottom:.6rem;'>How to use</div>
        <div style='color:#A0AEC0;font-size:.82rem;line-height:2;'>
          🎤 Tap the mic button<br>
          👂 Speak naturally<br>
          🤔 MindMate thinks…<br>
          🗣️ MindMate speaks back<br>
          🔁 Keep the conversation going!
        </div>
        </div>""", unsafe_allow_html=True)

        # ── Conversation tips ──────────────────────────────────────────
        st.markdown("""<div class='mm-card' style='padding:1.2rem;'>
        <div style='font-weight:600;color:#E2E8F0;margin-bottom:.6rem;'>💬 Things to say</div>
        <div style='color:#718096;font-size:.8rem;line-height:2;'>
          "I'm not feeling good today"<br>
          "I'm stressed about exams"<br>
          "मुझे बहुत चिंता हो रही है"<br>
          "આજે ઘણું ખરાબ લાગે છે"<br>
          "I can't focus at all"<br>
          "I feel lonely and tired"
        </div>
        </div>""", unsafe_allow_html=True)

        # ── Mood log from voice ────────────────────────────────────────
        if st.session_state.voice_history:
            recent = st.session_state.voice_history[-1]
            emo  = recent.get("emotion", "Neutral")
            emj  = get_emotion_emoji(emo)
            col_ = get_emotion_color(emo)
            st.markdown(f"""<div class='mm-card' style='padding:1rem;'>
            <div style='font-size:.75rem;color:#718096;margin-bottom:.3rem;'>Latest emotion detected</div>
            <div style='display:flex;align-items:center;gap:.5rem;'>
              <span style='font-size:1.5rem;'>{emj}</span>
              <span style='color:{col_};font-weight:600;'>{emo}</span>
            </div>
            </div>""", unsafe_allow_html=True)

        # ── API key reminder ───────────────────────────────────────────
        if not st.session_state.api_key:
            st.markdown("""<div style='background:rgba(251,191,36,.07);border:1px solid rgba(251,191,36,.2);
            border-radius:10px;padding:.75rem 1rem;font-size:.78rem;color:#A0AEC0;'>
            💡 <b style='color:#FBBF24;'>Add API key</b> in sidebar for smarter, more personal responses.
            Without it, a built-in fallback handles conversations — still works great!
            </div>""", unsafe_allow_html=True)

    # ── Mood logging from voice transcript ────────────────────────────────
    if transcript and isinstance(transcript, str) and transcript.strip():
        dl = detect_language(transcript)
        en = translate_to_english(transcript, dl)
        ed = detect_emotion(en)
        st.session_state.current_emotion = ed
        log_mood(ed["score"], ed["emotion"])
        st.session_state.voice_history.append({
            "role": "user", "content": transcript,
            "emotion": ed["emotion"], "source": "voice"
        })
        st.session_state.sessions += 1
        # Rerun to update the emotion card in col_info
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MOOD TRACKER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊 Mood Tracker":
    st.markdown("<div class='sec-title'>📊 Mood Tracker</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Your emotional journey, visualised.</div>", unsafe_allow_html=True)

    days  = st.slider("Show last N days", 1, 30, 7, key="td")
    df    = get_records(days)
    wdata = get_wellness_score(df)

    sc = wdata["score"]
    col = "#4ADE80" if sc>=70 else ("#FBBF24" if sc>=40 else "#F87171")
    st.markdown(f"""<div class='mm-card mm-glow' style='text-align:center;margin-bottom:1.5rem;'>
    <div style='font-size:3.5rem;font-weight:700;color:{col};'>{sc}</div>
    <div style='font-size:1.25rem;color:#E2E8F0;'>{wdata["label"]}</div>
    <div style='color:#718096;margin-top:.2rem;font-size:.85rem;'>Trend: {wdata["trend"]}</div>
    </div>""", unsafe_allow_html=True)
    st.progress(sc/100)

    c1,c2 = st.columns([2,1])
    with c1: st.plotly_chart(build_mood_chart(df), use_container_width=True, config={"displayModeBar":False})
    with c2: st.plotly_chart(build_emotion_pie(df), use_container_width=True, config={"displayModeBar":False})

    if not df.empty:
        st.markdown("### Recent Entries")
        ddf = df[["timestamp","emotion","score"]].copy()
        ddf["timestamp"] = ddf["timestamp"].dt.strftime("%b %d, %H:%M")
        ddf["score"] = ddf["score"].round(2)
        st.dataframe(ddf.tail(10).sort_values("timestamp",ascending=False), use_container_width=True, hide_index=True)

    st.markdown("### ✍️ Log Mood Manually")
    mc1,mc2,mc3 = st.columns([2,2,1])
    with mc1: me = st.selectbox("Emotion",["Positive","Neutral","Stress","Anxiety","Burnout"])
    with mc2: ms = st.slider("Score",-1.0,1.0,0.0,.1,key="ms")
    with mc3:
        st.markdown("<br>",unsafe_allow_html=True)
        if st.button("Log",use_container_width=True): log_mood(ms,me); st.success("✅ Logged!"); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: STRESS RELIEF GAMES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎮 Stress Relief Games":
    st.markdown("<div class='sec-title'>🎮 Stress Relief Games</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Science-backed interactive activities to decompress and refocus.</div>", unsafe_allow_html=True)

    game = st.radio("Choose:", [
        "🌬️ Breathing Exercise",
        "🧠 Memory Match",
        "🎨 Mandala Art Therapy",
        "🎯 Bottle Shooting",
    ], horizontal=True, key="game_sel")

    st.markdown("<br>", unsafe_allow_html=True)

    if   game == "🌬️ Breathing Exercise":  breathing_game()
    elif game == "🧠 Memory Match":         memory_game()
    elif game == "🎨 Mandala Art Therapy":  mandala_art_game()
    elif game == "🎯 Bottle Shooting":      bottle_shooting_game()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MEDITATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🧘 Meditation":
    import streamlit.components.v1 as components

    st.markdown("<div class='sec-title'>🧘 Guided Meditation</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>Set your time, close your eyes, and let MindMate guide you — a gentle bell rings when you're done.</div>", unsafe_allow_html=True)

    # ── Session presets ────────────────────────────────────────────────────
    SESSIONS = {
        "🌿 Body Scan": {
            "color": "#4ADE80",
            "steps": [
                "Close your eyes and take 3 slow, deep breaths.",
                "Feel the weight of your body — let gravity hold you.",
                "Bring attention to your feet. Notice any sensations.",
                "Slowly scan upward — calves, knees, thighs.",
                "Let your belly soften with every exhale.",
                "Notice your chest gently rising and falling.",
                "Relax your shoulders away from your ears.",
                "Let your jaw unclench, your forehead smooth.",
                "You are fully present. Rest here.",
                "Take a final deep breath. Open your eyes slowly. 🙏",
            ]
        },
        "🌊 Ocean Breathing": {
            "color": "#60A5FA",
            "steps": [
                "Imagine yourself on a quiet, peaceful beach.",
                "Hear the waves — slow, steady, endless.",
                "Inhale as a wave rolls in… 1, 2, 3, 4.",
                "Hold at the peak… 1, 2.",
                "Exhale as the wave retreats… 1, 2, 3, 4, 5, 6.",
                "Feel the rhythm. You are the ocean.",
                "Let each breath wash away tension.",
                "Return to natural breath. Stay with the sound of waves. 🌊",
            ]
        },
        "☀️ Gratitude Reset": {
            "color": "#FBBF24",
            "steps": [
                "Take one slow breath and arrive fully here.",
                "Think of ONE thing you are grateful for today.",
                "Feel the warmth of that gratitude in your chest.",
                "Think of ONE person who has supported you.",
                "Send them a silent, heartfelt 'thank you'.",
                "Now bring kindness to yourself — you are doing your best.",
                "Breathe in peace. Breathe out everything else. ☀️",
            ]
        },
        "🌙 Sleep Wind-Down": {
            "color": "#A78BFA",
            "steps": [
                "Lie down comfortably. Let your body be heavy.",
                "Close your eyes. There is nothing you need to do right now.",
                "Breathe in for 4 counts… and out for 8.",
                "With each exhale, feel yourself sinking deeper.",
                "Release your jaw, your hands, your shoulders.",
                "Let go of today. Tomorrow will take care of itself.",
                "You are safe. You are calm. You can rest now. 🌙",
            ]
        },
    }

    # ── UI: choose session + custom time ──────────────────────────────────
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        sel      = st.radio("Choose a session:", list(SESSIONS.keys()), key="med_sel")
        s        = SESSIONS[sel]

        st.markdown("<br>", unsafe_allow_html=True)

        # Custom duration picker
        st.markdown("<div style='color:#A0AEC0;font-size:.85rem;font-weight:600;margin-bottom:.3rem;'>⏱ Set your meditation duration</div>", unsafe_allow_html=True)
        dur_min  = st.slider("Minutes", min_value=1, max_value=60, value=5, step=1, key="med_min")
        dur_sec  = st.slider("Extra seconds", min_value=0, max_value=59, value=0, step=5, key="med_sec")
        total_s  = dur_min * 60 + dur_sec

        # Bell sound selector
        st.markdown("<br>", unsafe_allow_html=True)
        bell_type = st.selectbox("🔔 End bell sound", [
            "🎵 Tibetan Singing Bowl",
            "🔔 Temple Bell (3 rings)",
            "🎶 Soft Chime",
            "📯 Deep Gong",
        ], key="med_bell")

        st.markdown(f"""<div class='mm-card' style='border-color:{s["color"]}30;text-align:center;padding:1rem;margin-top:.5rem;'>
        <div style='font-size:1.6rem;'>{sel.split()[0]}</div>
        <div style='color:{s["color"]};font-weight:600;margin:.3rem 0;'>{sel[2:]}</div>
        <div style='color:#718096;font-size:.82rem;'>{len(s["steps"])} guidance steps &nbsp;•&nbsp; {dur_min}m {dur_sec}s timer</div>
        </div>""", unsafe_allow_html=True)

    with col_right:
        st.markdown("""<div class='mm-card' style='padding:1.2rem;'>
        <div style='font-weight:600;color:#E2E8F0;margin-bottom:.6rem;'>💡 How it works</div>
        <div style='color:#A0AEC0;font-size:.82rem;line-height:2;'>
        ① Set your duration below<br>
        ② Choose your bell sound<br>
        ③ Press Begin & close your eyes<br>
        ④ Guidance steps appear quietly<br>
        ⑤ Bell rings when time is up 🔔<br>
        ⑥ Open your eyes gently
        </div></div>""", unsafe_allow_html=True)

        st.markdown("""<div class='mm-card' style='padding:1.2rem;'>
        <div style='font-weight:600;color:#E2E8F0;margin-bottom:.6rem;'>🔬 Science</div>
        <div style='color:#718096;font-size:.8rem;line-height:1.8;'>
        Even <b style='color:#A78BFA;'>5 minutes</b> of meditation reduces cortisol by up to 25%.
        The bell sound at the end prevents jarring wake-ups, preserving the calm state.
        </div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Build steps JSON for JS ────────────────────────────────────────────
    import json
    steps_json   = json.dumps(s["steps"])
    color        = s["color"]

    # Bell type → parameters for Web Audio API synthesis
    bell_params = {
        "🎵 Tibetan Singing Bowl": {"type":"sine",   "freq":432, "duration":4.0, "rings":1, "decay":3.5},
        "🔔 Temple Bell (3 rings)": {"type":"sine",   "freq":528, "duration":5.0, "rings":3, "decay":1.2},
        "🎶 Soft Chime":           {"type":"triangle","freq":660, "duration":3.0, "rings":2, "decay":1.5},
        "📯 Deep Gong":            {"type":"sine",    "freq":196, "duration":5.0, "rings":1, "decay":4.5},
    }
    bp = bell_params.get(bell_type, bell_params["🎵 Tibetan Singing Bowl"])
    bell_json = json.dumps(bp)

    # ── Meditation HTML5 component ─────────────────────────────────────────
    med_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{
  background:transparent;
  font-family:'Segoe UI',sans-serif;
  display:flex;flex-direction:column;align-items:center;
  gap:14px;padding:16px 10px;
  color:#E2E8F0;
}}

/* ── Ring / orb ── */
#orb-wrap{{position:relative;width:160px;height:160px;display:flex;align-items:center;justify-content:center}}
#orb{{
  width:140px;height:140px;border-radius:50%;
  background:radial-gradient(circle at 40% 35%, {color}44, {color}11);
  border:2px solid {color}55;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:2px;
  box-shadow:0 0 40px {color}22;
  transition:all .5s ease;
}}
#orb.active{{
  box-shadow:0 0 60px {color}44, 0 0 100px {color}22;
  animation:breatheOrb 8s ease-in-out infinite;
}}
#orb.done{{
  background:radial-gradient(circle at 40% 35%,#4ADE8044,#4ADE8011);
  border-color:#4ADE8066;
  box-shadow:0 0 60px #4ADE8044;
  animation:none;
}}
@keyframes breatheOrb{{
  0%,100%{{transform:scale(1);   box-shadow:0 0 40px {color}33}}
  50%{{  transform:scale(1.08); box-shadow:0 0 80px {color}55}}
}}

/* Pulse ring */
#pulse-ring{{
  position:absolute;border-radius:50%;
  width:140px;height:140px;
  border:2px solid {color}33;
  animation:none;
}}
#pulse-ring.active{{animation:pulseRing 8s ease-in-out infinite}}
@keyframes pulseRing{{
  0%,100%{{transform:scale(1);opacity:.5}}
  50%{{transform:scale(1.18);opacity:.1}}
}}

#timer-text{{font-size:2.2rem;font-weight:700;color:#E2E8F0;letter-spacing:.02em}}
#timer-label{{font-size:.72rem;color:#718096;letter-spacing:.06em;text-transform:uppercase}}

/* ── Progress ring ── */
#prog-svg{{position:absolute;top:0;left:0;transform:rotate(-90deg)}}
#prog-circle{{
  fill:none;stroke:{color};stroke-width:3;
  stroke-linecap:round;
  stroke-dasharray:408;stroke-dashoffset:408;
  transition:stroke-dashoffset .9s linear;
}}

/* ── Step card ── */
#step-card{{
  width:100%;max-width:380px;
  background:rgba(255,255,255,.03);
  border:1px solid {color}25;
  border-radius:14px;padding:1rem 1.2rem;
  text-align:center;min-height:60px;
  transition:all .6s ease;
  display:none;
}}
#step-num{{color:{color};font-size:.7rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:.3rem}}
#step-text{{color:#CBD5E0;font-size:.9rem;line-height:1.55;font-style:italic}}

/* ── Buttons ── */
#controls{{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}}
#btnStart{{
  padding:10px 28px;border-radius:10px;border:none;
  background:linear-gradient(135deg,{color}CC,{color}88);
  color:#000;font-size:.9rem;font-weight:700;
  cursor:pointer;transition:all .2s;
}}
#btnStart:hover{{transform:translateY(-1px);box-shadow:0 4px 18px {color}44}}
#btnStop{{
  padding:10px 22px;border-radius:10px;border:none;
  background:rgba(255,255,255,.07);color:#A0AEC0;
  font-size:.85rem;cursor:pointer;display:none;
}}

/* ── Bell animation on finish ── */
#bell-anim{{font-size:3rem;display:none;animation:bellRing .3s ease-in-out infinite alternate}}
@keyframes bellRing{{from{{transform:rotate(-15deg)}} to{{transform:rotate(15deg)}}}}

/* ── Status ── */
#status{{font-size:.78rem;color:#718096;text-align:center}}
</style>
</head>
<body>

<!-- Orb timer -->
<div id="orb-wrap">
  <svg id="prog-svg" width="160" height="160" viewBox="0 0 160 160">
    <circle id="prog-circle" cx="80" cy="80" r="65"/>
  </svg>
  <div id="pulse-ring"></div>
  <div id="orb">
    <div id="timer-text">--:--</div>
    <div id="timer-label">ready</div>
  </div>
</div>

<div id="bell-anim">🔔</div>
<div id="status">Press Begin to start your {dur_min}m {dur_sec}s session</div>

<!-- Guidance step -->
<div id="step-card">
  <div id="step-num">Step 1</div>
  <div id="step-text"></div>
</div>

<!-- Controls -->
<div id="controls">
  <button id="btnStart" onclick="startMed()">🧘 Begin</button>
  <button id="btnStop"  onclick="stopMed()">⏹ Stop</button>
</div>

<script>
/* ════════════════════════════════════════════════════
   CONFIG (injected from Python)
   ════════════════════════════════════════════════════ */
const TOTAL_SEC  = {total_s};
const STEPS      = {steps_json};
const BELL_P     = {bell_json};

/* ════════════════════════════════════════════════════
   STATE
   ════════════════════════════════════════════════════ */
let remaining   = TOTAL_SEC;
let intervalID  = null;
let running     = false;
let stepIdx     = 0;
let stepIntervalID = null;
const CIRCUMFERENCE = 408;   // 2 * π * 65

/* ════════════════════════════════════════════════════
   DOM
   ════════════════════════════════════════════════════ */
const orb        = document.getElementById("orb");
const pulseRing  = document.getElementById("pulse-ring");
const timerText  = document.getElementById("timer-text");
const timerLabel = document.getElementById("timer-label");
const progCircle = document.getElementById("prog-circle");
const stepCard   = document.getElementById("step-card");
const stepNum    = document.getElementById("step-num");
const stepTxt    = document.getElementById("step-text");
const statusEl   = document.getElementById("status");
const bellAnim   = document.getElementById("bell-anim");
const btnStart   = document.getElementById("btnStart");
const btnStop    = document.getElementById("btnStop");

/* ════════════════════════════════════════════════════
   WEB AUDIO — synthesise bell sound (no file needed)
   ════════════════════════════════════════════════════ */
function playBell() {{
  const rings    = BELL_P.rings || 1;
  const interval = BELL_P.rings > 1 ? 1.2 : 0;

  for (let r = 0; r < rings; r++) {{
    setTimeout(() => playSingleBell(r), r * interval * 1000);
  }}
}}

function playSingleBell(ringIndex) {{
  try {{
    const ctx  = new (window.AudioContext || window.webkitAudioContext)();
    const osc  = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.connect(gain);
    gain.connect(ctx.destination);

    // Fundamental tone
    osc.type      = BELL_P.type || "sine";
    osc.frequency.setValueAtTime(BELL_P.freq, ctx.currentTime);

    // Harmonic overtone — makes it sound richer / bell-like
    const osc2  = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.type = "sine";
    osc2.frequency.setValueAtTime(BELL_P.freq * 2.756, ctx.currentTime);  // bell harmonic ratio

    // Volume envelope: sharp attack, long exponential decay
    gain.gain.setValueAtTime(0.001, ctx.currentTime);
    gain.gain.linearRampToValueAtTime(0.55, ctx.currentTime + 0.005);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + BELL_P.decay);

    gain2.gain.setValueAtTime(0.001, ctx.currentTime);
    gain2.gain.linearRampToValueAtTime(0.2, ctx.currentTime + 0.005);
    gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + BELL_P.decay * 0.6);

    const end = ctx.currentTime + BELL_P.duration;
    osc.start(ctx.currentTime);   osc.stop(end);
    osc2.start(ctx.currentTime);  osc2.stop(end);

    // Auto-close audio context after bell fades
    setTimeout(() => ctx.close(), BELL_P.duration * 1000 + 200);
  }} catch(e) {{
    console.warn("Web Audio not available:", e);
  }}
}}

/* ════════════════════════════════════════════════════
   TIMER DISPLAY
   ════════════════════════════════════════════════════ */
function formatTime(s) {{
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return String(m).padStart(2,"0") + ":" + String(sec).padStart(2,"0");
}}

function updateProgress() {{
  const frac   = 1 - (remaining / TOTAL_SEC);
  const offset = CIRCUMFERENCE * (1 - frac);
  progCircle.style.strokeDashoffset = offset;
  timerText.textContent = formatTime(remaining);
}}

/* ════════════════════════════════════════════════════
   GUIDANCE STEPS  (cycle through at even intervals)
   ════════════════════════════════════════════════════ */
function startSteps() {{
  showStep(0);
  const stepInterval = Math.max(10, Math.floor(TOTAL_SEC / STEPS.length));
  stepIntervalID = setInterval(() => {{
    stepIdx = (stepIdx + 1) % STEPS.length;
    showStep(stepIdx);
  }}, stepInterval * 1000);
}}

function showStep(i) {{
  stepCard.style.display = "block";
  stepNum.textContent    = "Step " + (i + 1) + " / " + STEPS.length;
  // Fade animation
  stepCard.style.opacity = "0";
  setTimeout(() => {{
    stepTxt.textContent  = STEPS[i];
    stepCard.style.opacity = "1";
    stepCard.style.transition = "opacity .6s ease";
  }}, 200);
}}

/* ════════════════════════════════════════════════════
   START / STOP / FINISH
   ════════════════════════════════════════════════════ */
function startMed() {{
  if (running) return;
  running   = true;
  remaining = TOTAL_SEC;
  stepIdx   = 0;

  orb.classList.add("active");
  pulseRing.classList.add("active");
  bellAnim.style.display  = "none";
  btnStart.style.display  = "none";
  btnStop.style.display   = "inline-block";
  timerLabel.textContent  = "meditating";
  statusEl.textContent    = "Close your eyes and breathe…";

  updateProgress();
  startSteps();

  intervalID = setInterval(() => {{
    remaining--;
    updateProgress();

    if (remaining <= 0) {{
      finishMed();
    }}
  }}, 1000);
}}

function stopMed() {{
  clearInterval(intervalID);
  clearInterval(stepIntervalID);
  running = false;
  orb.classList.remove("active","done");
  pulseRing.classList.remove("active");
  stepCard.style.display  = "none";
  bellAnim.style.display  = "none";
  btnStart.style.display  = "inline-block";
  btnStop.style.display   = "none";
  timerLabel.textContent  = "stopped";
  statusEl.textContent    = "Session stopped. Press Begin to restart.";
  remaining = TOTAL_SEC;
  updateProgress();
  timerText.textContent   = formatTime(TOTAL_SEC);
  progCircle.style.strokeDashoffset = CIRCUMFERENCE;
}}

function finishMed() {{
  clearInterval(intervalID);
  clearInterval(stepIntervalID);
  running = false;

  // Visual finish
  orb.classList.remove("active");
  orb.classList.add("done");
  pulseRing.classList.remove("active");
  orb.textContent = "";
  timerText.textContent  = "00:00";
  timerLabel.textContent = "complete ✓";
  progCircle.style.strokeDashoffset = 0;

  // Show bell animation
  bellAnim.style.display = "block";
  setTimeout(() => {{ bellAnim.style.animation = "none"; bellAnim.textContent = "🙏"; }}, 3000);

  // Play bell sound
  playBell();

  // Update step card to final message
  stepNum.textContent = "Session Complete";
  stepTxt.textContent = "Carry this calm with you. Well done. 🙏";
  stepCard.style.opacity = "1";

  statusEl.textContent = "✨ Your session is complete. The bell has rung.";
  btnStop.style.display  = "none";
  btnStart.textContent   = "🧘 Begin Again";
  btnStart.style.display = "inline-block";
}}

/* ── Init display ── */
timerText.textContent = formatTime(TOTAL_SEC);
progCircle.style.strokeDashoffset = CIRCUMFERENCE;
</script>
</body>
</html>"""

    # Render the meditation component (full height)
    components.html(med_html, height=520, scrolling=False)

    # ── Tip strip below component ──────────────────────────────────────────
    st.markdown(f"""
    <div style='display:flex;gap:.8rem;flex-wrap:wrap;margin-top:.5rem;'>
      <div style='background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);
           border-radius:10px;padding:.55rem 1rem;font-size:.78rem;color:#718096;flex:1;'>
        🔔 <b style='color:#E2E8F0;'>{bell_type}</b> will ring when time ends
      </div>
      <div style='background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);
           border-radius:10px;padding:.55rem 1rem;font-size:.78rem;color:#718096;flex:1;'>
        ⏱ Duration: <b style='color:#E2E8F0;'>{dur_min} min {dur_sec} sec</b> &nbsp;|&nbsp; Session: <b style='color:{color};'>{sel}</b>
      </div>
      <div style='background:rgba(167,139,250,.07);border:1px solid rgba(167,139,250,.2);
           border-radius:10px;padding:.55rem 1rem;font-size:.78rem;color:#A0AEC0;flex:1;'>
        💡 Sound uses your browser — keep volume on
      </div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: EMERGENCY HELP
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🆘 Emergency Help":
    st.markdown("<div class='sec-title'>🆘 Emergency Support</div>", unsafe_allow_html=True)
    st.markdown("<div class='sec-sub'>You are not alone. Help is always available.</div>", unsafe_allow_html=True)

    st.markdown(f"""<div style='background:linear-gradient(135deg,rgba(124,58,237,.12),rgba(167,139,250,.08));
    border:2px solid rgba(124,58,237,.3);border-radius:20px;padding:2rem;text-align:center;margin-bottom:1.5rem;'>
    <div style='font-size:2.5rem;'>💙</div>
    <h2 style='color:#A78BFA;'>You Matter</h2>
    <p style='color:#CBD5E0;font-size:.95rem;'>"{get_safety_message()}"</p></div>""", unsafe_allow_html=True)

    st.markdown("### 📞 Crisis Helplines (India)")
    hls = get_helplines()
    c1,c2 = st.columns(2)
    for i,h in enumerate(hls):
        with (c1 if i%2==0 else c2):
            st.markdown(f"""<div class='emer-card'><div style='display:flex;align-items:center;gap:.75rem;'>
            <span style='font-size:1.5rem;'>{h["emoji"]}</span>
            <div><div style='font-weight:600;color:#FEB2B2;'>{h["name"]}</div>
            <div style='font-size:1.25rem;font-weight:700;color:white;font-family:monospace;'>{h["number"]}</div>
            <div style='color:#FC8181;font-size:.77rem;'>{h["hours"]}</div></div></div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🌿 Immediate Coping Steps")
    for num,title,desc in [
        ("1","Tell someone","Text or call one trusted person right now. You don't need to explain everything."),
        ("2","Ground yourself","Name 5 things you can see. Breathe slowly. You are safe in this moment."),
        ("3","Step away","Move to a different room or go outside for 2 minutes. Physical movement breaks the spiral."),
        ("4","Avoid isolation","Being alone amplifies crisis feelings. Go somewhere with other people."),
        ("5","Call a helpline","Trained counselors are available 24/7. You don't need to be 'bad enough' to call."),
    ]:
        st.markdown(f"""<div class='mm-card' style='display:flex;gap:1rem;align-items:flex-start;'>
        <div style='background:rgba(124,58,237,.15);color:#A78BFA;font-weight:700;border-radius:50%;
             width:2rem;height:2rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;'>{num}</div>
        <div><div style='font-weight:600;color:#E2E8F0;'>{title}</div>
        <div style='color:#A0AEC0;font-size:.87rem;margin-top:.15rem;'>{desc}</div></div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.info("💡 MindMate AI is a supportive tool, not a replacement for professional mental health care. If in immediate danger, call emergency services (112) or go to your nearest hospital.")

