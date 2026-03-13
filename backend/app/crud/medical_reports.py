from sqlalchemy.orm import Session
from app.models.medical_reports import MedicalReport
import os


def create_medical_report(db: Session, user_id: int, file_name: str, file_path: str, file_type: str):
    report = MedicalReport(
        user_id=user_id,
        file_name=file_name,
        file_path=file_path,
        file_type=file_type
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_medical_reports_by_user(db: Session, user_id: int):
    return (
        db.query(MedicalReport)
        .filter(MedicalReport.user_id == user_id)
        .order_by(MedicalReport.uploaded_at.desc())
        .all()
    )


def get_medical_report_by_id(db: Session, id: int):
    return (
        db.query(MedicalReport)
        .filter(MedicalReport.id == id)
        .first()
    )


def mark_report_as_processed(db: Session, id: int):
    report = get_medical_report_by_id(db, id)
    if not report:
        return None
    report.processed = True
    db.commit()
    db.refresh(report)
    return report


def delete_medical_report(db: Session, id: int):
    report = get_medical_report_by_id(db, id)
    if not report:
        return None
    db.delete(report)
    db.commit()
    return True


def delete_medical_report(db: Session, id: int):
    report = get_medical_report_by_id(db, id)
    if not report:
        return None
    # Delete file from disk
    if os.path.exists(report.file_path):
        os.remove(report.file_path)
    db.delete(report)
    db.commit()
    return True