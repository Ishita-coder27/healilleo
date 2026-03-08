from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# Used internally by the CRUD layer, not directly by the user
class MedicalReportCreate(BaseModel):
    user_id: int
    file_name: str
    file_path: str
    file_type: str


# Returned to the client — no file_path exposed
class MedicalReportRead(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_type: str
    processed: bool
    uploaded_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True