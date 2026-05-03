from sqlalchemy.orm import Session
from app.AI.vital_service import extract_vitals_from_report
from app.crud.vitals import get_or_create_vital
from app.models.report_vitals import ReportVital
from app.models.medical_reports import MedicalReport


def process_report(db: Session, report_id: int, file_path: str):
    payload = extract_vitals_from_report(file_path)

    report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()

    # Update report metadata
    report.patient_name = payload["patient_info"].get("patient_name")
    report.patient_age = payload["patient_info"].get("age")
    report.patient_gender = payload["patient_info"].get("gender")
    report.report_date = payload["patient_info"].get("report_date")
    report.doctor_name = payload["patient_info"].get("doctor")

    report.pdf_method = payload.get("pdf_method")
    report.used_gemini = payload.get("used_gemini", False)
    report.processed = True

    db.commit()

    results = []

    for v in payload["vitals"]:
        vital = get_or_create_vital(db, v["name"], v.get("category"))

        rv = ReportVital(
            report_id=report_id,
            vital_id=vital.id,
            value=v.get("value"),
            unit=v.get("unit"),
            reference_range=v.get("reference_range"),
            status=v.get("status"),
            method=v.get("method"),
            confidence=v.get("confidence")
        )

        db.add(rv)
        results.append(rv)

    db.commit()

    return {
        "total": len(results)
    }