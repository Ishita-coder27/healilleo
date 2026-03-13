from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone, timedelta
from app.models.medications import Medication
from app.schemas.medications import MedicationCreate, MedicationUpdate

def create_medication(db: Session, user_id: int, data: MedicationCreate):
    med = Medication(user_id=user_id, **data.model_dump())
    db.add(med)
    db.commit()
    db.refresh(med)
    return med

def get_medications_by_user(db: Session, user_id: int):
    return (
        db.query(Medication)
        .filter(Medication.user_id == user_id)
        .order_by(Medication.created_at.desc())
        .all()
    )

def get_medication_by_id(db: Session, id: int):
    return db.query(Medication).filter(Medication.id == id).first()

def update_medication(db: Session, id: int, data: MedicationUpdate):
    med = get_medication_by_id(db, id)
    if not med:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(med, field, value)
    db.commit()
    db.refresh(med)
    return med

def delete_medication(db: Session, id: int):
    med = get_medication_by_id(db, id)
    if not med:
        return None
    db.delete(med)
    db.commit()
    return True

def get_upcoming_medication_reminders(db: Session):
    """Get medications due for a reminder (15 mins before next_reminder_time, not yet sent)."""
    now          = datetime.now(timezone.utc)
    window_end   = now + timedelta(minutes=15, seconds=30)
    return (
        db.query(Medication)
        .filter(and_(
            Medication.next_reminder_time != None,
            Medication.next_reminder_time <= window_end,
            Medication.next_reminder_time >= now,
            Medication.reminder_sent == False,
        ))
        .all()
    )

def mark_reminder_sent(db: Session, id: int):
    med = get_medication_by_id(db, id)
    if med:
        med.reminder_sent = True
        db.commit()