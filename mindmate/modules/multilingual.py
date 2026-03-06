"""modules/multilingual.py — Language detection + translation (EN/HI/GU)."""
SUPPORTED_LANGUAGES = {"en":"English","hi":"Hindi","gu":"Gujarati"}
HINDI_CHARS   = set("अआइईउऊएऐओऔकखगघचछजझटठडढणतथदधनपफबभमयरलवशषसह")
GUJARATI_CHARS= set("અઆઇઈઉઊએઐઓઔકખગઘચછજઝટઠડઢણતથદધનપફબભમયરલવશષસહ")

try:
    from deep_translator import GoogleTranslator
    from langdetect import detect, LangDetectException
    AVAIL = True
except: AVAIL = False

def detect_language(text):
    if not text: return "en"
    chars = set(text)
    if chars & GUJARATI_CHARS: return "gu"
    if chars & HINDI_CHARS: return "hi"
    if AVAIL:
        try:
            l = detect(text)
            return l if l in SUPPORTED_LANGUAGES else "en"
        except: pass
    return "en"

def translate_to_english(text, src):
    if src == "en" or not AVAIL: return text
    try: return GoogleTranslator(source=src, target="en").translate(text) or text
    except: return text

def translate_from_english(text, tgt):
    if tgt == "en" or not AVAIL: return text
    try: return GoogleTranslator(source="en", target=tgt).translate(text) or text
    except: return text

UI = {
    "en":{"welcome":"Hello! I'm MindMate AI 👋","subtitle":"Your compassionate mental wellness companion.","placeholder":"How are you feeling today?","send":"Send"},
    "hi":{"welcome":"नमस्ते! मैं MindMate AI हूँ 👋","subtitle":"आपका मानसिक स्वास्थ्य साथी।","placeholder":"आज आप कैसा महसूस कर रहे हैं?","send":"भेजें"},
    "gu":{"welcome":"નમસ્તે! હું MindMate AI છું 👋","subtitle":"તમારો માનસિક સ્વાસ્થ્ય સાથી.","placeholder":"આજે તમે કેવું અનુભવો છો?","send":"મોકલો"},
}
def get_ui(key, lang="en"): return UI.get(lang, UI["en"]).get(key, UI["en"].get(key, key))
