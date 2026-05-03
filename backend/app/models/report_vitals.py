from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
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

    # Extracted data
    value = Column(String, nullable=True)  # stored as string (safe mode)
    unit = Column(String, nullable=True)
    reference_range = Column(String, nullable=True)
    status = Column(String, nullable=True)
    method = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    vital = relationship("Vital")
    report = relationship(
        "MedicalReport",
        back_populates="vitals"
    )