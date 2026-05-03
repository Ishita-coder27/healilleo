from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

from sqlalchemy.orm import relationship


class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)

    # Extraction metadata
    processed = Column(Boolean, default=False, nullable=False)

    patient_name = Column(String, nullable=True)
    patient_age = Column(String, nullable=True)
    patient_gender = Column(String, nullable=True)
    report_date = Column(String, nullable=True)
    doctor_name = Column(String, nullable=True)

    pdf_method = Column(String, nullable=True)
    used_gemini = Column(Boolean, default=False)

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    vitals = relationship(
        "ReportVital",
        back_populates="report",
        cascade="all, delete-orphan"
    )