from sqlalchemy.orm import Session
from app.models.medical_reports import MedicalReport

def create_medical_report(db: Session, user_id: int, file_path: str, file_type: str):
    report = MedicalReport(user_id = user_id, file_path = file_path, file_type = file_type)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report

def get_medical_report_by_user(db: Session, user_id: int):
   return (db.query(MedicalReport).filter_by(user_id = user_id).order_by(MedicalReport.uploaded_at.desc()).all())

def get_medical_report_by_id(db: Session, id: int):
    return (db.query(MedicalReport).filter_by(id = id).first())

def delete_medical_report(db: Session, id: int):
    report = db.query(MedicalReport).filter_by(id = id).first()
    db.delete(report)
    db.commit()