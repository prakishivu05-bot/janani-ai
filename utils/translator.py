from deep_translator import GoogleTranslator

language_map = {
    "English": "en",
    "Hindi": "hi",
    "Kannada": "kn",
    "Telugu": "te",
    "Tamil": "ta"
}

def translate_to_english(text, lang):

    if lang == "English":
        return text

    return GoogleTranslator(source=language_map[lang], target="en").translate(text)


def translate_from_english(text, lang):

    if lang == "English":
        return text

    return GoogleTranslator(source="en", target=language_map[lang]).translate(text)