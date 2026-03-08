import json
import subprocess
from rag.retriever import RAGRetriever

# ---------- Local LLM via Ollama ----------
def llm(prompt: str) -> str:
    result = subprocess.run(
        ["ollama", "run", "phi3:3.8b"],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return result.stdout.strip()


# ---------- Recommendation Engine ----------
def get_recommendations(user_data: dict) -> str:
    vitals = user_data.get("vitals", {})

    prompt = f"""
You are a professional health and wellness assistant.
Do not give medical diagnosis. Only safe lifestyle guidance.

User Vitals:
{vitals}

Generate:
1. Diet recommendations
2. Fitness recommendations
3. Daily routine tips
4. Health precautions
"""

    return llm(prompt)


# ---------- RAG-powered Medical Chatbot ----------
def chat_with_ai(user_data: dict, question: str) -> str:
    retriever = RAGRetriever()
    medical_context = retriever.retrieve(question)

    prompt = f"""
You are a helpful health assistant.
Do not provide medical diagnosis or prescriptions.

Relevant Medical Knowledge:
{medical_context}

User Health Data:
{user_data}

User Question:
{question}

Answer clearly and responsibly.
"""

    return llm(prompt)
