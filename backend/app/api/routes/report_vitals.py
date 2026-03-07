from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.report_vitals import (
    ReportVitalCreate,
    ReportVitalUpdate,
    ReportVitalRead
)
from app.crud import report_vitals as crud_report_vitals
from app.crud import medical_reports as crud_reports
from app.crud import vitals as crud_vitals

router = APIRouter(prefix="/reports", tags=["Report Vitals"])

@router.post(
    "/{report_id}/vitals",
    response_model=ReportVitalRead,
    status_code=status.HTTP_201_CREATED
)
def add_vital_to_report(
    report_id: int,
    vital: ReportVitalCreate,
    db: Session = Depends(get_db)
):
    if not crud_reports.get_medical_report_by_id(db, report_id):
        raise HTTPException(status_code=404, detail="Report not found")

    if not crud_vitals.get_vital_by_id(db, vital.vital_id):
        raise HTTPException(status_code=404, detail="Vital not found")

    return crud_report_vitals.create_report_vital(
        db=db,
        report_id=report_id,
        vital_data=vital
    )

@router.get(
    "/{report_id}/vitals",
    response_model=list[ReportVitalRead]
)
def list_report_vitals(
    report_id: int,
    db: Session = Depends(get_db)
):
    if not crud_reports.get_medical_report_by_id(db, report_id):
        raise HTTPException(status_code=404, detail="Report not found")

    return crud_report_vitals.get_vitals_for_report(db, report_id)

@router.patch(
    "/vitals/{report_vital_id}",
    response_model=ReportVitalRead
)
def update_report_vital(
    report_vital_id: int,
    vital_data: ReportVitalUpdate,
    db: Session = Depends(get_db)
):
    vital = crud_report_vitals.update_report_vital(
        db,
        report_vital_id,
        vital_data
    )
    if not vital:
        raise HTTPException(status_code=404, detail="Report vital not found")
    return vital

@router.delete(
    "/vitals/{report_vital_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_report_vital(
    report_vital_id: int,
    db: Session = Depends(get_db)
):
    deleted = crud_report_vitals.delete_report_vital(
        db,
        report_vital_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Report vital not found")
