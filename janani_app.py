import os
import json
import re
import base64
import random
import tempfile

import streamlit as st
from geopy.geocoders import Nominatim
from streamlit_geolocation import streamlit_geolocation
from deep_translator import GoogleTranslator
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
    if language == "English" or not text:
        return text
    try:
        return GoogleTranslator(
            source=language_codes[language], target="en"
        ).translate(text)
    except Exception:
        return text


def t(text: str) -> str:
    """Translate a short UI string from English into the selected language."""
    return translate_from_english(text) if language != "English" else text


def translate_from_english(text: str) -> str:
    if language == "English" or not text:
        return text
    try:
        return GoogleTranslator(
            source="en", target=language_codes[language]
        ).translate(text)
    except Exception:
        return text


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


# -----------------------------
# CHATBOT STATE
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "page" not in st.session_state:
    st.session_state.page = "home"


def risk_pill(risk: str) -> str:
    cls = {
        "GREEN": "risk-pill risk-green",
        "YELLOW": "risk-pill risk-yellow",
        "RED": "risk-pill risk-red",
    }.get(risk, "risk-pill risk-green")
    label = {"GREEN": "Low", "YELLOW": "Moderate", "RED": "High"}.get(risk, "Low")
    return f'<span class="{cls}">{risk.title()} · {label}</span>'


def speak_text(text: str):
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
            r = sr.Recognizer()
            with sr.Microphone() as source:
                st.info(t("Listening... please speak clearly."))
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
            try:
                detected = r.recognize_google(
                    audio, language=language_codes.get(language, "en")
                )
                st.session_state.symptom_input = detected
                st.success(t("Captured speech."))
                st.rerun()
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
                data["mothers"].append(
                    {
                        "name": name,
                        "age": age,
                        "phone": phone,
                        "username": username,
                        "password": password,
                        "location": address,
                    }
                )
                save_data(data)
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
                        "username": username,
                        "password": password,
                        "location": address,
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

