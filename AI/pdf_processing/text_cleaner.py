import re

def clean_medical_text(text: str) -> str:
    """
    Cleans extracted medical report text by:
    - Removing excessive whitespace
    - Normalizing line breaks
    - Removing noisy characters
    """
    # Remove extra newlines
    text = re.sub(r"\n+", "\n", text)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text)

    # Remove leading/trailing spaces
    return text.strip()


# Temporary test runner
if __name__ == "__main__":
    from pdf_to_text import extract_text_from_pdf

    raw_text = extract_text_from_pdf("../sample_reports/report(1).pdf")
    cleaned_text = clean_medical_text(raw_text)

    print("\n--- CLEANED TEXT ---\n")
    print(cleaned_text)
