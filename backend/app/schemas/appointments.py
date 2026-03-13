from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AppointmentCreate(BaseModel):
    doctor_name: str
    clinic_name: Optional[str] = None
    appointment_time: datetime
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    doctor_name: Optional[str] = None
    clinic_name: Optional[str] = None
    appointment_time: Optional[datetime] = None
    notes: Optional[str] = None

class AppointmentRead(BaseModel):
    id: int
    user_id: int
    doctor_name: str
    clinic_name: Optional[str]
    appointment_time: datetime
    notes: Optional[str]
    reminder_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True