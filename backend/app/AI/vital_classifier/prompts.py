def get_classifier_prompt(user_query: str) -> str:
    return f"""
You are a medical query classifier.

Your task is to classify a user query into one or more of the following categories:
[cardiovascular, diabetes_metabolic, blood_cbc, liver_hepatic, kidney_renal, electrolytes, thyroid, nutritional, respiratory, hormonal, general_wellness, normal_communication]

Rules:
- Return ONLY a JSON array of category names
- Do NOT explain anything
- Use only the given categories
- If unsure, return ["general"]
- Multiple categories allowed

Examples:
Query: "Is my blood pressure high?"
Output: ["cardio"]

Query: "My sugar levels are increasing, should I worry?"
Output: ["diabetes"]

Query: "Why do I feel weak and tired?"
Output: ["blood", "general"]

Query: "Check my thyroid report"
Output: ["thyroid"]

Now classify:

Query: "{user_query}"
"""

def get_response_prompt(query: str, vitals: dict, context_summary: dict) -> str:
    vitals_block = "\n".join(
        f"  {name}: {value}" for name, value in vitals.items()
    ) or "  No vitals available."

    issues = ", ".join(context_summary.get("issues", [])) or "none"
    advice = ", ".join(context_summary.get("advice_given", [])) or "none"
    observations = ", ".join(context_summary.get("observations", [])) or "none"

    return f"""You are a medical AI assistant. Answer the user's health question using their vitals.
Respond ONLY with a JSON object — no markdown, no preamble.

Format:
{{
  "answer": "<your response to the user, plain text, max 200 words>",
  "summary": {{
    "issues": ["<any new health issues identified, or []>"],
    "advice_given": ["<key advice you gave, or []>"],
    "observations": ["<notable observations about vitals, or []>"]
  }}
}}

Context from prior conversation:
- Known issues: {issues}
- Advice already given: {advice}
- Prior observations: {observations}

Patient vitals:
{vitals_block}

User question: {query}"""