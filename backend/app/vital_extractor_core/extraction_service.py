"""
services/extraction_service.py — Orchestrates VitalsExtractor and builds the API response payload.
"""

import os
import json
import tempfile
import logging
import traceback

from app.vital_extractor_core.vitals_extractor import VitalsExtractor
from app.vital_extractor_core.report_generator import generate_report
from app.vital_extractor_core.helpers.formatters import vitals_to_json_payload, build_summary_md

logger = logging.getLogger(__name__)

# GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


def run_extraction(pdf_path: str, pdf_filename: str, use_ai: bool = False) -> dict:
    """
    Core extraction logic. Runs VitalsExtractor on the uploaded PDF.

    Args:
        pdf_path:     Absolute path to the temp PDF file.
        pdf_filename: Original filename from the upload.
        use_ai:       If True, forces Groq LLM regardless of confidence thresholds.

    Returns:
        A dict containing vitals, patient_info, stats, download paths, and summary.
    """
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key and use_ai:
        raise RuntimeError("GROQ_API_KEY is not set on the server. AI extraction is unavailable.")

    extractor = VitalsExtractor(gemini_api_key=groq_key if use_ai else "")

    if use_ai and groq_key:
        # Bypass confidence thresholds — always call Groq
        extractor.GEMINI_THRESHOLD_COUNT = 9999
        extractor.GEMINI_THRESHOLD_CONF  = 999.0

    result = extractor.extract(pdf_path)
    result["pdf_filename"] = pdf_filename

    vitals       = result["vitals"]
    patient_info = result["patient_info"]
    stats        = result["stats"]
    pdf_method   = result["pdf_method"]
    used_gemini  = result["used_gemini"]
    token_usage  = result.get("token_usage", {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    })

    # ── Build JSON payload ────────────────────────────────────────────────────
    payload = vitals_to_json_payload(result)

    # ── Write JSON to temp file ───────────────────────────────────────────────
    json_tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix="_vitals.json",
        dir=tempfile.gettempdir(), prefix="VitalExtractor_"
    )
    json_tmp.write(json.dumps(payload, indent=2).encode())
    json_tmp.close()

    # ── Generate PDF report ───────────────────────────────────────────────────
    pdf_tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix="_vital_report.pdf",
        dir=tempfile.gettempdir(), prefix="VitalExtractor_"
    )
    pdf_tmp.close()
    generate_report(
        output_path=pdf_tmp.name,
        vitals=vitals,
        patient_info=patient_info,
        stats=stats,
        used_gemini=used_gemini,
        pdf_method=pdf_method,
    )

    # ── Abnormal vitals warning ───────────────────────────────────────────────
    abnormal = [v for v in vitals if v.status in ("High", "Low")]
    warning = ""
    if abnormal:
        names = ", ".join(v.name for v in abnormal[:5])
        more  = f" and {len(abnormal) - 5} more" if len(abnormal) > 5 else ""
        warning = f"Abnormal values detected: {names}{more}. Please consult a physician."

    # ── Summary markdown ──────────────────────────────────────────────────────
    summary = build_summary_md(stats, patient_info, pdf_method, used_gemini, token_usage)

    return {
        "payload":      payload,
        "summary":      summary,
        "warning":      warning,
        "json_path":    json_tmp.name,
        "pdf_path":     pdf_tmp.name,
        "token_usage":  token_usage,
        "used_ai":      used_gemini,
        "stats":        stats,
        "patient_info": patient_info,
    }