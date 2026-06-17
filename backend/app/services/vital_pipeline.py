from sqlalchemy.orm import Session
from app.crud.vitals import get_or_create_vital
from app.models.report_vitals import ReportVital
from app.models.medical_reports import MedicalReport

try:
    from app.vital_extractor_core.extraction_service import run_extraction
    _EXTRACTOR_AVAILABLE = True
except Exception as _e:
    import logging
    logging.getLogger(__name__).warning(f"Vital extractor unavailable: {_e}")
    _EXTRACTOR_AVAILABLE = False


def process_report(db: Session, report_id: int, file_path: str):
    if not _EXTRACTOR_AVAILABLE:
        return {"total": 0, "error": "Vital extractor not available"}
    result  = run_extraction(file_path, file_path.split("/")[-1].split("\\")[-1], use_ai=False)
    payload = result["payload"]

    patient_info = payload.get("patient_info", {})
    report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()

    # Update report metadata
    report.patient_name   = patient_info.get("patient_name") or patient_info.get("Patient Name")
    report.patient_age    = patient_info.get("age")          or patient_info.get("Age")
    report.patient_gender = patient_info.get("gender")       or patient_info.get("Gender")
    report.report_date    = patient_info.get("report_date")  or patient_info.get("Report Date")
    report.doctor_name    = patient_info.get("doctor")       or patient_info.get("Doctor")

    report.pdf_method  = payload.get("pdf_method")
    report.used_gemini = payload.get("used_gemini", result.get("used_ai", False))
    report.processed   = True

    db.commit()

    results = []

    for v in payload.get("vitals", []):
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