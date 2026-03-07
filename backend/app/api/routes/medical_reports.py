import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.crud import user as crud_user
from app.db.session import get_db
from app.schemas.medical_reports import MedicalReportRead
from app.crud import medical_reports as crud_reports

UPLOAD_DIR = "uploads/reports"

router = APIRouter(prefix="/medical-reports", tags=["Medical Reports"])


# POST upload a medical report
@router.post("/upload", response_model=MedicalReportRead, status_code=status.HTTP_201_CREATED)
async def upload_medical_report(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not crud_user.get_user_by_id(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    user_folder = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(user_folder, unique_filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return crud_reports.create_medical_report(
        db=db,
        user_id=user_id,
        file_name=file.filename,
        file_path=file_path,
        file_type="pdf"
    )


# GET all reports for a user
@router.get("/", response_model=list[MedicalReportRead])
def view_all_reports(user_id: int, db: Session = Depends(get_db)):
    return crud_reports.get_medical_reports_by_user(db, user_id)


# GET a single report by ID
@router.get("/{report_id}", response_model=MedicalReportRead)
def view_one_report(report_id: int, db: Session = Depends(get_db)):
    report = crud_reports.get_medical_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


# DELETE a report
@router.delete("/delete/{report_id}", status_code=status.HTTP_200_OK)
def delete_a_report(report_id: int, db: Session = Depends(get_db)):
    result = crud_reports.delete_medical_report(db, report_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"detail": "Report deleted successfully"}