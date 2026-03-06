"""
modules/games.py
4 stress-relief mini-games embedded in Streamlit.
  1. Breathing Exercise (4-7-8 technique)
  2. Memory Match (emoji pairs)
  3. Mandala Art / Color Filling (interactive HTML5 Canvas)
  4. Bottle Shooting (Easy & Medium levels, HTML5 Canvas)
"""
import streamlit as st
import streamlit.components.v1 as components
import random, time


# ══════════════════════════════════════════════════════════
# GAME 1 — Breathing Exercise
# ══════════════════════════════════════════════════════════
def breathing_game():
    st.markdown("""<div style='text-align:center;padding:.5rem'>
    <h3 style='color:#A78BFA;'>🌬️ 4-7-8 Breathing Exercise</h3>
    <p style='color:#A0AEC0;'>Activates your parasympathetic nervous system — your body's built-in calm switch.</p>
    </div>""", unsafe_allow_html=True)

    rounds = st.slider("Rounds", 1, 5, 3, key="br_rounds")
    phases = [("Inhale 🫁", 4, "#4ADE80", "inhale"),
              ("Hold ⏸️",   7, "#FBBF24", "hold"),
              ("Exhale 💨", 8, "#60A5FA", "exhale")]

    if st.button("▶️ Start Breathing", use_container_width=True, key="br_start"):
        prog = st.progress(0)
        box  = st.empty()
        total = rounds * sum(p[1] for p in phases)
        done  = 0
        for r in range(rounds):
            for label, dur, color, _ in phases:
                for i in range(dur):
                    box.markdown(f"""
                    <div style='text-align:center;background:rgba(255,255,255,0.04);border-radius:20px;
                         padding:2.5rem;border:2px solid {color}40;'>
                      <h2 style='color:{color};font-size:2rem;'>{label}</h2>
                      <div style='font-size:5rem;font-weight:800;color:white;line-height:1;'>{dur-i}</div>
                      <p style='color:#718096;margin-top:.5rem;'>Round {r+1} of {rounds}</p>
                    </div>""", unsafe_allow_html=True)
                    done += 1
                    prog.progress(done / total)
                    time.sleep(1)
        box.markdown("""<div style='text-align:center;background:rgba(74,222,128,.08);border-radius:20px;
             padding:2.5rem;border:2px solid #4ADE8040;'>
          <div style='font-size:3rem;'>✨</div>
          <h2 style='color:#4ADE80;'>Exercise complete!</h2>
          <p style='color:#A0AEC0;'>Notice the calm. This effect lasts for hours.</p>
        </div>""", unsafe_allow_html=True)
        prog.progress(1.0)


# ══════════════════════════════════════════════════════════
# GAME 2 — Memory Match
# ══════════════════════════════════════════════════════════
def memory_game():
    st.markdown("""<div style='text-align:center;'>
    <h3 style='color:#A78BFA;'>🧠 Memory Match</h3>
    <p style='color:#A0AEC0;'>Find all matching pairs. Trains focus and distracts from stress.</p>
    </div>""", unsafe_allow_html=True)

    EMOJIS = ["🌸","🌟","🦋","🌈","🍀","🌙","☀️","🌺"]

    col_ctrl, _ = st.columns([1, 3])
    with col_ctrl:
        new_game = st.button("🔄 New Game", key="mem_new")

    if "mem_board" not in st.session_state or new_game:
        pairs = EMOJIS * 2; random.shuffle(pairs)
        st.session_state.mem_board   = pairs
        st.session_state.mem_flip    = [False]*16
        st.session_state.mem_match   = [False]*16
        st.session_state.mem_first   = None
        st.session_state.mem_moves   = 0
        st.session_state.mem_unflip  = None
        if new_game: st.rerun()

    board, flip, match = st.session_state.mem_board, st.session_state.mem_flip, st.session_state.mem_match

    # Unflip pending
    if st.session_state.mem_unflip:
        a,b = st.session_state.mem_unflip
        flip[a] = flip[b] = False
        st.session_state.mem_unflip = None

    cols = st.columns(4)
    for i in range(16):
        with cols[i % 4]:
            if match[i]:
                st.markdown(f"<div style='text-align:center;font-size:2rem;padding:.6rem;background:rgba(74,222,128,.15);border-radius:10px;margin:3px;border:1px solid #4ADE8040;'>{board[i]}</div>", unsafe_allow_html=True)
            elif flip[i]:
                st.markdown(f"<div style='text-align:center;font-size:2rem;padding:.6rem;background:rgba(167,139,250,.15);border-radius:10px;margin:3px;border:1px solid #A78BFA40;'>{board[i]}</div>", unsafe_allow_html=True)
            else:
                if st.button("❓", key=f"m{i}", use_container_width=True):
                    _mem_click(i)

    matched_count = sum(match)//2
    st.markdown(f"<p style='text-align:center;color:#A0AEC0;margin-top:.5rem;'>Moves: <b>{st.session_state.mem_moves}</b> &nbsp;|&nbsp; Matched: <b>{matched_count}/8</b></p>", unsafe_allow_html=True)
    if all(match):
        st.balloons()
        st.success(f"🎉 All matched in {st.session_state.mem_moves} moves! Excellent focus!")

def _mem_click(idx):
    flip, match = st.session_state.mem_flip, st.session_state.mem_match
    if flip[idx] or match[idx]: return
    flip[idx] = True
    if st.session_state.mem_first is None:
        st.session_state.mem_first = idx
    else:
        first = st.session_state.mem_first
        st.session_state.mem_moves += 1
        if st.session_state.mem_board[first] == st.session_state.mem_board[idx] and first != idx:
            match[first] = match[idx] = True
        else:
            st.session_state.mem_unflip = (first, idx)
        st.session_state.mem_first = None
    st.rerun()


# ══════════════════════════════════════════════════════════
# GAME 3 — Mandala Art / Color Filling
# ══════════════════════════════════════════════════════════
def mandala_art_game():
    st.markdown("""<div style='text-align:center;'>
    <h3 style='color:#A78BFA;'>🎨 Mandala Color Therapy</h3>
    <p style='color:#A0AEC0;'>Pick a mandala design, choose colors, and paint — your work is never reset when you change colors.</p>
    </div>""", unsafe_allow_html=True)

    # The entire game lives inside ONE self-contained HTML component.
    # Color picker, design selector, canvas and fills state all live inside JS —
    # so Streamlit re-renders never wipe the painted artwork.
    mandala_html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:transparent;font-family:'Segoe UI',sans-serif;
     display:flex;flex-direction:column;align-items:center;gap:10px;padding:12px 8px}

/* ── top controls ── */
#controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:center;width:100%}

label{color:#A0AEC0;font-size:.78rem;font-weight:600;letter-spacing:.04em;text-transform:uppercase}

select{background:#12122A;color:#E2E8F0;border:1px solid rgba(124,58,237,.4);
       border-radius:8px;padding:5px 10px;font-size:.8rem;cursor:pointer;outline:none}

#colorPicker{width:44px;height:38px;border-radius:8px;border:2px solid rgba(124,58,237,.5);
             cursor:pointer;background:none;padding:2px}

/* ── palette swatches ── */
#palette{display:flex;gap:5px;flex-wrap:wrap;justify-content:center}
.swatch{width:26px;height:26px;border-radius:6px;cursor:pointer;border:2px solid transparent;
        transition:transform .15s,border-color .15s;flex-shrink:0}
.swatch:hover{transform:scale(1.18)}
.swatch.active{border-color:#fff;transform:scale(1.18)}

canvas{border-radius:14px;cursor:crosshair;background:#08081A;
       border:1px solid rgba(124,58,237,.35);max-width:100%}

/* ── bottom bar ── */
#bar{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}
button{padding:6px 15px;border-radius:8px;border:none;cursor:pointer;
       font-size:.78rem;font-weight:700;transition:opacity .15s}
button:hover{opacity:.85}
#bReset{background:linear-gradient(135deg,#7C3AED,#5B21B6);color:#fff}
#bDl   {background:linear-gradient(135deg,#276749,#22543D);color:#fff}
#bUndo {background:rgba(255,255,255,.08);color:#E2E8F0}

#colorLabel{color:#A0AEC0;font-size:.75rem;margin-top:2px;text-align:center}
</style>
</head>
<body>

<!-- Design selector -->
<div id="controls">
  <label>Design:</label>
  <select id="designSel" onchange="changeDesign()">
    <option value="lotus">🌸 Lotus Bloom</option>
    <option value="sunburst">☀️ Sunburst</option>
    <option value="geometric">🔷 Geometric</option>
    <option value="celtic">🌀 Celtic Spiral</option>
  </select>
  <label style="margin-left:6px">Color:</label>
  <input type="color" id="colorPicker" value="#7C3AED" oninput="setColor(this.value)">
</div>

<!-- Quick palette -->
<div id="palette"></div>
<div id="colorLabel">Active: <span id="colorHex">#7C3AED</span></div>

<!-- Canvas -->
<canvas id="c" width="440" height="440"></canvas>

<!-- Buttons -->
<div id="bar">
  <button id="bUndo"  onclick="undo()">↩ Undo</button>
  <button id="bReset" onclick="resetCanvas()">🔄 New Canvas</button>
  <button id="bDl"    onclick="download()">💾 Save PNG</button>
</div>

<script>
/* ══════════════════════════════════════════════════════
   STATE — lives entirely in JS, never wiped by Streamlit
   ══════════════════════════════════════════════════════ */
const canvas = document.getElementById("c");
const ctx    = canvas.getContext("2d");
const W = canvas.width, H = canvas.height, CX = W/2, CY = H/2;

let currentColor = "#7C3AED";
let currentDesign = "lotus";
let fills = {};          // sectionId → fillColor
let history = [];        // stack of fills snapshots for undo
let sections = [];       // [{id, path, stroke}]

/* ── Palette colours ── */
const PALETTE = [
  "#F87171","#FB923C","#FBBF24","#A3E635","#4ADE80",
  "#34D399","#22D3EE","#60A5FA","#818CF8","#A78BFA",
  "#E879F9","#F472B6","#FFFFFF","#94A3B8","#1E293B"
];

function buildPalette(){
  const el = document.getElementById("palette");
  el.innerHTML = "";
  PALETTE.forEach(c=>{
    const d = document.createElement("div");
    d.className = "swatch" + (c===currentColor?" active":"");
    d.style.background = c;
    d.title = c;
    d.onclick = ()=>setColor(c);
    el.appendChild(d);
  });
}

function setColor(c){
  currentColor = c;
  document.getElementById("colorPicker").value = c;
  document.getElementById("colorHex").textContent = c;
  document.querySelectorAll(".swatch").forEach(s=>{
    s.classList.toggle("active", s.style.background===hexToRgbStr(c)||s.title===c);
  });
}

function hexToRgbStr(hex){
  const r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);
  return `rgb(${r}, ${g}, ${b})`;
}

/* ══════════════════════════════════════════════════════
   DESIGN BUILDERS
   ══════════════════════════════════════════════════════ */
function buildDesign(name){
  sections = [];
  if(name==="lotus")    buildLotus();
  else if(name==="sunburst")  buildSunburst();
  else if(name==="geometric") buildGeometric();
  else if(name==="celtic")    buildCeltic();
}

/* Helper: annular sector */
function annularSector(id, r1, r2, a1, a2, stroke){
  const p = new Path2D();
  p.arc(CX,CY,r2,a1,a2);
  p.arc(CX,CY,r1,a2,a1,true);
  p.closePath();
  sections.push({id,path:p,stroke:stroke||"rgba(167,139,250,0.5)"});
}

/* Helper: full circle */
function circle(id,r,stroke){
  const p=new Path2D(); p.arc(CX,CY,r,0,Math.PI*2);
  sections.push({id,path:p,stroke:stroke||"rgba(167,139,250,0.5)"});
}

/* ── DESIGN 1: Lotus Bloom ── */
function buildLotus(){
  // centre
  circle("c0",22,"rgba(249,168,212,0.7)");
  // ring 1: 8 inner petals
  const s1=Math.PI*2/8;
  for(let i=0;i<8;i++) annularSector(`p1_${i}`,24,68,i*s1-0.05,(i+1)*s1+0.05,"rgba(167,139,250,0.6)");
  // ring 2: 12 petals
  const s2=Math.PI*2/12;
  for(let i=0;i<12;i++) annularSector(`p2_${i}`,70,115,i*s2,(i+1)*s2,"rgba(96,165,250,0.55)");
  // ring 3: 16 petals
  const s3=Math.PI*2/16;
  for(let i=0;i<16;i++) annularSector(`p3_${i}`,117,158,i*s3,(i+1)*s3,"rgba(74,222,128,0.5)");
  // ring 4: 20 petals
  const s4=Math.PI*2/20;
  for(let i=0;i<20;i++) annularSector(`p4_${i}`,160,196,i*s4,(i+1)*s4,"rgba(251,191,36,0.5)");
  // outer ring: 8 large petals
  const s5=Math.PI*2/8;
  for(let i=0;i<8;i++) annularSector(`p5_${i}`,198,215,i*s5,(i+1)*s5,"rgba(244,114,182,0.55)");
}

/* ── DESIGN 2: Sunburst ── */
function buildSunburst(){
  circle("sc",28,"rgba(251,191,36,0.8)");
  // 3 dense rings
  for(let ring=0;ring<4;ring++){
    const n=[6,10,14,18][ring];
    const r1=[30,70,112,155][ring];
    const r2=[68,110,153,195][ring];
    const strokes=["rgba(251,191,36,0.7)","rgba(251,146,60,0.65)","rgba(248,113,113,0.6)","rgba(244,114,182,0.55)"];
    const step=Math.PI*2/n;
    for(let i=0;i<n;i++) annularSector(`s${ring}_${i}`,r1,r2,i*step,(i+1)*step,strokes[ring]);
  }
  // alternating small notch ring
  const ns=Math.PI*2/36;
  for(let i=0;i<36;i++) annularSector(`sn_${i}`,197,213,i*ns,(i+1)*ns,"rgba(253,224,71,0.5)");
}

/* ── DESIGN 3: Geometric ── */
function buildGeometric(){
  circle("gc",24,"rgba(96,165,250,0.8)");
  // hexagonal-feel rings
  const configs=[
    {n:6, r1:26,r2:72, stroke:"rgba(96,165,250,0.65)"},
    {n:6, r1:74,r2:118,stroke:"rgba(129,140,248,0.6)"},
    {n:12,r1:120,r2:160,stroke:"rgba(167,139,250,0.55)"},
    {n:6, r1:162,r2:196,stroke:"rgba(192,132,252,0.55)"},
    {n:12,r1:198,r2:215,stroke:"rgba(216,180,254,0.5)"},
  ];
  configs.forEach((c,ci)=>{
    const step=Math.PI*2/c.n;
    const offset=ci%2===0?0:step/2;
    for(let i=0;i<c.n;i++) annularSector(`g${ci}_${i}`,c.r1,c.r2,offset+i*step,offset+(i+1)*step,c.stroke);
  });
}

/* ── DESIGN 4: Celtic Spiral ── */
function buildCeltic(){
  circle("cc",20,"rgba(52,211,153,0.8)");
  // interlocking feel via offset rings
  const defs=[
    {n:4, r1:22,r2:60, stroke:"rgba(52,211,153,0.7)",  off:0},
    {n:8, r1:62,r2:100,stroke:"rgba(34,211,238,0.65)", off:Math.PI/8},
    {n:4, r1:102,r2:140,stroke:"rgba(96,165,250,0.6)", off:Math.PI/4},
    {n:8, r1:142,r2:178,stroke:"rgba(129,140,248,0.55)",off:Math.PI/8},
    {n:16,r1:180,r2:215,stroke:"rgba(167,139,250,0.5)", off:0},
  ];
  defs.forEach((d,di)=>{
    const step=Math.PI*2/d.n;
    for(let i=0;i<d.n;i++) annularSector(`k${di}_${i}`,d.r1,d.r2,d.off+i*step,d.off+(i+1)*step,d.stroke);
  });
}

/* ══════════════════════════════════════════════════════
   DRAWING
   ══════════════════════════════════════════════════════ */
function drawDecorations(){
  // radial glow
  const g=ctx.createRadialGradient(CX,CY,0,CX,CY,220);
  g.addColorStop(0,"rgba(124,58,237,0.07)");
  g.addColorStop(1,"rgba(0,0,0,0)");
  ctx.fillStyle=g; ctx.fillRect(0,0,W,H);

  // outer dot ring (design-specific colors)
  const dotColors={"lotus":"rgba(244,114,182,0.5)","sunburst":"rgba(251,191,36,0.5)",
                   "geometric":"rgba(96,165,250,0.5)","celtic":"rgba(52,211,153,0.5)"};
  ctx.fillStyle=dotColors[currentDesign]||"rgba(167,139,250,0.5)";
  for(let i=0;i<28;i++){
    const a=i*(Math.PI*2/28);
    ctx.beginPath(); ctx.arc(CX+207*Math.cos(a),CY+207*Math.sin(a),2.2,0,Math.PI*2); ctx.fill();
  }
  // outer circle
  ctx.beginPath(); ctx.arc(CX,CY,216,0,Math.PI*2);
  ctx.strokeStyle=dotColors[currentDesign]||"rgba(167,139,250,0.3)";
  ctx.lineWidth=1; ctx.stroke();
}

function draw(){
  ctx.clearRect(0,0,W,H);
  drawDecorations();
  sections.forEach(s=>{
    ctx.save();
    ctx.fillStyle = fills[s.id] || "rgba(255,255,255,0.025)";
    ctx.fill(s.path);
    ctx.strokeStyle = s.stroke;
    ctx.lineWidth = 1.3;
    ctx.stroke(s.path);
    ctx.restore();
  });
}

/* ══════════════════════════════════════════════════════
   INTERACTION
   ══════════════════════════════════════════════════════ */
canvas.addEventListener("click", e=>{
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const mx = (e.clientX - rect.left) * scaleX;
  const my = (e.clientY - rect.top)  * scaleY;

  for(let i=sections.length-1;i>=0;i--){
    if(ctx.isPointInPath(sections[i].path, mx, my)){
      // push undo snapshot
      history.push({...fills});
      fills[sections[i].id] = currentColor;
      draw();
      break;
    }
  }
});

function undo(){
  if(history.length===0) return;
  fills = history.pop();
  draw();
}

function resetCanvas(){
  history.push({...fills});
  fills = {};
  draw();
}

function download(){
  // render on white background for PNG
  const tmp = document.createElement("canvas");
  tmp.width=W; tmp.height=H;
  const tc=tmp.getContext("2d");
  tc.fillStyle="#08081A"; tc.fillRect(0,0,W,H);
  tc.drawImage(canvas,0,0);
  const a=document.createElement("a");
  a.download="mindmate_mandala.png"; a.href=tmp.toDataURL(); a.click();
}

function changeDesign(){
  const sel = document.getElementById("designSel").value;
  if(sel===currentDesign) return;
  // save undo point, clear fills, rebuild
  history.push({...fills});
  fills = {};
  currentDesign = sel;
  buildDesign(sel);
  draw();
}

/* ── Init ── */
buildPalette();
buildDesign("lotus");
draw();
</script>
</body>
</html>"""

    components.html(mandala_html, height=620, scrolling=False)

    st.markdown("""
    <div style='background:rgba(167,139,250,.08);border:1px solid rgba(167,139,250,.2);
         border-radius:10px;padding:.75rem 1rem;font-size:.83rem;color:#A0AEC0;margin-top:.5rem;'>
    🧠 <b style='color:#A78BFA;'>Art Therapy Science:</b> Coloring mandalas engages the frontal lobe,
    triggering deep focus and calm. Studies show it reduces anxiety as effectively as mindfulness meditation.
    &nbsp;|&nbsp; 🎨 Color changes <b>never</b> reset your painted artwork — use Undo to step back, New Canvas to start fresh.
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# GAME 4 — Bottle Shooting (Easy & Medium)
# ══════════════════════════════════════════════════════════
def bottle_shooting_game():
    st.markdown("""<div style='text-align:center;'>
    <h3 style='color:#A78BFA;'>🎯 Bottle Shooting</h3>
    <p style='color:#A0AEC0;'>Click the bottles before they escape! Release stress through action & focus.</p>
    </div>""", unsafe_allow_html=True)

    level = st.radio("Select Level:", ["🟢 Easy", "🟡 Medium"], horizontal=True, key="bottle_level")
    is_easy = "Easy" in level

    # Config per level
    speed       = 1.2 if is_easy else 2.2
    spawn_rate  = 120 if is_easy else 70   # frames between spawns
    bottles_cfg = 5   if is_easy else 7
    time_limit  = 60  if is_easy else 45

    level_color = "#4ADE80" if is_easy else "#FBBF24"
    level_label = "Easy" if is_easy else "Medium"

    st.markdown(f"""<div style='display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:.75rem;'>
    <span style='background:rgba(255,255,255,.05);padding:.4rem .9rem;border-radius:8px;color:{level_color};font-size:.82rem;'>⚡ Speed: {"Slow" if is_easy else "Fast"}</span>
    <span style='background:rgba(255,255,255,.05);padding:.4rem .9rem;border-radius:8px;color:#A0AEC0;font-size:.82rem;'>🍾 Bottles: {bottles_cfg} max</span>
    <span style='background:rgba(255,255,255,.05);padding:.4rem .9rem;border-radius:8px;color:#A0AEC0;font-size:.82rem;'>⏱ Time: {time_limit}s</span>
    </div>""", unsafe_allow_html=True)

    game_html = f"""
<!DOCTYPE html><html><head><meta charset="utf-8"/>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;display:flex;flex-direction:column;align-items:center;gap:10px;padding:10px;font-family:'Segoe UI',sans-serif}}
canvas{{border-radius:14px;cursor:crosshair;background:#0D1117;border:2px solid {level_color}30;display:block}}
#hud{{display:flex;gap:16px;align-items:center;width:500px;max-width:100%;justify-content:space-between}}
.stat{{background:rgba(255,255,255,.05);padding:.4rem .9rem;border-radius:8px;font-size:.82rem;color:#E2E8F0;font-weight:600}}
.stat span{{color:{level_color}}}
#overlay{{position:absolute;top:0;left:0;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;background:rgba(0,0,0,.75);border-radius:14px}}
#overlay h2{{color:#E2E8F0;font-size:1.6rem;margin-bottom:.5rem}}
#overlay p{{color:#A0AEC0;font-size:.9rem;margin-bottom:1.2rem}}
#start-btn{{padding:10px 28px;border-radius:10px;border:none;background:linear-gradient(135deg,{level_color},{level_color}AA);color:#000;font-size:1rem;font-weight:700;cursor:pointer}}
#wrap{{position:relative;width:500px;max-width:100%}}
</style></head><body>
<div id="hud">
  <div class="stat">🎯 Score: <span id="score">0</span></div>
  <div class="stat">💔 Missed: <span id="missed">0</span></div>
  <div class="stat">⏱ Time: <span id="timer">{time_limit}</span>s</div>
  <div class="stat">Level: <span>{level_label}</span></div>
</div>
<div id="wrap">
  <canvas id="c" width="500" height="380"></canvas>
  <div id="overlay">
    <h2>🍾 Bottle Shooting</h2>
    <p>Click bottles before they escape! {level_label} mode.</p>
    <button id="start-btn" onclick="startGame()">▶ Start Game</button>
  </div>
</div>

<script>
const canvas=document.getElementById("c"),ctx=canvas.getContext("2d");
const W=canvas.width,H=canvas.height;
let bottles=[],score=0,missed=0,frame=0,timeLeft={time_limit},running=false,timerID=null,animID=null;
const SPEED={speed},SPAWN={spawn_rate},MAX_B={bottles_cfg};
const LEVEL="{level_label}";

// Bottle shapes: colour palettes per level
const COLORS_EASY  =["#4ADE80","#60A5FA","#F472B6","#FBBF24","#A78BFA","#34D399"];
const COLORS_MED   =["#EF4444","#F97316","#FBBF24","#06B6D4","#8B5CF6","#EC4899"];
const COLORS = LEVEL==="Easy"?COLORS_EASY:COLORS_MED;

// Particle system
let particles=[];

function spawnBottle(){{
  if(bottles.length>=MAX_B) return;
  const x=60+Math.random()*(W-120);
  const color=COLORS[Math.floor(Math.random()*COLORS.length)];
  const speedVar=SPEED*(0.8+Math.random()*0.5);
  // Wiggle for medium
  const wiggle=LEVEL==="Medium"?{{amp:0.6+Math.random()*0.6,freq:0.03+Math.random()*0.02,phase:Math.random()*Math.PI*2}}:null;
  bottles.push({{x,y:-60,w:30,h:55,color,speed:speedVar,wiggle,baseX:x,angle:0,hp:1}});
}}

function drawBottle(b){{
  ctx.save();
  ctx.translate(b.x,b.y);
  // Shadow glow
  ctx.shadowColor=b.color;
  ctx.shadowBlur=12;
  // Body
  ctx.fillStyle=b.color+"CC";
  ctx.beginPath();
  ctx.roundRect(-b.w/2,0,b.w,b.h,6);
  ctx.fill();
  // Neck
  ctx.fillStyle=b.color+"EE";
  ctx.beginPath();
  ctx.roundRect(-b.w/4,-18,b.w/2,20,4);
  ctx.fill();
  // Cap
  ctx.fillStyle="#E2E8F0";
  ctx.beginPath();
  ctx.roundRect(-b.w/4-2,-24,b.w/2+4,8,3);
  ctx.fill();
  // Shine
  ctx.fillStyle="rgba(255,255,255,0.25)";
  ctx.beginPath();
  ctx.roundRect(-b.w/2+4,4,8,b.h-8,3);
  ctx.fill();
  ctx.shadowBlur=0;
  ctx.restore();
}}

function spawnParticles(x,y,color){{
  for(let i=0;i<14;i++){{
    const angle=Math.random()*Math.PI*2;
    const speed=2+Math.random()*5;
    particles.push({{x,y,vx:Math.cos(angle)*speed,vy:Math.sin(angle)*speed,
      color,alpha:1,life:30+Math.random()*20,size:3+Math.random()*5}});
  }}
}}

function drawParticles(){{
  particles=particles.filter(p=>p.life>0);
  particles.forEach(p=>{{
    p.x+=p.vx;p.y+=p.vy;p.vy+=0.15;p.life--;p.alpha=p.life/50;
    ctx.save();ctx.globalAlpha=p.alpha;
    ctx.fillStyle=p.color;
    ctx.shadowColor=p.color;ctx.shadowBlur=6;
    ctx.beginPath();ctx.arc(p.x,p.y,p.size,0,Math.PI*2);ctx.fill();
    ctx.restore();
  }});
}}

function drawBackground(){{
  // Starfield
  ctx.fillStyle="rgba(255,255,255,0.03)";
  for(let i=0;i<40;i++){{
    // deterministic pseudo-random using frame
    const px=(Math.sin(i*127.1)*43758)%1*W;
    const py=(Math.sin(i*311.7)*43758)%1*H;
    ctx.beginPath();ctx.arc(Math.abs(px),Math.abs(py),1,0,Math.PI*2);ctx.fill();
  }}
  // Ground shelf
  ctx.fillStyle="rgba(124,58,237,0.08)";
  ctx.fillRect(0,H-20,W,20);
  ctx.strokeStyle="rgba(124,58,237,0.3)";
  ctx.lineWidth=1;
  ctx.beginPath();ctx.moveTo(0,H-20);ctx.lineTo(W,H-20);ctx.stroke();
}}

function gameLoop(){{
  ctx.clearRect(0,0,W,H);
  drawBackground();
  frame++;
  if(frame%SPAWN===0) spawnBottle();

  bottles=bottles.filter(b=>{{
    // Wiggle
    if(b.wiggle){{ b.x=b.baseX+Math.sin(frame*b.wiggle.freq+b.wiggle.phase)*30*b.wiggle.amp; }}
    b.y+=b.speed;
    drawBottle(b);
    if(b.y>H){{ missed++;document.getElementById("missed").textContent=missed;return false; }}
    return true;
  }});

  drawParticles();

  // Miss indicator
  if(missed>=5){{
    ctx.fillStyle="rgba(239,68,68,0.15)";
    ctx.fillRect(0,0,W,H);
  }}

  animID=requestAnimationFrame(gameLoop);
}}

canvas.addEventListener("click",e=>{{
  if(!running) return;
  const rect=canvas.getBoundingClientRect();
  const scaleX=canvas.width/rect.width,scaleY=canvas.height/rect.height;
  const mx=(e.clientX-rect.left)*scaleX,my=(e.clientY-rect.top)*scaleY;
  for(let i=bottles.length-1;i>=0;i--){{
    const b=bottles[i];
    if(mx>=b.x-b.w/2&&mx<=b.x+b.w/2&&my>=b.y&&my<=b.y+b.h){{
      spawnParticles(b.x,b.y+b.h/2,b.color);
      bottles.splice(i,1);
      score++;
      document.getElementById("score").textContent=score;
      break;
    }}
  }}
}});

function startGame(){{
  score=0;missed=0;frame=0;timeLeft={time_limit};bottles=[];particles=[];running=true;
  document.getElementById("score").textContent=0;
  document.getElementById("missed").textContent=0;
  document.getElementById("timer").textContent={time_limit};
  document.getElementById("overlay").style.display="none";
  if(timerID) clearInterval(timerID);
  if(animID) cancelAnimationFrame(animID);
  timerID=setInterval(()=>{{
    timeLeft--;
    document.getElementById("timer").textContent=timeLeft;
    if(timeLeft<=0){{
      clearInterval(timerID);cancelAnimationFrame(animID);running=false;
      // Show result
      const ov=document.getElementById("overlay");
      const grade=score>=20?"🏆 Excellent!":score>=12?"✅ Good!":"🌱 Keep practicing!";
      ov.innerHTML=`<h2 style="color:#E2E8F0;">Game Over!</h2>
        <p style="color:#A0AEC0;">Score: <b style="color:{level_color}">${{score}}</b> | Missed: <b style="color:#FC8181">${{missed}}</b></p>
        <p style="font-size:1.3rem;margin:.4rem 0;">${{grade}}</p>
        <button id="start-btn" onclick="startGame()" style="padding:10px 28px;border-radius:10px;border:none;background:linear-gradient(135deg,{level_color},{level_color}AA);color:#000;font-size:1rem;font-weight:700;cursor:pointer;">▶ Play Again</button>`;
      ov.style.display="flex";
    }}
  }},1000);
  gameLoop();
}}
</script></body></html>"""

    components.html(game_html, height=480, scrolling=False)

    st.markdown(f"""<div style='background:rgba({"74,222,128" if is_easy else "251,191,36"},.08);
         border:1px solid rgba({"74,222,128" if is_easy else "251,191,36"},.2);
         border-radius:10px;padding:.7rem 1rem;font-size:.82rem;color:#A0AEC0;margin-top:.4rem;'>
    🧠 <b style='color:{"#4ADE80" if is_easy else "#FBBF24"}'>{"Easy Mode:" if is_easy else "Medium Mode:"}</b>
    {"Slower bottles, more time. Perfect for first-timers or when you need gentle decompression." if is_easy else "Faster bottles with unpredictable zigzag motion. Sharpens focus under pressure — like exam prep!"}
    </div>""", unsafe_allow_html=True)
