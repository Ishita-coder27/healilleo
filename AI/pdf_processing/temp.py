import pdfplumber

with pdfplumber.open(r"E:\AI_engine\sample_reports\sterling-accuris-pathology-sample-report-unlocked.pdf") as pdf:
    text = pdf.pages[0].extract_text()
    print(text[:1500])