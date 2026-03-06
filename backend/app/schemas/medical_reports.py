from pydantic import BaseModel
from datetime import datetime


class MedicalReportCreate(BaseModel):
    file_path: str
    file_type: str


class MedicalReportRead(BaseModel):
    id: int
    user_id: int
    file_path: str
    file_type: str
    processed: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True
