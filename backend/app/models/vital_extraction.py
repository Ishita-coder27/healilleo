from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class VitalExtraction(Base):
    """
    Stores one full vitals-extraction result per PDF upload.
    Separate from report_vitals (which links medical_reports ↔ vitals).
    """
    __tablename__ = "vital_extractions"

    id = Column(Integer, primary_key=True, index=True)

    # ── Ownership ─────────────────────────────────────────────────────────────
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Patient meta (extracted from PDF) ─────────────────────────────────────
    patient_name   = Column(String, nullable=True)
    report_date    = Column(String(50),  nullable=True)
    doctor_name    = Column(String,      nullable=True)
    patient_age    = Column(String(20),  nullable=True)
    patient_gender = Column(String(20),  nullable=True)

    # ── Extraction meta ────────────────────────────────────────────────────────
    pdf_filename   = Column(String, nullable=True)
    pdf_method     = Column(String(50), nullable=True)   # pdfplumber / pymupdf / ocr
    used_gemini    = Column(Boolean, default=False)
    total_vitals   = Column(Integer, default=0)
    normal_count   = Column(Integer, default=0)
    abnormal_count = Column(Integer, default=0)

    # ── Full JSON payload ──────────────────────────────────────────────────────
    vitals_json = Column(JSON, nullable=False)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now(), nullable=False)

    # ── Relationship ───────────────────────────────────────────────────────────
    user = relationship("User", back_populates="vital_extractions")