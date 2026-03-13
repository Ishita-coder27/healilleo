"""
api/routes/report_vitals.py

All endpoints require a valid JWT (get_current_user dependency).
Users can only save / read / delete their own extraction records.

Endpoints:
  POST   /api/report-vitals/save-extraction   → save a new extraction
  GET    /api/report-vitals/my-extractions    → list current user's records
  GET    /api/report-vitals/{id}              → get one full record
  DELETE /api/report-vitals/{id}              → delete one record
"""

from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.report_vitals import (
    VitalExtractionSaveRequest,
    VitalExtractionSaveResponse,
    VitalExtractionListItem,
    VitalExtractionDetailResponse,
)
import app.crud.report_vitals as crud

router = APIRouter(
    prefix="/report-vitals",
    tags=["Report Vitals"],
)


@router.post(
    "/save-extraction",
    response_model=VitalExtractionSaveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save vitals extracted from a PDF (ownership enforced)",
)
def save_extraction(
    payload: VitalExtractionSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.save_extraction(db=db, payload=payload, current_user=current_user)


@router.get(
    "/my-extractions",
    response_model=List[VitalExtractionListItem],
    summary="List all extraction records saved by the current user",
)
def list_my_extractions(
    skip:  int = Query(default=0,  ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db:    Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_my_extractions(db=db, current_user=current_user, skip=skip, limit=limit)


@router.get(
    "/{extraction_id}",
    response_model=VitalExtractionDetailResponse,
    summary="Get full detail of one extraction record (must belong to current user)",
)
def get_extraction(
    extraction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_extraction_by_id(db=db, extraction_id=extraction_id, current_user=current_user)


@router.delete(
    "/{extraction_id}",
    summary="Delete an extraction record (must belong to current user)",
)
def delete_extraction(
    extraction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.delete_extraction(db=db, extraction_id=extraction_id, current_user=current_user)