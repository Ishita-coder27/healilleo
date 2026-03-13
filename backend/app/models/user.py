from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)          # nullable for Google users
    provider = Column(String(20), default="local")           # "local" or "google"
    picture = Column(String, nullable=True)                  # Google profile picture
    age = Column(Integer, nullable=True)                     # optional for Google signup
    gender = Column(String(10), nullable=True)
    phone_number = Column(String(20), nullable=True)         # optional for Google signup
    emergency_phone_number = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    vital_extractions = relationship(
        "VitalExtraction",
        back_populates="user",
        cascade="all, delete-orphan",
    )