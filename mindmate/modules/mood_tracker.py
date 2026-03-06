"""
modules/mood_tracker.py
JSON-backed mood log + Plotly visualisations.
"""
import os, json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "mood_log.json")

def _load():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f: return json.load(f)
        except: pass
    return []

def _save(records):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f: json.dump(records[-200:], f, indent=2)

def log_mood(score, emotion, note=""):
    records = _load()
    records.append({"timestamp":datetime.now().isoformat(),"score":round(score,3),"emotion":emotion,"note":note[:80]})
    _save(records)

def get_records(days=7):
    records = _load()
    if not records: return pd.DataFrame(columns=["timestamp","score","emotion","note"])
    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    cutoff = datetime.now() - timedelta(days=days)
    return df[df["timestamp"] >= cutoff].sort_values("timestamp")

def get_wellness_score(df):
    if df.empty: return {"score":50,"label":"No data yet","trend":"stable ➡️"}
    avg = float(np.mean(df["score"]))
    wellness = int((avg + 1) / 2 * 100)
    scores = df["score"].tolist()
    if len(scores) >= 4:
        r,e = np.mean(scores[-3:]), np.mean(scores[:-3])
        trend = "improving 📈" if r > e+0.05 else ("declining 📉" if r < e-0.05 else "stable ➡️")
    else: trend = "stable ➡️"
    label = "Thriving 🌟" if wellness>=70 else ("Doing OK 😊" if wellness>=50 else ("Needs Care 💛" if wellness>=30 else "Struggling 💙"))
    return {"score":wellness,"label":label,"trend":trend}

def _layout(title):
    return dict(title=dict(text=title,font=dict(color="#E2E8F0",size=16)),
                paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#A0AEC0"),margin=dict(l=10,r=10,t=50,b=10),
                legend=dict(bgcolor="rgba(0,0,0,0)"))

ECOLORS = {"Positive":"#4CAF50","Neutral":"#9E9E9E","Stress":"#FF9800","Anxiety":"#F44336","Burnout":"#9C27B0"}

def build_mood_chart(df):
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="No mood data yet. Start chatting!",xref="paper",yref="paper",x=0.5,y=0.5,showarrow=False,font=dict(size=14,color="#888"))
    else:
        fig.add_trace(go.Scatter(x=df["timestamp"],y=df["score"],mode="lines",line=dict(color="rgba(124,58,237,0.2)",width=0),fill="tozeroy",fillcolor="rgba(124,58,237,0.06)",showlegend=False,hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=df["timestamp"],y=df["score"],mode="lines+markers",
            line=dict(color="#7C3AED",width=2.5,shape="spline",smoothing=0.8),
            marker=dict(size=10,color=[ECOLORS.get(e,"#607D8B") for e in df["emotion"]],line=dict(color="#0A0A18",width=2)),
            text=df["emotion"],hovertemplate="<b>%{text}</b><br>Score: %{y:.2f}<br>%{x|%b %d %H:%M}<extra></extra>",name="Mood"))
        fig.add_hline(y=0,line_dash="dot",line_color="rgba(255,255,255,0.15)",line_width=1)
    fig.update_layout(**_layout("Your Mood Trend"),
        yaxis=dict(range=[-1.1,1.1],tickvals=[-1,-0.5,0,0.5,1],ticktext=["Burnout","Anxiety","Neutral","Good","Great"],gridcolor="rgba(255,255,255,0.04)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"))
    return fig

def build_emotion_pie(df):
    fig = go.Figure()
    if df.empty:
        fig.add_annotation(text="No data yet",xref="paper",yref="paper",x=0.5,y=0.5,showarrow=False,font=dict(color="#888"))
    else:
        counts = df["emotion"].value_counts()
        fig.add_trace(go.Pie(labels=counts.index,values=counts.values,hole=0.55,
            marker=dict(colors=[ECOLORS.get(e,"#607D8B") for e in counts.index],line=dict(color="#0A0A18",width=2)),
            textinfo="label+percent",hovertemplate="%{label}: %{value}<extra></extra>"))
    fig.update_layout(**_layout("Emotion Breakdown"))
    return fig
