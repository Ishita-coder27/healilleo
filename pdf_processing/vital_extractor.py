import json
import os
from dotenv import load_dotenv
from google import genai

from regex_extractor import regex_extract_vitals
from pdf_to_text import extract_text_from_pdf
from text_cleaner import clean_medical_text


# Load API key
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def extract_vitals_to_json(cleaned_text: str) -> dict:
    prompt = f"""
You are a medical data extraction assistant.

From the following medical report text:
1. Identify ALL clinically relevant patient information, vitals, and lab parameters.
2. Extract their values and units exactly as written.
3. Group them logically (patient_info, vital_signs, lab_results).
4. Do NOT infer or invent missing values.
5. Return ONLY valid JSON. No explanations. No markdown.

Medical Report Text:
{cleaned_text}
"""

    response = client.models.generate_content(
        model="models/gemini-flash-latest",
        contents=prompt
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        raise ValueError("LLM did not return valid JSON")


# ---------------- TEST RUN ----------------
if __name__ == "__main__":
    raw_text = extract_text_from_pdf("../sample_reports/report(1).pdf")
    cleaned_text = clean_medical_text(raw_text)

    # Try regex first
    regex_result = regex_extract_vitals(cleaned_text)

    if len(regex_result["lab_results"]) >= 3:
        print("Using REGEX extraction")
        vitals_json = regex_result
    else:
        print("Fallback to LLM extraction")
        vitals_json = extract_vitals_to_json(cleaned_text)

    print("\n--- EXTRACTED UNIVERSAL JSON ---\n")
    print(json.dumps(vitals_json, indent=2, ensure_ascii=False))