"""
crud/report_vitals.py

Database operations for PDF vitals-extraction results.

OWNERSHIP RULE:
  Before saving, `user.name` is fetched from the DB via the JWT token
  and compared (case-insensitive, honorific-stripped) against
  `patient_info.patient_name` in the payload.
  Mismatch → 403 Forbidden.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.vital_extraction import VitalExtraction
from app.models.user import User
from app.schemas.report_vitals import (
    VitalExtractionSaveRequest,
    VitalExtractionSaveResponse,
    VitalExtractionListItem,
    VitalExtractionDetailResponse,
)

logger = logging.getLogger(__name__)


# ── Name-matching helpers ──────────────────────────────────────────────────────

def _normalise(name: str | None) -> str:
    if not name:
        return ""
    return " ".join(name.lower().strip().split())


def _names_match(db_name: str, patient_name: str | None) -> bool:
    a = _normalise(db_name)
    b = _normalise(patient_name)
    if not a or not b:
        return False
    for prefix in ("mr.", "mrs.", "ms.", "dr.", "prof.", "mr", "mrs", "ms", "dr"):
        a = a.removeprefix(prefix).strip()
        b = b.removeprefix(prefix).strip()
    return a == b or a in b or b in a


# ── SAVE ──────────────────────────────────────────────────────────────────────

def save_extraction(
    db: Session,
    payload: VitalExtractionSaveRequest,
    current_user: User,
) -> VitalExtractionSaveResponse:

    patient_name_from_pdf = payload.patient_info.patient_name

    # Ownership check — only enforce when a name was actually extracted
    if patient_name_from_pdf:
        if not _names_match(current_user.name, patient_name_from_pdf):
            logger.warning(
                "Ownership mismatch: user '%s' (id=%d) tried to save report for '%s'",
                current_user.name, current_user.id, patient_name_from_pdf,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. The patient name on the report "
                    f"('{patient_name_from_pdf}') does not match your "
                    f"account name ('{current_user.name}'). "
                    "You can only save reports that belong to you."
                ),
            )

    vitals_json = {
        "patient_info": payload.patient_info.model_dump(),
        "vitals":       [v.model_dump() for v in payload.vitals],
        "stats":        payload.stats.model_dump(),
        "pdf_filename": payload.pdf_filename,
        "pdf_method":   payload.pdf_method,
        "used_gemini":  payload.used_gemini,
    }

    record = VitalExtraction(
        user_id        = current_user.id,
        patient_name   = patient_name_from_pdf,
        report_date    = payload.patient_info.report_date,
        doctor_name    = payload.patient_info.doctor,
        patient_age    = payload.patient_info.age,
        patient_gender = payload.patient_info.gender,
        pdf_filename   = payload.pdf_filename,
        pdf_method     = payload.pdf_method,
        used_gemini    = payload.used_gemini,
        total_vitals   = payload.stats.total,
        normal_count   = payload.stats.normal,
        abnormal_count = payload.stats.abnormal,
        vitals_json    = vitals_json,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(
        "Saved VitalExtraction id=%d for user_id=%d (%s), %d vitals",
        record.id, current_user.id, current_user.name, payload.stats.total,
    )

    return VitalExtractionSaveResponse(
        success      = True,
        record_id    = record.id,
        message      = f"Successfully saved {payload.stats.total} vitals.",
        patient_name = record.patient_name,
        saved_at     = record.created_at,
    )


# ── LIST ──────────────────────────────────────────────────────────────────────

def get_my_extractions(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 20,
) -> List[VitalExtractionListItem]:
    records = (
        db.query(VitalExtraction)
        .filter(VitalExtraction.user_id == current_user.id)
        .order_by(VitalExtraction.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [VitalExtractionListItem.model_validate(r) for r in records]


# ── GET ONE ───────────────────────────────────────────────────────────────────

def get_extraction_by_id(
    db: Session,
    extraction_id: int,
    current_user: User,
) -> VitalExtractionDetailResponse:
    record = db.query(VitalExtraction).filter(VitalExtraction.id == extraction_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction record id={extraction_id} not found.",
        )
    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this record.",
        )

    return VitalExtractionDetailResponse.model_validate(record)


# ── DELETE ────────────────────────────────────────────────────────────────────

def delete_extraction(
    db: Session,
    extraction_id: int,
    current_user: User,
) -> dict:
    record = db.query(VitalExtraction).filter(VitalExtraction.id == extraction_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction record id={extraction_id} not found.",
        )
    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete another user's record.",
        )

    db.delete(record)
    db.commit()
    return {"success": True, "message": f"Extraction id={extraction_id} deleted."}