from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.auth import get_current_user
from app.schemas.appointments import AppointmentCreate, AppointmentUpdate, AppointmentRead
from app.crud import appointments as crud

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("/", response_model=AppointmentRead, status_code=201)
def create(data: AppointmentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.create_appointment(db, current_user.id, data)

@router.get("/", response_model=list[AppointmentRead])
def get_all(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_appointments_by_user(db, current_user.id)

@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_one(appointment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    appt = crud.get_appointment_by_id(db, appointment_id)
    if not appt or appt.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt

@router.put("/{appointment_id}", response_model=AppointmentRead)
def update(appointment_id: int, data: AppointmentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    appt = crud.get_appointment_by_id(db, appointment_id)
    if not appt or appt.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return crud.update_appointment(db, appointment_id, data)

@router.delete("/{appointment_id}", status_code=200)
def delete(appointment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    appt = crud.get_appointment_by_id(db, appointment_id)
    if not appt or appt.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    crud.delete_appointment(db, appointment_id)
    return {"detail": "Appointment deleted"}

@router.get("/reminders/due", response_model=list[AppointmentRead])
def get_due_reminders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import datetime, timezone, timedelta
    from app.models.appointments import Appointment
    now        = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=1, minutes=5)
    return db.query(Appointment).filter(
        Appointment.user_id          == current_user.id,
        Appointment.appointment_time >= now,
        Appointment.appointment_time <= window_end,
        Appointment.reminder_sent    == True,
    ).all()
    return all_due