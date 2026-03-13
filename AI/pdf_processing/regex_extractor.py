import re

def regex_extract_vitals(cleaned_text: str) -> dict:
    lab_results = []

    # Match pattern like: TestName 123 mg/dL
    pattern = r"([A-Za-z\s\-:]+)\s+(\d+\.?\d*)\s+(mg/dL|g/dL|/µL|bpm|mmHg|Ratio)"

    matches = re.findall(pattern, cleaned_text)

    for match in matches:
        lab_results.append({
            "test_name": match[0].strip(),
            "result": match[1],
            "unit": match[2]
        })

    return {
        "patient_info": {},
        "vital_signs": {},
        "lab_results": lab_results
    }