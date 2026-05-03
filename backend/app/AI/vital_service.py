from app.AI.pdf_processing.vitals_extractor import VitalsExtractor
from app.AI.helpers.formatters import vitals_to_json_payload

# Initialize once (important for performance)
extractor = VitalsExtractor(
    gemini_api_key=""  # add your key if using Groq/Gemini
)


def extract_vitals_from_report(file_path: str) -> dict:
    """
    Runs full extraction pipeline on a PDF file
    and returns structured JSON payload.
    """

    # Run extractor
    result = extractor.extract(file_path)

    # Convert to clean JSON format
    payload = vitals_to_json_payload(result)

    return payload