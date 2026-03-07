from typing import Optional, Dict, Any
from pydantic import BaseModel


# -------- Base --------
class VitalBase(BaseModel):
    key: str
    display_name: str
    unit: Optional[str] = None
    normal_range: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    description: Optional[str] = None


# -------- Create --------
class VitalCreate(VitalBase):
    pass


# -------- Update --------
class VitalUpdate(BaseModel):
    display_name: Optional[str] = None
    unit: Optional[str] = None
    normal_range: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    description: Optional[str] = None


# -------- Read --------
class VitalRead(VitalBase):
    id: int

    class Config:
        from_attributes = True
