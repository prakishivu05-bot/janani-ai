import os
import json
import re
import base64
import random
import tempfile
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from streamlit_geolocation import streamlit_geolocation
from gtts import gTTS
import speech_recognition as sr

from ai_engine.janani_ai import get_ai_response
from ai_engine.risk_classifier import classify_risk


st.set_page_config(page_title="Janani AI", layout="wide")


# -----------------------------
# LANGUAGE SYSTEM
# -----------------------------
languages = ["English", "Hindi", "Kannada", "Telugu", "Tamil"]

language_codes = {
    "English": "en",
    "Hindi": "hi",
    "Kannada": "kn",
    "Telugu": "te",
    "Tamil": "ta",
}

# -----------------------------
# EMAIL / ALERT CONFIG
# -----------------------------

# Set SMTP_ENABLED = True and fill in these values to actually send emails.
SMTP_ENABLED = False
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_email@example.com"
SMTP_PASSWORD = "your_email_password"
SMTP_FROM_NAME = "Janani AI Alerts"
SMTP_FROM_EMAIL = SMTP_USERNAME

# Built-in translations for important UI texts so the interface really
#switches language even without external APIs.
UI_TRANSLATIONS = {
    "Hindi": {
        "Janani AI • Assistant": "जननी AI • सहायक",
        "Describe your symptoms": "अपने लक्षण बताइए",
        "🎙️ Speak symptoms": "🎙️ लक्षण बोलें",
        "Listening... please speak clearly.": "सुन रहा हूँ... कृपया साफ़‑साफ़ बोलें।",
        "Captured speech. You can edit the text if needed, then ask Janani AI.": "आवाज़ पकड़ ली गई है। ज़रूरत हो तो ऊपर लिखे वाक्य को बदलकर फिर जननी AI से पूछें।",
        "I did not hear anything. Please try again or type your symptoms.": "कुछ सुनाई नहीं दिया। दोबारा बोलें या लक्षण टाइप करें।",
        "Microphone is not available on this device. Please type your symptoms.": "इस डिवाइस पर माइक्रोफ़ोन उपलब्ध नहीं है। कृपया लक्षण टाइप करें।",
        "Could not understand audio. Please try again.": "आवाज़ समझ नहीं पाई। कृपया फिर से प्रयास करें।",
        "Ask Janani AI": "जननी AI से पूछें",
        "Please type or speak your symptoms first.": "पहले अपने लक्षण बोलें या टाइप करें।",
        "🔊 Read answers aloud": "🔊 उत्तर ज़ोर से सुनाएँ",
        "🤰 Continue as Mother": "🤰 गर्भवती महिला के रूप में जारी रखें",
        "👩‍⚕️ Continue as ASHA Worker": "👩‍⚕️ आशा कार्यकर्ता के रूप में जारी रखें",
        "Mother Login": "माँ लॉगिन",
        "ASHA Worker Login": "आशा कार्यकर्ता लॉगिन",
        "Username": "उपयोगकर्ता नाम",
        "Password": "पासवर्ड",
        "Login": "लॉगिन",
        "Invalid login": "गलत लॉगिन विवरण",
        "Register New Mother": "नई माँ को पंजीकृत करें",
        "Register New ASHA Worker": "नई आशा कार्यकर्ता को पंजीकृत करें",
        "Mother Registration": "माँ पंजीकरण",
        "ASHA Worker Registration": "आशा कार्यकर्ता पंजीकरण",
        "Name": "नाम",
        "Age": "आयु",
        "Phone Number": "मोबाइल नंबर",
        "Mother registered successfully": "माँ सफलतापूर्वक पंजीकृत हुई",
        "ASHA Worker registered successfully": "आशा कार्यकर्ता सफलतापूर्वक पंजीकृत हुई",
        "Mother Dashboard": "माँ डैशबोर्ड",
        "Use the assistant on the left to report symptoms and get guidance.": "बाएँ तरफ़ के सहायक से लक्षण बताएँ और सलाह प्राप्त करें।",
        "ASHA Worker Dashboard": "आशा कार्यकर्ता डैशबोर्ड",
        "Registered Pregnant Women:": "पंजीकृत गर्भवती महिलाएँ:",
        "⬅ Back": "⬅ वापस",
    },
    "Kannada": {
        "Janani AI • Assistant": "ಜನನಿ AI • ಸಹಾಯಕಿ",
        "Describe your symptoms": "ನಿಮ್ಮ ಲಕ್ಷಣಗಳನ್ನು ವಿವರಿಸಿ",
        "🎙️ Speak symptoms": "🎙️ ಲಕ್ಷಣಗಳನ್ನು ಮಾತನಾಡಿ",
        "Listening... please speak clearly.": "ಕೇಳುತ್ತಿದ್ದೇನೆ... ದಯವಿಟ್ಟು ಸ್ಪಷ್ಟವಾಗಿ ಮಾತನಾಡಿ.",
        "Captured speech. You can edit the text if needed, then ask Janani AI.": "ನಿಮ್ಮ ಧ್ವನಿ ದಾಖಲಿಸಲಾಗಿದೆ. ಬೇಕಾದರೆ ಮೇಲಿನ ಬರಹವನ್ನು ಬದಲಿಸಿ ನಂತರ ಜನನಿ AI ಗೆ ಕೇಳಿ.",
        "I did not hear anything. Please try again or type your symptoms.": "ಯಾವುದೂ ಕೇಳಿಸಲಿಲ್ಲ. ಮತ್ತೆ ಮಾತನಾಡಿ ಅಥವಾ ಲಕ್ಷಣಗಳನ್ನು ಟೈಪ್ ಮಾಡಿ.",
        "Microphone is not available on this device. Please type your symptoms.": "ಈ ಸಾಧನದಲ್ಲಿ ಮೈಕ್ರೋಫೋನ್ ಲಭ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ಲಕ್ಷಣಗಳನ್ನು ಟೈಪ್ ಮಾಡಿ.",
        "Could not understand audio. Please try again.": "ಧ್ವನಿಯನ್ನು ಅರ್ಥ ಮಾಡಿಕೊಳ್ಳಲು ಆಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
        "Ask Janani AI": "ಜನನಿ AI ಯನ್ನು ಕೇಳಿ",
        "Please type or speak your symptoms first.": "ಮೊದಲು ಲಕ್ಷಣಗಳನ್ನು ಮಾತನಾಡಿ ಅಥವಾ ಟೈಪ್ ಮಾಡಿ.",
        "🔊 Read answers aloud": "🔊 ಉತ್ತರವನ್ನು ಜೋರಾಗಿ ಓದಿ",
        "🤰 Continue as Mother": "🤰 ಗರ್ಭಿಣಿಯಾಗಿ ಮುಂದುವರೆಯಿರಿ",
        "👩‍⚕️ Continue as ASHA Worker": "👩‍⚕️ ಆಶಾ ಕಾರ್ಯಕರ್ತೆಯಾಗಿ ಮುಂದುವರೆಯಿರಿ",
        "Mother Login": "ತಾಯಿ ಲಾಗಿನ್",
        "ASHA Worker Login": "ಆಶಾ ಕಾರ್ಯಕರ್ತೆ ಲಾಗಿನ್",
        "Username": "ಬಳಕೆದಾರ ಹೆಸರು",
        "Password": "ಗುಪ್ತಪದ",
        "Login": "ಲಾಗಿನ್",
        "Invalid login": "ತಪ್ಪು ಲಾಗಿನ್ ವಿವರಗಳು",
        "Register New Mother": "ಹೊಸ ತಾಯಿಯನ್ನು ನೋಂದಣಿ ಮಾಡಿ",
        "Register New ASHA Worker": "ಹೊಸ ಆಶಾ ಕಾರ್ಯಕರ್ತೆಯನ್ನು ನೋಂದಣಿ ಮಾಡಿ",
        "Mother Registration": "ತಾಯಿ ನೋಂದಣಿ",
        "ASHA Worker Registration": "ಆಶಾ ಕಾರ್ಯಕರ್ತೆ ನೋಂದಣಿ",
        "Name": "ಹೆಸರು",
        "Age": "ವಯಸ್ಸು",
        "Phone Number": "ಫೋನ್ ಸಂಖ್ಯೆ",
        "Mother registered successfully": "ತಾಯಿ ಯಶಸ್ವಿಯಾಗಿ ನೋಂದಾಯಿಸಲ್ಪಟ್ಟರು",
        "ASHA Worker registered successfully": "ಆಶಾ ಕಾರ್ಯಕರ್ತೆ ಯಶಸ್ವಿಯಾಗಿ ನೋಂದಾಯಿಸಲ್ಪಟ್ಟರು",
        "Mother Dashboard": "ತಾಯಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "Use the assistant on the left to report symptoms and get guidance.": "ಲಕ್ಷಣಗಳನ್ನು ಹೇಳಲು ಮತ್ತು ಮಾರ್ಗದರ್ಶನಕ್ಕಾಗಿ ಎಡಬದಿಯ ಸಹಾಯಕಿಯನ್ನು ಬಳಸಿ.",
        "ASHA Worker Dashboard": "ಆಶಾ ಕಾರ್ಯಕರ್ತೆ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "Registered Pregnant Women:": "ನೋಂದಾಯಿತ ಗರ್ಭಿಣಿಯರು:",
        "⬅ Back": "⬅ ಹಿಂತಿರುಗಿ",
    },
    "Telugu": {
        "Janani AI • Assistant": "జనని AI • సహాయకురాలు",
        "Describe your symptoms": "మీ లక్షణాలను వివరించండి",
        "🎙️ Speak symptoms": "🎙️ లక్షణాలను మాట్లాడండి",
        "Listening... please speak clearly.": "వింటున్నాను... దయచేసి స్పష్టంగా మాట్లాడండి.",
        "Captured speech. You can edit the text if needed, then ask Janani AI.": "మీ మాటలు నమోదయ్యాయి. కావాలంటే పై వాక్యాన్ని మార్చి జనని AI ని అడగండి.",
        "I did not hear anything. Please try again or type your symptoms.": "ఏమీ వినిపించలేదు. దయచేసి మళ్ళీ మాట్లాడండి లేదా లక్షణాలను టైప్ చేయండి.",
        "Microphone is not available on this device. Please type your symptoms.": "ఈ పరికరంలో మైక్రోఫోన్ లేదు. దయచేసి లక్షణాలను టైప్ చేయండి.",
        "Could not understand audio. Please try again.": "మీ స్వరాన్ని అర్థం చేసుకోలేకపోయాను. మళ్లీ ప్రయత్నించండి.",
        "Ask Janani AI": "జనని AIని అడగండి",
        "Please type or speak your symptoms first.": "మొదట మీ లక్షణాలను చెప్పండి లేదా టైప్ చేయండి.",
        "🔊 Read answers aloud": "🔊 సమాధానాన్ని గట్టిగా చదవండి",
        "🤰 Continue as Mother": "🤰 గర్భిణిగా కొనసాగండి",
        "👩‍⚕️ Continue as ASHA Worker": "👩‍⚕️ ఆశా వర్కర్‌గా కొనసాగండి",
        "Mother Login": "తల్లి లాగిన్",
        "ASHA Worker Login": "ఆశా వర్కర్ లాగిన్",
        "Username": "యూజర్ పేరు",
        "Password": "పాస్‌వర్డ్",
        "Login": "లాగిన్",
        "Invalid login": "తప్పు లాగిన్ వివరాలు",
        "Register New Mother": "కొత్త తల్లిని నమోదు చేయండి",
        "Register New ASHA Worker": "కొత్త ఆశా వర్కర్ ను నమోదు చేయండి",
        "Mother Registration": "తల్లి నమోదు",
        "ASHA Worker Registration": "ఆశా వర్కర్ నమోదు",
        "Name": "పేరు",
        "Age": "వయస్సు",
        "Phone Number": "ఫోన్ నంబర్",
        "Mother registered successfully": "తల్లి విజయవంతంగా నమోదైంది",
        "ASHA Worker registered successfully": "ఆశా వర్కర్ విజయవంతంగా నమోదైంది",
        "Mother Dashboard": "తల్లి డ్యాష్‌బోర్డ్",
        "Use the assistant on the left to report symptoms and get guidance.": "లక్షణాలు చెప్పడానికి మరియు సలహా కోసం ఎడమవైపు ఉన్న సహాయకురాలిని వాడండి.",
        "ASHA Worker Dashboard": "ఆశా వర్కర్ డ్యాష్‌బోర్డ్",
        "Registered Pregnant Women:": "నమోదైన గర్భిణులు:",
        "⬅ Back": "⬅ వెనక్కు",
    },
    "Tamil": {
        "Janani AI • Assistant": "ஜனனி AI • உதவியாளர்",
        "Describe your symptoms": "உங்கள் அறிகுறிகளை எழுதுங்கள்",
        "🎙️ Speak symptoms": "🎙️ அறிகுறிகளை பேசுங்கள்",
        "Listening... please speak clearly.": "கேட்டு கொண்டிருக்கிறேன்... தயவுசெய்து தெளிவாக பேசுங்கள்.",
        "Captured speech. You can edit the text if needed, then ask Janani AI.": "உங்கள் குரல் பதிவாகியுள்ளது. மேலே உள்ள எழுத்தை மாற்றி பின்னர் ஜனனி AIஇடம் கேளுங்கள்.",
        "I did not hear anything. Please try again or type your symptoms.": "எதுவும் கேட்கவில்லை. மறுபடியும் பேசுங்கள் அல்லது அறிகுறிகளை type செய்யுங்கள்.",
        "Microphone is not available on this device. Please type your symptoms.": "இந்த சாதனத்தில் மைக்ரோஃபோன் இல்லை. தயவுசெய்து அறிகுறிகளை type செய்யுங்கள்.",
        "Could not understand audio. Please try again.": "குரலை புரிந்து கொள்ள முடியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
        "Ask Janani AI": "ஜனனி AIயிடம் கேளுங்கள்",
        "Please type or speak your symptoms first.": "முதலில் உங்கள் அறிகுறிகளைச் சொல்லுங்கள் அல்லது type செய்யுங்கள்.",
        "🔊 Read answers aloud": "🔊 பதிலைக் குரலில் வாசிக்கவும்",
        "🤰 Continue as Mother": "🤰 கர்ப்பிணியாகத் தொடரவும்",
        "👩‍⚕️ Continue as ASHA Worker": "👩‍⚕️ ஆஷா பணியாளராகத் தொடரவும்",
        "Mother Login": "அம்மா உள்நுழைவு",
        "ASHA Worker Login": "ஆஷா பணியாளர் உள்நுழைவு",
        "Username": "பயனர் பெயர்",
        "Password": "கடவுச்சொல்",
        "Login": "உள்நுழைவு",
        "Invalid login": "தவறான உள்நுழைவு விவரங்கள்",
        "Register New Mother": "புதிய அம்மாவை பதிவு செய்யவும்",
        "Register New ASHA Worker": "புதிய ஆஷா பணியாளரை பதிவு செய்யவும்",
        "Mother Registration": "அம்மா பதிவு",
        "ASHA Worker Registration": "ஆஷா பணியாளர் பதிவு",
        "Name": "பெயர்",
        "Age": "வயது",
        "Phone Number": "தொலைபேசி எண்",
        "Mother registered successfully": "அம்மா வெற்றிகரமாக பதிவு செய்யப்பட்டார்",
        "ASHA Worker registered successfully": "ஆஷா பணியாளர் வெற்றிகரமாக பதிவு செய்யப்பட்டார்",
        "Mother Dashboard": "அம்மா டாஷ்போர்டு",
        "Use the assistant on the left to report symptoms and get guidance.": "இடது பக்கத்தில் உள்ள உதவியாளரைப் பயன்படுத்தி அறிகுறிகளைச் சொல்லி ஆலோசனை பெறுங்கள்.",
        "ASHA Worker Dashboard": "ஆஷா பணியாளர் டாஷ்போர்டு",
        "Registered Pregnant Women:": "பதிவு செய்யப்பட்ட கர்ப்பிணிகள்:",
        "⬅ Back": "⬅ பின்செல்",
    },
}

if "language" not in st.session_state:
    st.session_state.language = "English"

top1, top2 = st.columns([8, 2])

with top2:
    selected_lang = st.selectbox(
        "🌐 Language",
        languages,
        index=languages.index(st.session_state.language),
    )

if selected_lang != st.session_state.language:
    st.session_state.language = selected_lang
    st.rerun()

language = st.session_state.language


def translate_to_english(text: str) -> str:
    # If you later want to call an English-only AI backend for all inputs,
    # plug a translator here. For now we assume users may speak any language
    # and the backend can still handle short messages reasonably.
    return text


def translate_from_english(text: str) -> str:
    # Placeholder for future external translation; currently we keep the text.
    return text


def t(text: str) -> str:
    """Translate a short UI string from English into the selected language."""
    if language == "English":
        return text
    return UI_TRANSLATIONS.get(language, {}).get(text, text)


# -----------------------------
# SIMPLE STYLING
# -----------------------------
def get_base64_image(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


bg_image = get_base64_image("hero_background.png")

st.markdown(
    f"""
<style>
.stApp {{
    background: radial-gradient(circle at 0% 0%, #ffe6f2, transparent 55%),
                radial-gradient(circle at 100% 0%, #e0e7ff, transparent 55%),
                radial-gradient(circle at 0% 100%, #e0f7fa, transparent 55%),
                linear-gradient(145deg, #ffffff, #f3f4ff);
}}
.chat-card {{
    background: linear-gradient(145deg, #0f172a, #1f2937);
    border-radius: 24px;
    padding: 1rem 1.1rem;
    color: #e5e7eb;
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.6);
}}
.chat-bubble-user {{
    background: linear-gradient(135deg, #4f46e5, #ec4899);
    border-radius: 18px 18px 4px 18px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.35rem;
    font-size: 0.85rem;
}}
.chat-bubble-ai {{
    background: rgba(15, 23, 42, 0.9);
    border-radius: 18px 18px 18px 4px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.35rem;
    font-size: 0.85rem;
    border: 1px solid rgba(148, 163, 184, 0.4);
}}
.chat-title {{
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 0.25rem;
}}
.risk-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    border-radius: 999px;
    padding: 0.15rem 0.55rem;
    font-size: 0.72rem;
    font-weight: 600;
}}
.risk-green {{ background: rgba(34,197,94,0.15); color: #22c55e; }}
.risk-yellow {{ background: rgba(234,179,8,0.15); color: #eab308; }}
.risk-red {{ background: rgba(239,68,68,0.15); color: #ef4444; }}
.login-card {{
    background: rgba(255,255,255,0.9);
    border-radius: 24px;
    padding: 1.5rem 1.6rem;
    box-shadow: 0 25px 50px rgba(148, 163, 184, 0.3);
    border: 1px solid rgba(148, 163, 184, 0.35);
}}
.login-title {{
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(120deg,#1e293b,#4f46e5);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    margin-bottom: 0.1rem;
}}
.login-sub {{
    font-size: 0.9rem;
    color: #4b5563;
    margin-bottom: 1rem;
}}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------
# DATABASE HELPERS
# -----------------------------
def load_data():
    if not os.path.exists("database/users.json"):
        os.makedirs("database", exist_ok=True)
        with open("database/users.json", "w") as f:
            json.dump({"mothers": [], "asha_workers": []}, f, indent=4)
    with open("database/users.json", "r") as f:
        return json.load(f)


def save_data(data):
    os.makedirs("database", exist_ok=True)
    with open("database/users.json", "w") as f:
        json.dump(data, f, indent=4)


def password_strength(p: str) -> bool:
    if len(p) < 8:
        return False
    if not re.search("[A-Z]", p):
        return False
    if not re.search("[a-z]", p):
        return False
    if not re.search("[0-9]", p):
        return False
    if not re.search("[@#$%^&+=]", p):
        return False
    return True


def username_exists(username: str, role: str) -> bool:
    data = load_data()
    if role == "mother":
        return any(u["username"] == username for u in data["mothers"])
    if role == "asha":
        return any(u["username"] == username for u in data["asha_workers"])
    return False


def get_exact_location():
    location = streamlit_geolocation()
    if location and location.get("latitude"):
        lat = location["latitude"]
        lon = location["longitude"]
        try:
            geolocator = Nominatim(user_agent="janani_ai", timeout=10)
            address = geolocator.reverse(f"{lat},{lon}")
            return address.address, lat, lon
        except Exception:
            return f"Lat:{lat},Lon:{lon}", lat, lon
    return None, None, None


def send_asha_email(to_email: str, subject: str, body: str):
    """Send an email to the given ASHA email address if SMTP is enabled."""
    if not SMTP_ENABLED or not to_email:
        return
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr((SMTP_FROM_NAME, SMTP_FROM_EMAIL))
        msg["To"] = to_email

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM_EMAIL, [to_email], msg.as_string())
    except Exception:
        # Fail silently in demo mode so UI is not broken
        pass


def find_nearby_asha(user_lat, user_lon, asha_list, max_km: float = 5.0):
    """
    Return ASHA workers within `max_km` kilometers of the given user
    latitude/longitude. Each returned item includes a `distance_km` field.
    """
    if user_lat is None or user_lon is None:
        return []

    user_point = (user_lat, user_lon)
    nearby = []

    for a in asha_list:
        # Safely read stored coordinates; skip if missing or invalid
        try:
            lat = float(a.get("lat")) if a.get("lat") is not None else None
            lon = float(a.get("lon")) if a.get("lon") is not None else None
        except (TypeError, ValueError):
            lat, lon = None, None

        if lat is None or lon is None:
            continue

        asha_point = (lat, lon)
        try:
            km = geodesic(user_point, asha_point).km
        except Exception:
            continue

        if km <= max_km:
            enriched = dict(a)
            enriched["distance_km"] = km
            nearby.append(enriched)

    nearby.sort(key=lambda x: x.get("distance_km", max_km + 1))
    return nearby


# -----------------------------
# CHATBOT STATE
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "page" not in st.session_state:
    st.session_state.page = "home"

if "read_aloud" not in st.session_state:
    # default ON so answers come in voice + text
    st.session_state.read_aloud = True


def risk_pill(risk: str) -> str:
    cls = {
        "GREEN": "risk-pill risk-green",
        "YELLOW": "risk-pill risk-yellow",
        "RED": "risk-pill risk-red",
    }.get(risk, "risk-pill risk-green")
    label = {"GREEN": "Low", "YELLOW": "Moderate", "RED": "High"}.get(risk, "Low")
    return f'<span class="{cls}">{risk.title()} · {label}</span>'


def speak_text(text: str):
    if not st.session_state.get("read_aloud"):
        return
    lang_code = language_codes.get(language, "en")
    try:
        tts = gTTS(text=text, lang=lang_code)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(fp.name, format="audio/mp3", autoplay=True)
    except Exception:
        # Fail silently if TTS fails
        pass


def render_chatbot():
    st.markdown(
        f'<div class="chat-card"><div class="chat-title">{t("Janani AI • Assistant")}</div>',
        unsafe_allow_html=True,
    )

    st.session_state.read_aloud = st.checkbox(
        t("🔊 Read answers aloud"), value=st.session_state.read_aloud
    )

    for msg in st.session_state.chat_history[-8:]:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-bubble-user">{msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            badge = risk_pill(msg["risk"]) if msg.get("risk") else ""
            st.markdown(
                f'<div class="chat-bubble-ai">{badge}<br>{msg["content"]}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    symptom = st.text_area(t("Describe your symptoms"), key="symptom_input", height=70)

    c1, c2 = st.columns(2)
    with c1:
        if st.button(t("🎙️ Speak symptoms")):
            try:
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    st.info(t("Listening... please speak clearly."))
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    audio = r.listen(source, timeout=3, phrase_time_limit=6)
                detected = r.recognize_google(
                    audio, language=language_codes.get(language, "en")
                )
                st.session_state.symptom_input = detected
                st.success(t("Captured speech. You can edit the text if needed, then ask Janani AI."))
            except sr.WaitTimeoutError:
                st.warning(
                    t("I did not hear anything. Please try again or type your symptoms.")
                )
            except OSError:
                st.error(
                    t("Microphone is not available on this device. Please type your symptoms.")
                )
            except Exception:
                st.error(t("Could not understand audio. Please try again."))
    with c2:
        if st.button(t("Ask Janani AI")):
            text = st.session_state.get("symptom_input", "").strip()
            if not text:
                st.warning(t("Please type or speak your symptoms first."))
            else:
                st.session_state.chat_history.append(
                    {"role": "user", "content": text}
                )
                english = translate_to_english(text)
                risk = classify_risk(english)
                response_en = get_ai_response(english)
                response_local = translate_from_english(response_en)
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": response_local,
                        "risk": risk,
                    }
                )

                # If risk is moderate or high, email nearby ASHA workers (when configured)
                if risk in ("YELLOW", "RED"):
                    current_mother = st.session_state.get("current_mother")
                    if current_mother:
                        data = load_data()
                        addr, user_lat, user_lon = get_exact_location()
                        nearby_asha = find_nearby_asha(
                            user_lat, user_lon, data.get("asha_workers", [])
                        )
                        for a in nearby_asha:
                            to_email = a.get("email")
                            if not to_email:
                                continue
                            subject = f"Janani AI alert for {current_mother.get('name','Mother')} ({risk} risk)"
                            body = f"""Janani AI has detected a {risk} risk report.

Mother details:
- Name: {current_mother.get('name','Not Available')}
- Age: {current_mother.get('age','Not Available')}
- Phone: {current_mother.get('phone','Not Available')}
- Address (registered): {current_mother.get('location','Not Available')}

Current location (approx):
- {addr or 'Not available'}

Reported symptoms:
- {text}

AI Response:
{response_local}

You are receiving this because you are registered as a nearby ASHA worker in Janani AI.
"""
                            send_asha_email(to_email, subject, body)

                speak_text(response_local)
                st.rerun()


# -----------------------------
# MAIN LAYOUT: CHAT LEFT, PAGES RIGHT
# -----------------------------
chat_col, main_col = st.columns([1.1, 2.4])

with chat_col:
    render_chatbot()

with main_col:
    if st.session_state.page == "home":
        st.markdown(
            """
            <div class="login-card">
              <div class="login-title">Janani AI</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button(t("🤰 Continue as Mother"), use_container_width=True):
                st.session_state.page = "mother_login"
                st.rerun()
        with c2:
            if st.button(t("👩‍⚕️ Continue as ASHA Worker"), use_container_width=True):
                st.session_state.page = "asha_login"
                st.rerun()

    elif st.session_state.page == "mother_login":
        if st.button(t("⬅ Back"), key="mother_back"):
            st.session_state.page = "home"
            st.rerun()
        st.subheader(t("Mother Login"))
        username = st.text_input(t("Username"))
        password = st.text_input(t("Password"), type="password")
        if st.button(t("Login")):
            data = load_data()
            for user in data["mothers"]:
                if user["username"] == username and user["password"] == password:
                    st.session_state.current_mother = user
                    st.session_state.page = "mother_dashboard"
                    st.rerun()
            st.error(t("Invalid login"))
        if st.button(t("Register New Mother")):
            st.session_state.page = "mother_register"
            st.rerun()

    elif st.session_state.page == "asha_login":
        if st.button(t("⬅ Back"), key="asha_back"):
            st.session_state.page = "home"
            st.rerun()
        st.subheader(t("ASHA Worker Login"))
        username = st.text_input(t("Username"), key="asha_user")
        password = st.text_input(t("Password"), type="password", key="asha_pass")
        if st.button(t("Login"), key="asha_login_btn"):
            data = load_data()
            for user in data["asha_workers"]:
                if user["username"] == username and user["password"] == password:
                    st.session_state.page = "asha_dashboard"
                    st.rerun()
            st.error(t("Invalid login"))
        if st.button(t("Register New ASHA Worker"), key="asha_register_btn"):
            st.session_state.page = "asha_register"
            st.rerun()

    elif st.session_state.page == "mother_register":
        if st.button(t("⬅ Back")):
            st.session_state.page = "mother_login"
            st.rerun()
        st.subheader(t("Mother Registration"))
        name = st.text_input(t("Name"))
        age = st.number_input(t("Age"), 18, 50)
        col1, col2 = st.columns([1, 4])
        with col1:
            st.write("+91")
        with col2:
            phone = st.text_input(t("Phone Number"), max_chars=10)
        username = st.text_input(t("Username"))
        password = st.text_input(t("Password"), type="password")
        address, lat, lon = get_exact_location()
        if address:
            st.success("📍 Location Detected")
            st.write(address)
        if st.button("Register"):
            if username_exists(username, "mother"):
                st.error("Username already exists")
            elif not password_strength(password):
                st.error("Weak password")
            else:
                data = load_data()
                mother_obj = {
                    "name": name,
                    "age": age,
                    "phone": phone,
                    "username": username,
                    "password": password,
                    "location": address,
                }
                data["mothers"].append(mother_obj)
                save_data(data)
                st.session_state.current_mother = mother_obj
            st.success(t("Mother registered successfully"))

    elif st.session_state.page == "asha_register":
        if st.button(t("⬅ Back")):
            st.session_state.page = "asha_login"
            st.rerun()
        st.subheader(t("ASHA Worker Registration"))
        name = st.text_input(t("Name"))
        col1, col2 = st.columns([1, 4])
        with col1:
            st.write("+91")
        with col2:
            phone = st.text_input(t("Phone Number"), max_chars=10)
        asha_email = st.text_input("Email")
        username = st.text_input(t("Username"))
        password = st.text_input(t("Password"), type="password")
        address, lat, lon = get_exact_location()
        if address:
            st.success("📍 Location Detected")
            st.write(address)
        if st.button("Register"):
            if username_exists(username, "asha"):
                st.error("Username already exists")
            elif not password_strength(password):
                st.error("Weak password")
            else:
                data = load_data()
                data["asha_workers"].append(
                    {
                        "name": name,
                        "phone": phone,
                        "email": asha_email,
                        "username": username,
                        "password": password,
                        "location": address,
                        "lat": lat,
                        "lon": lon,
                    }
                )
                save_data(data)
            st.success(t("ASHA Worker registered successfully"))

    elif st.session_state.page == "mother_dashboard":
        if st.button(t("⬅ Back"), key="mother_dash_back"):
            st.session_state.page = "home"
            st.rerun()
        st.subheader(t("Mother Dashboard"))
        st.write(t("Use the assistant on the left to report symptoms and get guidance."))

        st.subheader("Nearby ASHA Workers")
        data = load_data()
        address, lat, lon = get_exact_location()

        if lat is None or lon is None:
            st.info("Unable to detect your exact location. Please allow location access.")
        else:
            nearby_asha = find_nearby_asha(lat, lon, data.get("asha_workers", []))
            if not nearby_asha:
                st.info("No nearby ASHA workers found within 5 km.")
            else:
                for a in nearby_asha:
                    name = a.get("name", "Not Available")
                    phone = a.get("phone", "Not Available")
                    location = a.get("location", "Not Available")
                    km = a.get("distance_km", 0.0)

                    st.write(f"""
👩‍⚕️ Name: {name}

📞 Phone: {phone}

📍 Address: {location}

📏 Distance: {km:.1f} km
""")

    elif st.session_state.page == "asha_dashboard":
        if st.button(t("⬅ Back"), key="asha_dash_back"):
            st.session_state.page = "home"
            st.rerun()
        st.subheader(t("ASHA Worker Dashboard"))
        data = load_data()
        st.write(t("Registered Pregnant Women:"))
        for m in data["mothers"]:
            name = m.get("name", "Not Available")
            phone = m.get("phone", "Not Available")
            location = m.get("location", "Not Available")
            st.write(f"👩 Name: {name}")
            st.write(f"📞 Phone: {phone}")
            st.write(f"📍 Location: {location}")
            st.write("---")

