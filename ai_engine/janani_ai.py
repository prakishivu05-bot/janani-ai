from openai import OpenAI

# OpenRouter Client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

def get_ai_response(user_input):

    models = [
        "z-ai/glm-4.5-air:free",
        "liquid/lfm-2.5-1.2b-instruct:free",
        "arcee-ai/trinity-mini:free",
        "arcee-ai/trinity-large-preview:free",
        "liquid/lfm-2.5-1.2b-thinking:free",
        "google/gemma-3-4b-it:free",
        "meta-llama/llama-3.3-70b-instruct:free"
    ]


    import time
    for model in models:
        for attempt in range(3):   # retry 3 times
            try:

                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role":"system","content":"You are Janani AI maternal health assistant."},
                        {"role":"user","content":user_input}
                    ]
                )

                return completion.choices[0].message.content

            except:
                time.sleep(2)   # wait before retry

    return "AI servers are busy. Please try again in a few seconds."