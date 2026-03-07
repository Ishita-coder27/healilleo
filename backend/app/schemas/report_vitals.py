from typing import Optional
from datetime import datetime
from pydantic import BaseModel


# -------- Base --------
class ReportVitalBase(BaseModel):
    vital_id: int
    value: float
    unit_override: Optional[str] = None
    measured_at: Optional[datetime] = None
    confidence: Optional[str] = None


# -------- Create --------
class ReportVitalCreate(ReportVitalBase):
    pass


# -------- Update --------
class ReportVitalUpdate(BaseModel):
    value: Optional[float] = None
    unit_override: Optional[str] = None
    measured_at: Optional[datetime] = None
    confidence: Optional[str] = None


# -------- Read --------
class ReportVitalRead(ReportVitalBase):
    id: int
    report_id: int
    created_at: datetime

    class Config:
        from_attributes = True
