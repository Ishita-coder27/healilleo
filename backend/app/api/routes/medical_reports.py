from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.crud import user as crud_user
from app.db.session import get_db
from app.schemas.medical_reports import (
    MedicalReportCreate,
    MedicalReportRead
)
from app.crud import medical_reports as crud_reports

router = APIRouter(prefix="/medical-reports", tags=["Medical Reports"])

@router.post(
    "/add",
    response_model=MedicalReportRead,
    status_code=status.HTTP_201_CREATED
)
def add_medical_report(
    user_id: int,
    report: MedicalReportCreate,
    db: Session = Depends(get_db)
):
    if not crud_user.get_user_by_id(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    return crud_reports.create_medical_report(
        db=db,
        user_id=user_id,
        file_path=report.file_path,
        file_type=report.file_type
    )

@router.get("/", response_model=list[MedicalReportRead])

def view_all_reports(user_id: int, db: Session = Depends(get_db)):

    return crud_reports.get_medical_report_by_user(db, user_id)

@router.get("/{report_id}", response_model=MedicalReportRead)

def view_one_report(report_id: int, db: Session = Depends(get_db)):

    return crud_reports.get_medical_report_by_id(db, report_id)

@router.delete('/delete/{report_id}', response_model=str)

def delete_a_report(report_id: int, db: Session = Depends(get_db)):

    crud_reports.delete_medical_report(db, report_id)
    return ("Report deleted successully")

