import json
from .llm_client import call_llm   # your existing Groq client
from .prompts import get_response_prompt  # update prompt to request JSON


def build_medical_prompt(query: str, vitals: dict) -> str:
    """
    Compact prompt optimized for Groq + medical QA.
    """

    return f"""
You are a safe medical assistant.

You are given:
- A user's question
- Their medical vitals in compact format

RULES:
- Use ONLY provided data
- Do NOT assume missing values
- Do NOT hallucinate medical conditions
- Be concise and clear
- Answer the query like you are a real expert doctor
- Do not ask the user to consult other doctos or healthcare professionals

FORMAT OF VITALS:
vital_name → value unit | ref: range | status | date

USER QUESTION:
{query}

USER VITALS:
{json.dumps(vitals, ensure_ascii=False)}

Now answer the question clearly.
""".strip()

def generate_response(query: str, vitals: dict, context_summary: dict) -> tuple[str, dict]:
    prompt = get_response_prompt(query, vitals, context_summary)
    raw = call_llm(prompt)
    print(f"[RESPONSE_LLM] raw output type={type(raw)} | value={repr(raw[:200])}")

    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]          # drop opening fence
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]                  # drop the "json" language tag
        cleaned = cleaned.rsplit("```", 1)[0]  
            # drop closing fence
    cleaned = cleaned.strip()
    print(f"[RESPONSE_LLM] cleaned='{cleaned[:100]}'")  # add this

    try:
        parsed = json.loads(cleaned)
        print(f"[RESPONSE_LLM] parsed type={type(parsed)} | keys={parsed.keys()}")  # add this
        answer = parsed.get("answer", cleaned)
        summary = parsed.get("summary", {})
        print(f"[RESPONSE_LLM] extracted answer type={type(answer)}")  # add this
    except (json.JSONDecodeError, TypeError) as e:
        print(f"[RESPONSE_LLM] parse failed: {e}")  # add this
        answer = cleaned
        summary = {}

    return answer, summary