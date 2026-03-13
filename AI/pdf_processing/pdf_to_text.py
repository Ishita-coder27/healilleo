import pdfplumber

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


if __name__ == "__main__":
    pdf_path = "../sample_reports/report(1).pdf"
    extracted_text = extract_text_from_pdf(pdf_path)
    print(extracted_text)
