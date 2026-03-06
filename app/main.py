import json
import os
from dotenv import load_dotenv
from google import genai
from rag.retriever import RAGRetriever

# Load environment variables
load_dotenv()

# Create Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ---------- AI FUNCTIONS ----------

def gemini_llm(prompt: str) -> str:
    response = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents=prompt
    )
    return response.text



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

    return gemini_llm(prompt)


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

    return gemini_llm(prompt)

# ---------- PROGRAM ENTRY ----------

if __name__ == "__main__":
    with open("test_data/sample_user.json") as f:
        user = json.load(f)

    print("\n🧾 HEALTH RECOMMENDATIONS\n")
    print(get_recommendations(user))

    print("\n💬 CHATBOT RESPONSE\n")
    print(chat_with_ai(user, "Tum kaise ho ?"))
