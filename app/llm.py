import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_ai_reply(conversation_history: list[dict]) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=conversation_history
    )
    return response.choices[0].message.content

def stream_ai_reply(conversation_history: list[dict]):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=conversation_history,
        stream=True
    )
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta