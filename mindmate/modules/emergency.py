"""modules/emergency.py — Crisis detection and helpline resources."""
import random

HELPLINES = [
    {"name":"iCall (TISS)",         "number":"9152987821",   "hours":"Mon–Sat 8am–10pm","emoji":"📞","color":"#63B3ED"},
    {"name":"Kiran Helpline",        "number":"1800-599-0019","hours":"24/7 Toll-Free",  "emoji":"🆘","color":"#FC8181"},
    {"name":"AASRA",                 "number":"9820466627",   "hours":"24/7",            "emoji":"💙","color":"#76E4F7"},
    {"name":"Vandrevala Foundation", "number":"1860-2662-345","hours":"24/7",            "emoji":"🤝","color":"#68D391"},
    {"name":"Snehi",                 "number":"044-24640050", "hours":"8am–10pm",        "emoji":"🌸","color":"#F6AD55"},
]
SAFETY = [
    "You are not alone — millions have felt this way and found their way through.",
    "This feeling is temporary, even when it doesn't feel that way.",
    "Reaching out for help is a sign of courage, not weakness.",
    "One small action — a text, a call — can change everything.",
    "Please tell someone you trust how you're feeling right now.",
]

def is_emergency(ed): return ed.get("emergency",False) or ed.get("score",0) < -0.85
def get_helplines(): return HELPLINES
def get_safety_message(): return random.choice(SAFETY)
