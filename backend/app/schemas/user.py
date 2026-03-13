from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ── Request schemas ────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_phone_number: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    token: str   # Google ID token from frontend


# ── Response schemas ───────────────────────────────────────────────────────────

class UserRead(BaseModel):
    id: int
    name: str
    email: str
    provider: str
    picture: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_phone_number: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ── Update schema ──────────────────────────────────────────────────────────────

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_phone_number: Optional[str] = None
    picture: Optional[str] = None