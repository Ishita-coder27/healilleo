from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class Medication(Base):
    __tablename__ = "medications"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    medication_name     = Column(String, nullable=False)
    dosage              = Column(String)
    frequency           = Column(String)
    start_date          = Column(Date, nullable=False)
    end_date            = Column(Date)
    notes               = Column(Text)
    reminder_sent       = Column(Boolean, default=False)
    next_reminder_time  = Column(DateTime(timezone=True))
    created_at          = Column(DateTime(timezone=True), server_default=func.now())
    updated_at          = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())