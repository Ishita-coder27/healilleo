from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.base import Base


class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(Integer, primary_key=True, index=True)

    # assuming you already have a users table
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # path or URL where the raw report is stored
    file_path = Column(String, nullable=False)

    # pdf | image | text
    file_type = Column(String, nullable=False)

    # whether the report has been parsed / processed
    processed = Column(Boolean, default=False, nullable=False)

    # timestamp
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
