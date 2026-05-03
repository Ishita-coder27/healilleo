from groq import Groq
from app.core.config import settings   # 👈 use this

# Initialize client
client = Groq(api_key=settings.GROQ_API_KEY)


def call_llm(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=2048
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("LLM ERROR:", e)
        return '["general"]'