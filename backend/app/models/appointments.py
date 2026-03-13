from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    doctor_name      = Column(String, nullable=False)
    clinic_name      = Column(String)
    appointment_time = Column(DateTime(timezone=True), nullable=False)
    notes            = Column(Text)
    reminder_sent    = Column(Boolean, default=False)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())