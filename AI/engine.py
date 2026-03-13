import os
import shutil
import subprocess
from typing import Any, Dict, List

from rag.retriever import RAGRetriever

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None


if load_dotenv:
    load_dotenv()


OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:3.8b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-flash-latest")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def _format_patient_info(user_data: Dict[str, Any]) -> str:
    patient_info = user_data.get("patient_info", {})
    if not patient_info:
        return "No patient info available."

    lines = []
    for key, value in patient_info.items():
        if value:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines) if lines else "No patient info available."


def _format_vitals_for_prompt(user_data: Dict[str, Any]) -> str:
    vitals = user_data.get("vitals_detailed")
    if isinstance(vitals, list) and vitals:
        lines = []
        for vital in vitals:
            line = f"- {vital.get('name', 'Unknown')}: {vital.get('value', '')}"
            unit = vital.get("unit")
            status = vital.get("status")
            category = vital.get("category")
            if unit:
                line += f" {unit}"
            if status and status != "Unknown":
                line += f" [{status}]"
            if category:
                line += f" <{category}>"
            lines.append(line)
        return "\n".join(lines)

    vitals = user_data.get("vitals", {})
    if isinstance(vitals, dict) and vitals:
        return "\n".join(f"- {name}: {value}" for name, value in vitals.items())

    return "No vitals available."


def _extract_abnormal_vitals(user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    vitals = user_data.get("vitals_detailed", [])
    return [
        vital for vital in vitals
        if str(vital.get("status", "")).lower() in {"high", "low", "critical", "elevated"}
    ]


def _build_report_snapshot(user_data: Dict[str, Any]) -> str:
    snapshot = f"""Patient Info:
{_format_patient_info(user_data)}

Vitals:
{_format_vitals_for_prompt(user_data)}
"""
    pdf_text = user_data.get("pdf_text", "")
    if pdf_text and len(pdf_text.strip()) > 100:
        snapshot += f"""
Raw Report Text (first 3000 chars):
{pdf_text[:3000]}
"""
    return snapshot


def _run_groq(prompt: str) -> str:
    if not GROQ_API_KEY or Groq is None:
        raise RuntimeError("Groq is not configured.")

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    text = response.choices[0].message.content.strip()
    if not text:
        raise RuntimeError("Groq returned an empty response.")
    return text


def _run_ollama(prompt: str) -> str:
    if not shutil.which("ollama"):
        raise RuntimeError("Ollama is not installed or not available in PATH.")

    result = subprocess.run(
        ["ollama", "run", OLLAMA_MODEL],
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise RuntimeError(stderr or f"Ollama failed for model {OLLAMA_MODEL}.")

    output = (result.stdout or "").strip()
    if not output:
        raise RuntimeError("Ollama returned an empty response.")

    return output


def _run_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY or genai is None:
        raise RuntimeError("Gemini is not configured.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    text = getattr(response, "text", "") or ""
    text = text.strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text


def llm(prompt: str) -> str:
    errors = []

    try:
        return _run_groq(prompt)
    except Exception as exc:
        errors.append(f"Groq: {exc}")

    try:
        return _run_ollama(prompt)
    except Exception as exc:
        errors.append(f"Ollama: {exc}")

    try:
        return _run_gemini(prompt)
    except Exception as exc:
        errors.append(f"Gemini: {exc}")

    raise RuntimeError(" | ".join(errors))


def _rule_based_recommendations(user_data: Dict[str, Any]) -> str:
    abnormal_vitals = _extract_abnormal_vitals(user_data)
    if not abnormal_vitals:
        return (
            "Diet Recommendations\n"
            "- Continue balanced meals with vegetables, protein, and hydration.\n\n"
            "Fitness Recommendations\n"
            "- Maintain regular walking or light exercise most days of the week.\n\n"
            "Daily Routine Tips\n"
            "- Sleep consistently, manage stress, and repeat tests if your clinician advised follow-up."
        )

    lines = ["Diet Recommendations"]
    for vital in abnormal_vitals[:3]:
        name = vital.get("name", "")
        lower_name = name.lower()
        if "glucose" in lower_name or "hba1c" in lower_name:
            lines.append("- Reduce sugary drinks and refined carbs; prefer high-fiber meals.")
        elif "cholesterol" in lower_name or "triglyceride" in lower_name:
            lines.append("- Prefer lower saturated fat intake and add more fiber-rich foods.")
        elif "blood pressure" in lower_name or name.lower() == "bp":
            lines.append("- Keep salt intake moderate and avoid heavily processed foods.")
        elif "bmi" in lower_name or "weight" in lower_name:
            lines.append("- Focus on portion control and consistent meal timing.")

    lines.extend([
        "",
        "Fitness Recommendations",
        "- Aim for regular walking, light cardio, or clinician-approved activity.",
        "- Stay consistent rather than intense if the report shows abnormal values.",
        "",
        "Daily Routine Tips",
        "- Track abnormal vitals over time and discuss trends with a qualified doctor.",
        "- Use this report as a baseline for follow-up testing.",
    ])
    return "\n".join(dict.fromkeys(lines))


def _rule_based_chat(user_data: Dict[str, Any], question: str) -> str:
    question_lower = question.lower()
    abnormal_vitals = _extract_abnormal_vitals(user_data)
    patient_info = user_data.get("patient_info", {})

    if "abnormal" in question_lower or "high" in question_lower or "low" in question_lower:
        if not abnormal_vitals:
            return "No clearly abnormal vitals were found in the extracted report data."

        lines = ["These are the abnormal values found in the current report:"]
        for vital in abnormal_vitals:
            line = f"- {vital.get('name')}: {vital.get('value')}"
            if vital.get("unit"):
                line += f" {vital.get('unit')}"
            if vital.get("status"):
                line += f" ({vital.get('status')})"
            lines.append(line)
        lines.append("Use the report summary with a clinician for medical interpretation.")
        return "\n".join(lines)

    if "summary" in question_lower or "summarize" in question_lower:
        name = patient_info.get("Patient Name", "the patient")
        report_name = user_data.get("report_name", "the report")
        total = user_data.get("stats", {}).get("total", 0)
        abnormal = user_data.get("stats", {}).get("abnormal", 0)
        return (
            f"{report_name} was analyzed for {name}. "
            f"{total} vitals were extracted, and {abnormal} were flagged as abnormal. "
            "Review the abnormal values first, then use the recommendations section for lifestyle guidance."
        )

    if "diet" in question_lower or "food" in question_lower or "eat" in question_lower:
        return _rule_based_recommendations(user_data)

    if "patient" in question_lower or "name" in question_lower or "age" in question_lower:
        return _format_patient_info(user_data)

    return (
        "I can answer questions about the extracted report, including abnormal values, summary, diet guidance, "
        "and patient details. If you want a stronger free-form answer, make sure Ollama or Gemini is configured."
    )


# ---------- Recommendation Engine ----------
def get_recommendations(user_data: dict) -> str:
    prompt = f"""
You are a professional health and wellness assistant.

Rules:
- Never diagnose disease
- Never mention dangerous medical conclusions
- Only give practical lifestyle advice

Patient Info:
{_format_patient_info(user_data)}

User Vitals:
{_format_vitals_for_prompt(user_data)}

Give output in clean sections:

1. Diet Recommendations
2. Fitness Recommendations
3. Daily Routine Tips
"""
    try:
        return llm(prompt)
    except Exception:
        return _rule_based_recommendations(user_data)


# ---------- RAG-powered Medical Chatbot ----------
def chat_with_ai(user_data, question):
    try:
        retriever = RAGRetriever()
        context = retriever.retrieve(question)
    except Exception:
        context = "No external medical context was available."

    prompt = f"""
You are a helpful health assistant.

Use patient report carefully.
Do not diagnose disease.
If the report contains abnormal values, explain them plainly and suggest safe follow-up with a clinician.

Patient Data:
{_build_report_snapshot(user_data)}

Medical Context:
{context}

Answer clearly and practically and responsibly.

Question:
{question}
"""
    try:
        return llm(prompt)
    except Exception:
        return _rule_based_chat(user_data, question)
