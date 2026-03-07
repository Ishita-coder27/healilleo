from sqlalchemy.orm import Session
from app.models.report_vitals import ReportVital
from app.schemas.report_vitals import (
    ReportVitalCreate,
    ReportVitalUpdate
)


# -------- Create --------
def create_report_vital(
    db: Session,
    report_id: int,
    vital_data: ReportVitalCreate
) -> ReportVital:
    report_vital = ReportVital(
        report_id=report_id,
        **vital_data.model_dump()
    )
    db.add(report_vital)
    db.commit()
    db.refresh(report_vital)
    return report_vital


# -------- Read --------
def get_report_vital_by_id(
    db: Session,
    report_vital_id: int
) -> ReportVital | None:
    return (
        db.query(ReportVital)
        .filter(ReportVital.id == report_vital_id)
        .first()
    )


def get_vitals_for_report(
    db: Session,
    report_id: int
):
    return (
        db.query(ReportVital)
        .filter(ReportVital.report_id == report_id)
        .all()
    )


# -------- Update --------
def update_report_vital(
    db: Session,
    report_vital_id: int,
    vital_data: ReportVitalUpdate
) -> ReportVital | None:
    report_vital = get_report_vital_by_id(db, report_vital_id)
    if not report_vital:
        return None

    update_data = vital_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(report_vital, field, value)

    db.commit()
    db.refresh(report_vital)
    return report_vital


# -------- Delete --------
def delete_report_vital(
    db: Session,
    report_vital_id: int
) -> bool:
    report_vital = get_report_vital_by_id(db, report_vital_id)
    if not report_vital:
        return False

    db.delete(report_vital)
    db.commit()
    return True
