import streamlit as st
import json
import re
import base64
import random
from geopy.geocoders import Nominatim
from streamlit_geolocation import streamlit_geolocation
from deep_translator import GoogleTranslator

from ai_engine.janani_ai import get_ai_response
from ai_engine.risk_classifier import classify_risk

st.set_page_config(page_title="Janani AI", layout="wide")

# -----------------------------
# GOOGLE MAP EMBED
# -----------------------------
def show_google_map(lat, lon):
    map_html = f"""
    <iframe
        width="100%"
        height="450"
        style="border:0"
        loading="lazy"
        allowfullscreen
        src="https://www.google.com/maps?q={lat},{lon}&z=18&output=embed">
    </iframe>
    """
    st.markdown(map_html, unsafe_allow_html=True)

# -----------------------------
# LANGUAGE SYSTEM
# -----------------------------
languages = ["English","Hindi","Kannada","Telugu","Tamil"]

language_codes = {
    "English":"en",
    "Hindi":"hi",
    "Kannada":"kn",
    "Telugu":"te",
    "Tamil":"ta"
}

if "language" not in st.session_state:
    st.session_state.language="English"

top1,top2 = st.columns([8,2])

with top2:
    selected_lang = st.selectbox("🌐 Language",languages,index=languages.index(st.session_state.language))

if selected_lang!=st.session_state.language:
    st.session_state.language=selected_lang
    st.rerun()

language=st.session_state.language

# -----------------------------
# TRANSLATION
# -----------------------------
def translate_to_english(text):

    if language=="English":
        return text

    try:
        return GoogleTranslator(source=language_codes[language],target="en").translate(text)
    except:
        return text


def translate_from_english(text):

    if language=="English":
        return text

    try:
        return GoogleTranslator(source="en",target=language_codes[language]).translate(text)
    except:
        return text

# -----------------------------
# BACKGROUND IMAGE
# -----------------------------
def get_base64_image(path):
    with open(path,"rb") as f:
        return base64.b64encode(f.read()).decode()

bg_image=get_base64_image("hero_background.png")

# -----------------------------
# STYLING (UNCHANGED)
# -----------------------------
st.markdown(f"""
<style>

.stApp.home-bg {{
background-image:url("data:image/png;base64,{bg_image}");
background-size:cover;
background-position:center;
background-repeat:no-repeat;
overflow-x:hidden;
}}

.overlay {{
position:fixed;
top:0;
left:0;
width:100%;
height:100%;
background:rgba(0,0,0,0.35);
z-index:-1;
}}

.title {{
text-align:center;
font-size:90px;
font-weight:900;
background:linear-gradient(90deg,#0f172a,#2563eb);
-webkit-background-clip:text;
-webkit-text-fill-color:transparent;
margin-top:60px;
}}

.subtitle {{
text-align:center;
font-size:24px;
color:#1e293b;
margin-bottom:70px;
}}

.card {{
padding:45px;
border-radius:32px;
background:rgba(255,255,255,0.55);
backdrop-filter:blur(30px);
border:1px solid rgba(255,255,255,0.6);
text-align:center;
box-shadow:0 25px 60px rgba(0,0,0,0.15);
}}

</style>
<div class="overlay"></div>
""",unsafe_allow_html=True)

# -----------------------------
# DATABASE
# -----------------------------
def load_data():
    with open("database/users.json","r") as f:
        return json.load(f)

def save_data(data):
    with open("database/users.json","w") as f:
        json.dump(data,f,indent=4)

# -----------------------------
# PASSWORD VALIDATION
# -----------------------------
def password_strength(p):

    if len(p)<8: return False
    if not re.search("[A-Z]",p): return False
    if not re.search("[a-z]",p): return False
    if not re.search("[0-9]",p): return False
    if not re.search("[@#$%^&+=]",p): return False

    return True

# -----------------------------
# USERNAME CHECK
# -----------------------------
def username_exists(username,role):

    data=load_data()

    if role=="mother":
        for u in data["mothers"]:
            if u["username"]==username:
                return True

    if role=="asha":
        for u in data["asha_workers"]:
            if u["username"]==username:
                return True

    return False

# -----------------------------
# LOCATION
# -----------------------------
def get_exact_location():

    location = streamlit_geolocation()

    if location and location["latitude"]:

        lat=location["latitude"]
        lon=location["longitude"]

        try:
            geolocator=Nominatim(user_agent="janani_ai",timeout=10)
            address=geolocator.reverse(f"{lat},{lon}")
            return address.address,lat,lon

        except:
            return f"Lat:{lat},Lon:{lon}",lat,lon

    return None,None,None

# -----------------------------
# OTP SESSION
# -----------------------------
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent=False

if "generated_otp" not in st.session_state:
    st.session_state.generated_otp=""

if "phone_verified" not in st.session_state:
    st.session_state.phone_verified=False

# -----------------------------
# SESSION PAGE
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page="home"

if st.session_state.page=="home":
    st.markdown("<script>document.querySelector('.stApp').classList.add('home-bg')</script>",unsafe_allow_html=True)

# -----------------------------
# HOME
# -----------------------------
if st.session_state.page=="home":

    st.markdown('<div class="title">Janani AI</div>',unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI Maternal Health Companion</div>',unsafe_allow_html=True)

    col1,col2=st.columns(2)

    with col1:

        st.markdown("""
        <div class='card'>
        <h2>🤰 Pregnant Mother</h2>
        </div>
        """,unsafe_allow_html=True)

        if st.button("Continue as Mother"):
            st.session_state.page="mother_login"
            st.rerun()

    with col2:

        st.markdown("""
        <div class='card'>
        <h2>👩‍⚕️ ASHA Worker</h2>
        </div>
        """,unsafe_allow_html=True)

        if st.button("Continue as ASHA Worker"):
            st.session_state.page="asha_login"
            st.rerun()

# -----------------------------
# MOTHER LOGIN
# -----------------------------
elif st.session_state.page=="mother_login":

    if st.button("⬅ Back"):
        st.session_state.page="home"
        st.rerun()

    st.header("Mother Login")

    username=st.text_input("Username")
    password=st.text_input("Password",type="password")

    if st.button("Login"):

        data=load_data()

        for user in data["mothers"]:
            if user["username"]==username and user["password"]==password:

                st.session_state.page="mother_dashboard"
                st.rerun()

        st.error("Invalid login")

    if st.button("Register New Mother"):
        st.session_state.page="mother_register"
        st.rerun()

# -----------------------------
# MOTHER DASHBOARD
# -----------------------------
elif st.session_state.page=="mother_dashboard":

    if st.button("⬅ Back"):
        st.session_state.page="home"
        st.rerun()

    st.header("Report Symptoms")

    symptom=st.text_input("Describe symptoms")

    if st.button("Analyze"):

        english=translate_to_english(symptom)

        risk=classify_risk(english)

        response=get_ai_response(english)

        final=translate_from_english(response)

        st.write("### Janani AI Response")
        st.write(final)

        st.write("### Risk Level:",risk)

        # -----------------------------
        # SHOW NEARBY ASHA WORKERS
        # -----------------------------
        st.subheader("Nearby ASHA Workers")

        data = load_data()

        address,lat,lon = get_exact_location()

        found=False

        # prevent NoneType split
        if address:

            for a in data["asha_workers"]:

                if a.get("location"):

                    if address.split(",")[0] in a["location"]:

                        found=True

                        st.write(f"""
👩‍⚕️ Name: {a.get("name","Not Available")}

📞 Phone: {a.get("phone","Not Available")}

📍 Address: {a.get("location","Not Available")}
""")

        if not found:
            st.info("No nearby ASHA workers found in your area.")

# -----------------------------
# ASHA LOGIN
# -----------------------------
elif st.session_state.page=="asha_login":

    if st.button("⬅ Back", key="asha_back"):
        st.session_state.page="home"
        st.rerun()

    st.header("ASHA Worker Login")

    username=st.text_input("Username", key="asha_user")
    password=st.text_input("Password",type="password", key="asha_pass")

    if st.button("Login", key="asha_login_btn"):

        data=load_data()

        for user in data["asha_workers"]:
            if user["username"]==username and user["password"]==password:

                st.session_state.page="asha_dashboard"
                st.rerun()

        st.error("Invalid login")

    if st.button("Register New ASHA Worker", key="asha_register_btn"):
        st.session_state.page="asha_register"
        st.rerun()

# -----------------------------
# ASHA DASHBOARD
# -----------------------------
elif st.session_state.page=="asha_dashboard":

    if st.button("⬅ Back"):
        st.session_state.page="home"
        st.rerun()

    st.header("ASHA Worker Dashboard")

    data=load_data()

    st.subheader("Registered Pregnant Women")

    for m in data["mothers"]:

        name = m.get("name","Not Available")
        phone = m.get("phone","Not Available")
        location = m.get("location","Not Available")

        st.write(f"""
👩 Name: {name}

📞 Phone: {phone}

📍 Location: {location}
""")

# -----------------------------
# ASHA REGISTER
# -----------------------------
elif st.session_state.page=="asha_register":

    if st.button("⬅ Back"):
        st.session_state.page="asha_login"
        st.rerun()

    st.header("ASHA Worker Registration")

    name = st.text_input("Name")

    col1,col2 = st.columns([1,4])

    with col1:
        st.write("+91")

    with col2:
        phone = st.text_input("Phone Number",max_chars=10)

    username = st.text_input("Username")
    password = st.text_input("Password",type="password")

    address,lat,lon = get_exact_location()

    if address:

        st.success("📍 Location Detected")

        st.write(address)

        show_google_map(lat,lon)

    if st.button("Register"):

        if username_exists(username,"asha"):
            st.error("Username already exists")

        elif not password_strength(password):
            st.error("Weak password")

        else:

            data = load_data()

            data["asha_workers"].append({
                "name":name,
                "phone":phone,
                "username":username,
                "password":password,
                "location":address
            })

            save_data(data)

            st.success("ASHA Worker registered successfully")

# -----------------------------
# MOTHER REGISTER
# -----------------------------
elif st.session_state.page=="mother_register":

    if st.button("⬅ Back"):
        st.session_state.page="mother_login"
        st.rerun()

    st.header("Mother Registration")

    name = st.text_input("Name")
    age = st.number_input("Age",18,50)

    col1,col2 = st.columns([1,4])

    with col1:
        st.write("+91")

    with col2:
        phone = st.text_input("Phone Number",max_chars=10)

    username = st.text_input("Username")
    password = st.text_input("Password",type="password")

    address,lat,lon = get_exact_location()

    if address:

        st.success("📍 Location Detected")

        st.write(address)

        show_google_map(lat,lon)

    if st.button("Register"):

        if username_exists(username,"mother"):
            st.error("Username already exists")

        elif not password_strength(password):
            st.error("Weak password")

        else:

            data = load_data()

            data["mothers"].append({
                "name":name,
                "age":age,
                "phone":phone,
                "username":username,
                "password":password,
                "location":address
            })

            save_data(data)

            st.success("Mother registered successfully")

