import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from app.db.session import get_db
from app.models.user import User
from app.schemas.medical_reports import MedicalReportRead
from app.crud import medical_reports as crud_reports
from app.core.auth import get_current_user

from app.services.vital_pipeline import process_report

UPLOAD_DIR = "uploads/reports"

router = APIRouter(prefix="/medical-reports", tags=["Medical Reports"])


@router.post("/upload", response_model=MedicalReportRead, status_code=status.HTTP_201_CREATED)
async def upload_medical_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    user_folder = os.path.join(UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_folder, exist_ok=True)

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(user_folder, unique_filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    report = crud_reports.create_medical_report(
        db=db,
        user_id=current_user.id,
        file_name=file.filename,
        file_path=file_path,
        file_type="pdf"
    )

    # Run extraction after saving
    process_report(db, report.id, file_path)

    return report


@router.get("/", response_model=list[MedicalReportRead])
def view_all_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud_reports.get_medical_reports_by_user(db, current_user.id)


@router.get("/{report_id}", response_model=MedicalReportRead)
def view_one_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = crud_reports.get_medical_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return report


@router.delete("/delete/{report_id}", status_code=status.HTTP_200_OK)
def delete_a_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = crud_reports.get_medical_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    crud_reports.delete_medical_report(db, report_id)
    return {"detail": "Report deleted successfully"}


@router.get("/download/{report_id}")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    report = crud_reports.get_medical_report_by_id(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    return FileResponse(
        path=report.file_path,
        media_type="application/pdf",
        filename=report.file_name,
    )