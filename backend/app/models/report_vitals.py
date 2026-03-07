from sqlalchemy import (Column, Integer, Float, String, ForeignKey, DateTime)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class ReportVital(Base):
    __tablename__ = "report_vitals"

    id = Column(Integer, primary_key=True, index=True)

    report_id = Column(
        Integer,
        ForeignKey("medical_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    vital_id = Column(
        Integer,
        ForeignKey("vitals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Measured value
    value = Column(Float, nullable=False)

    # Optional overrides / metadata
    unit_override = Column(String, nullable=True)
    confidence = Column(String, nullable=True)      # lab / ocr / manual

    measured_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    vital = relationship("Vital")
    report = relationship("MedicalReport", backref="vitals")
