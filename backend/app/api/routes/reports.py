"""
Public report analysis endpoints for frontend (no auth required, like Gradio main.py).
Replicates: sample list, PDF analysis/extraction, report-aware chat.
"""

import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel

from app.schemas.report_vitals import AnalyzeRequest, AnalyzeResponse, ChatRequest, ChatResponse
from pdf_processing.vitals_extractor import VitalsExtractor
from engine import chat_with_ai, get_recommendations

# Match main.py exactly
ROOT_DIR = Path("e:/AI_engine")
SAMPLE_REPORTS_DIR = ROOT_DIR / "sample_reports"
EXTRACTOR = VitalsExtractor()

router = APIRouter(prefix="/reports", tags=["Reports (Public)"])


def get_sample_report_choices() -> dict[str, str]:
    """Returns {name: full_path} like main.py"""
    reports = {}
    if SAMPLE_REPORTS_DIR.exists():
        for pdf_path in sorted(SAMPLE_REPORTS_DIR.glob("*.pdf")):
            reports[pdf_path.name] = str(pdf_path)
    return reports


SAMPLE_REPORTS = get_sample_report_choices()


def resolve_report_path(sample_name: Optional[str], pdf_file: Optional[UploadFile]) -> tuple[str, str]:
    """Like main.py - resolve uploaded or sample path"""
    if pdf_file is not None:
        # Uploaded temp file needs saving, but for API return filename for frontend
        return pdf_file.filename, pdf_file.filename

    if sample_name and sample_name in SAMPLE_REPORTS:
        return SAMPLE_REPORTS[sample_name], sample_name

    raise HTTPException(status_code=400, detail="Choose a sample report or upload a PDF.")


def normalize_extracted_data(result: dict, report_name: str) -> AnalyzeResponse:
    """Convert VitalsExtractor result → frontend schema (exact match to main.py)"""
    vitals = []
    vitals_for_prompt = {}

    for vital in result.get("vitals", []):
        vital_row = {
            "name": vital.name,
            "value": vital.value,
            "unit": vital.unit,
            "status": vital.status,
            "category": vital.category,
            "reference_range": vital.reference_range,
            "confidence": round(vital.confidence, 3),
            "method": vital.method,
        }
        vitals.append(VitalDetailItem(**vital_row))

        display_value = vital.value
        if vital.unit:
            display_value = f"{display_value} {vital.unit}"
        if vital.status and vital.status != "Unknown":
            display_value = f"{display_value} [{vital.status}]"
        vitals_for_prompt[vital.name] = display_value

    stats = result.get("stats", ExtractionStatsSchema())

    return AnalyzeResponse(
        report_name=report_name,
        patient_info=PatientInfoSchema(**result.get("patient_info", {})),
        vitals=vitals_for_prompt,
        vitals_detailed=vitals,
        stats=stats,
        pdf_method=result.get("pdf_method", "unknown"),
    )


@router.get("/samples")
async def list_samples():
    """GET list of sample_reports/*.pdf for frontend dropdown"""
    return {"samples": list(SAMPLE_REPORTS.keys())}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_report(request: AnalyzeRequest = AnalyzeRequest()):
    """POST analyze sample or uploaded PDF → full extraction"""
    report_path, report_name = resolve_report_path(request.sample_name, request.pdf_file)
    raw_result = EXTRACTOR.extract(report_path)
    return normalize_extracted_data(raw_result, report_name)


@router.post("/chat", response_model=ChatResponse)
async def ask_report_question(request: ChatRequest):
    """POST chat question with report context → AI answer"""
    answer = chat_with_ai(request.report_data.model_dump(), request.question)
    return ChatResponse(answer=answer)


@router.post("/recommendations", response_model=str)
async def get_health_recommendations(report_data: AnalyzeResponse):
    """POST get lifestyle recommendations from report_data"""
    return get_recommendations(report_data.model_dump())

