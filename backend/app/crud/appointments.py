from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone
from app.models.appointments import Appointment
from app.schemas.appointments import AppointmentCreate, AppointmentUpdate

def create_appointment(db: Session, user_id: int, data: AppointmentCreate):
    appt = Appointment(user_id=user_id, **data.model_dump())
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt

def get_appointments_by_user(db: Session, user_id: int):
    return (
        db.query(Appointment)
        .filter(Appointment.user_id == user_id)
        .order_by(Appointment.appointment_time.asc())
        .all()
    )

def get_appointment_by_id(db: Session, id: int):
    return db.query(Appointment).filter(Appointment.id == id).first()

def update_appointment(db: Session, id: int, data: AppointmentUpdate):
    appt = get_appointment_by_id(db, id)
    if not appt:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(appt, field, value)
    db.commit()
    db.refresh(appt)
    return appt

def delete_appointment(db: Session, id: int):
    appt = get_appointment_by_id(db, id)
    if not appt:
        return None
    db.delete(appt)
    db.commit()
    return True

def get_upcoming_appointment_reminders(db: Session):
    """Get appointments due for a reminder (1 hour before, not yet sent)."""
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    window_start = now
    window_end   = now + timedelta(hours=1, minutes=5)
    return (
        db.query(Appointment)
        .filter(and_(
            Appointment.appointment_time >= window_start,
            Appointment.appointment_time <= window_end,
            Appointment.reminder_sent == False,
        ))
        .all()
    )

def mark_reminder_sent(db: Session, id: int):
    appt = get_appointment_by_id(db, id)
    if appt:
        appt.reminder_sent = True
        db.commit()