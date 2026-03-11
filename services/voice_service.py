import speech_recognition as sr
from gtts import gTTS
import os


# ----------------------------
# Voice Input (Speech → Text)
# ----------------------------
def listen():

    r = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio)
        return text

    except:
        return "Could not understand audio"


# ----------------------------
# Voice Output (Text → Speech)
# ----------------------------
def speak(text):

    tts = gTTS(text)

    file_name = "response.mp3"

    tts.save(file_name)

    os.system(f"start {file_name}")