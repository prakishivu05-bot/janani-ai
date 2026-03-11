def classify_risk(text):

    text = text.lower()

    red_keywords = ["bleeding","convulsions","severe pain","blurred vision"]
    yellow_keywords = ["dizziness","headache","swelling","fever"]

    for word in red_keywords:
        if word in text:
            return "RED"

    for word in yellow_keywords:
        if word in text:
            return "YELLOW"

    return "GREEN"