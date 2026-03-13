from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

class MedicationCreate(BaseModel):
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None
    next_reminder_time: Optional[datetime] = None

class MedicationUpdate(BaseModel):
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    next_reminder_time: Optional[datetime] = None

class MedicationRead(BaseModel):
    id: int
    user_id: int
    medication_name: str
    dosage: Optional[str]
    frequency: Optional[str]
    start_date: date
    end_date: Optional[date]
    notes: Optional[str]
    reminder_sent: bool
    next_reminder_time: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True