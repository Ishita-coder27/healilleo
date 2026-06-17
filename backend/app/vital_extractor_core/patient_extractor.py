import re
from typing import Dict

# ─────────────────────────────────────────────────────────────────────────────
# PATIENT INFO EXTRACTOR
# FIX: All patterns updated for TATA 1MG format
# ─────────────────────────────────────────────────────────────────────────────

_PATIENT_PATTERNS = {
    "Patient Name": [
        # TATA 1MG: "Customer Name : Mr.PRIYANK GUPTA   Collected Via : ..."
        re.compile(
            r"Customer\s*Name\s*[:\-]\s*(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*([A-Za-z][A-Za-z\s\.]{2,40}?)(?=\s{2,}|\s*Collected|\s*\n|$)",
            re.IGNORECASE
        ),
        # "Patient Name : John Doe" / "Patient Name: Mrs. Priya Singh"
        re.compile(
            r"Patient\s*Name\s*[:\-]?\s*(?:(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+)?([A-Za-z][A-Za-z\s\.]{1,40}?)(?=\s{2,}|\s*\n|\s*Age|\s*DOB|\s*Lab|\s*Reg|\s*Client|$)",
            re.IGNORECASE
        ),
        # "PATIENT NAME: AMIT VERMA" (all caps, SRL style)
        re.compile(
            r"^PATIENT\s+NAME\s*[:\-]\s*([A-Z][A-Z\s\.]{2,40}?)(?=\s{2,}|\s*\n|$)",
            re.MULTILINE
        ),
        # "Name : Lyubochka Svetka Lab Id : ..." / "Name: RAHUL KUMAR"
        re.compile(
            r"^\s*Name\s*[:\-]\s*(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?)?\s*([A-Za-z][A-Za-z\s\.]{2,40}?)(?:\s{2,}|\s*\n|\s*Age|\s*Lab|\s*Reg|\s*Client|\s*$)",
            re.IGNORECASE | re.MULTILINE
        ),
    ],
    "Age": [
        # "Age/Gender : 51/Male" or "Age/Sex : 25 Yrs / Male"  (slash-separated)
        re.compile(r"Age\s*/\s*(?:Gender|Sex)\s*[:\-]\s*(\d{1,3})(?:\s*Yrs?)?\s*/", re.IGNORECASE),
        # "Age / Sex       : 45 Yrs / Male"  (spaces around slash)
        re.compile(r"Age\s*\/\s*Sex\s*[:\-]\s*(\d{1,3})", re.IGNORECASE),
        # "Sex/Age : Male / 41 Y 01-Feb-1982"  (Sterling Accuris — reversed order)
        re.compile(r"Sex\s*/\s*Age\s*[:\-]\s*(?:Male|Female)\s*/\s*(\d{1,3})\s*Y", re.IGNORECASE),
        # "AGE: 32 YEARS" or "Age: 34 Years" or "Age : 25 Yrs" (inline or on its own line)
        re.compile(r"(?:^|\s)Age\s*[:\-]\s*(\d{1,3})\s*(?:years?|yrs?|Y)?\b", re.IGNORECASE | re.MULTILINE),
        # "45 Yrs" standalone (Metropolis / Thyrocare inline age without label)
        re.compile(r"\b(\d{1,3})\s*(?:Yrs?|Years?)\b", re.IGNORECASE),
    ],
    "Gender": [
        # "Age/Gender : 51/Male" or "Age/Sex : 25 Yrs / Male"
        re.compile(r"Age\s*/\s*(?:Gender|Sex)\s*[:\-]\s*\d+(?:\s*Yrs?)?\s*/\s*(Male|Female|M\b|F\b)", re.IGNORECASE),
        # "Age / Sex  : 45 Yrs / Male"
        re.compile(r"\d+\s*Yrs?\s*/\s*(Male|Female)\b", re.IGNORECASE),
        # "Sex/Age : Male / 41 Y"  (Sterling Accuris — reversed order)
        re.compile(r"Sex\s*/\s*Age\s*[:\-]\s*(Male|Female)\s*/", re.IGNORECASE),
        # "Sex: Male" / "Gender: Female" / "SEX: MALE" / standalone "MALE"/"FEMALE" after AGE
        re.compile(r"^\s*(?:Sex|Gender)\s*[:\-]\s*(Male|Female|M\b|F\b)", re.IGNORECASE | re.MULTILINE),
        re.compile(r"\bSex\s*[:\-]\s*(Male|Female)\b", re.IGNORECASE),
    ],
    "Date of Birth": [
        re.compile(r"(?:DOB|Date\s*of\s*Birth)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", re.IGNORECASE),
    ],
    "Report Date": [
        # "05/Jan/2026" or "10-Mar-2026" mixed alphanumeric
        re.compile(
            r"(?:Report\s*Date|Reported\s*On|Report\s*On)\s*[:\-]?\s*(\d{1,2}[\/-](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\/-]\d{4})",
            re.IGNORECASE
        ),
        # "Report Date : 10/03/2026" numeric
        re.compile(
            r"(?:Report\s*Date|Reported\s*On|Report\s*On)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            re.IGNORECASE
        ),
        # "Collection Date / Sample Collected / Collected On"
        re.compile(
            r"(?:Collection\s*Date|Sample\s*Collected|Collected\s*On|Collection\s*On)\s*[:\-]?\s*(\d{1,2}[\/\-\.](?:\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*)[\/\-\.]\d{2,4})",
            re.IGNORECASE
        ),
        # "Date: 12-02-2026" bare label (may be mid-line or start of line)
        re.compile(
            r"\bDate\s*[:\-]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            re.IGNORECASE
        ),
        # "13 March 2026" written out
        re.compile(
            r"(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})",
            re.IGNORECASE
        ),
    ],
    "Doctor": [
        # "Referred by / Ref. By : Dr. XYZ" — requires Dr. prefix, min 3 chars after it
        re.compile(
            r"(?:Referred?\s*[Bb]y|Ref\.?\s*[Bb]y|Consulting\s*(?:Dr\.?|Doctor)?)\s*[:\-]?\s*Dr\.?\s*([A-Za-z][A-Za-z\s\.]{2,35}?)(?=\s{2,}|\s*\n|\s*$)",
            re.IGNORECASE | re.MULTILINE
        ),
        # Same without "Dr." prefix (some reports write just the name)
        re.compile(
            r"(?:Referred?\s*[Bb]y|Ref\.?\s*[Bb]y)\s*[:\-]?\s*(?!Dr\.?\s*$)([A-Za-z][A-Za-z\s\.]{3,35}?)(?=\s{2,}|\s*\n|\s*$)",
            re.IGNORECASE | re.MULTILINE
        ),
        # "Consulting Doctor: Dr. Kapoor" / "CONSULTING DOCTOR: DR. KAPOOR"
        re.compile(
            r"(?:Consulting\s*Doctor|Attending\s*(?:Physician|Doctor))\s*[:\-]?\s*(?:Dr\.?\s*)?([A-Za-z][A-Za-z\s\.]{2,35}?)(?=\s{2,}|\s*\n|\s*$)",
            re.IGNORECASE | re.MULTILINE
        ),
        # "Doctor: Dr. Sharma" / "Doctor : Smith" (bare label)
        re.compile(
            r"^\s*Doctor\s*[:\-]\s*(?:Dr\.?\s*)?([A-Za-z][A-Za-z\s\.]{2,35}?)(?=\s{2,}|\s*\n|\s*$)",
            re.IGNORECASE | re.MULTILINE
        ),
    ],
}


def extract_patient_info(text: str) -> Dict[str, str]:
    info: Dict[str, str] = {}
    for field_name, patterns in _PATIENT_PATTERNS.items():
        for pat in patterns:
            m = pat.search(text)
            if m:
                val = m.group(1).strip()
                val = re.sub(r"\s+", " ", val).strip(" .,:").rstrip(".")
                if val and len(val) >= 2:
                    info[field_name] = val
                    break

    # Derive Age from DOB if Age was not found directly
    if "Age" not in info and "Date of Birth" in info:
        try:
            from datetime import datetime
            dob_str = info["Date of Birth"]
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
                try:
                    dob = datetime.strptime(dob_str, fmt)
                    age = (datetime.today() - dob).days // 365
                    if 0 < age < 130:
                        info["Age"] = str(age)
                    break
                except ValueError:
                    continue
        except Exception:
            pass

    return info
