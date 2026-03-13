import json
import os
from dotenv import load_dotenv
from groq import Groq
from rag.retriever import RAGRetriever

# Load environment variables
load_dotenv()

# Create Gemini client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------- AI FUNCTIONS ----------

def groq_llm(prompt: str) -> str:
    try:
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return chat.choices[0].message.content

    except Exception as e:
        return f"Groq Error: {e}"



def get_recommendations(user_data):
    vitals = user_data["vitals"]

    prompt = f"""
You are a professional health and wellness assistant.
Do NOT give medical diagnosis. Provide only lifestyle and wellness advice.

User Vitals:
{vitals}

Give:
1. Diet recommendations
2. Fitness recommendations
3. Daily routine tips
"""

    return groq_llm(prompt)


def chat_with_ai(user_data, question):
    retriever = RAGRetriever()
    context = retriever.retrieve(question)

    prompt = f"""
You are a helpful health assistant.
Use the medical context below to answer.

Medical Context:
{context}

User Data:
{user_data}

User Question:
{question}
"""

    return groq_llm(prompt)

# ---------- PROGRAM ENTRY ----------

if __name__ == "__main__":
    with open("test_data/sample_user.json") as f:
        user = json.load(f)

    print("\n🧾 HEALTH RECOMMENDATIONS\n")
    print(get_recommendations(user))

    print("\n💬 CHATBOT RESPONSE\n")
    print(chat_with_ai(user, "I am hungry right now,what should i eat a pizza or a bowl of dal?"))
