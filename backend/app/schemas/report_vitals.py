"""
schemas/report_vitals.py

Pydantic v2 schemas for the vitals-extraction save/retrieve endpoints.
All names kept as report_vitals to match the existing route file convention.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ── Individual vital item ──────────────────────────────────────────────────────

class VitalItemSchema(BaseModel):
    name:            str
    value:           str
    unit:            str
    reference_range: Optional[str] = ""
    status:          str           = "Unknown"
    category:        str           = "Other"
    method:          str           = "regex"
    confidence:      float         = Field(default=0.0, ge=0.0, le=1.0)

    model_config = {"from_attributes": True}


# ── Extraction stats ───────────────────────────────────────────────────────────

class ExtractionStatsSchema(BaseModel):
    total:     int = 0
    by_table:  int = 0
    by_regex:  int = 0
    by_gemini: int = 0
    normal:    int = 0
    abnormal:  int = 0


# ── Patient info ───────────────────────────────────────────────────────────────

class PatientInfoSchema(BaseModel):
    patient_name: Optional[str] = None
    age:          Optional[str] = None
    gender:       Optional[str] = None
    report_date:  Optional[str] = None
    doctor:       Optional[str] = None


# ── Save request  (Gradio → backend) ─────────────────────────────────────────

class VitalExtractionSaveRequest(BaseModel):
    patient_info: PatientInfoSchema
    vitals:       List[VitalItemSchema]
    stats:        ExtractionStatsSchema
    pdf_filename: Optional[str] = None
    pdf_method:   Optional[str] = None
    used_gemini:  bool          = False

    @field_validator("vitals")
    @classmethod
    def vitals_not_empty(cls, v):
        if not v:
            raise ValueError("vitals list cannot be empty")
        return v


# ── Save response ──────────────────────────────────────────────────────────────

class VitalExtractionSaveResponse(BaseModel):
    success:      bool
    record_id:    int
    message:      str
    patient_name: Optional[str]
    saved_at:     datetime

    model_config = {"from_attributes": True}


# ── List item (GET /my-extractions) ───────────────────────────────────────────

class VitalExtractionListItem(BaseModel):
    id:             int
    patient_name:   Optional[str]
    report_date:    Optional[str]
    doctor_name:    Optional[str]
    pdf_filename:   Optional[str]
    pdf_method:     Optional[str]
    used_gemini:    bool
    total_vitals:   int
    normal_count:   int
    abnormal_count: int
    created_at:     datetime

    model_config = {"from_attributes": True}


# ── Detail response (GET /my-extractions/{id}) ────────────────────────────────

class VitalExtractionDetailResponse(VitalExtractionListItem):
    vitals_json: Dict[str, Any]

    model_config = {"from_attributes": True}


# ── NEW: Public analysis/chat schemas (Gradio → React frontend) ─────────────────

class AnalyzeRequest(BaseModel):
    """For POST /api/reports/analyze"""
    sample_name: Optional[str] = None
    pdf_file: Optional[UploadFile] = File(None)


class VitalDetailItem(BaseModel):
    """Detailed vitals for frontend display"""
    name: str
    value: str
    unit: str
    status: str
    category: str
    reference_range: Optional[str] = ""
    confidence: float = 0.0
    method: str = "regex"


class AnalyzeResponse(BaseModel):
    """Full extraction result"""
    report_name: str
    patient_info: PatientInfoSchema
    vitals: Dict[str, str]  # name → "value unit [status]"
    vitals_detailed: List[VitalDetailItem]
    stats: ExtractionStatsSchema
    pdf_method: str


class ChatRequest(BaseModel):
    """For POST /api/reports/chat"""
    question: str
    report_data: AnalyzeResponse  # full context


class ChatResponse(BaseModel):
    answer: str

