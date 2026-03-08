from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ── Create (register) ─────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_phone_number: Optional[str] = None


# ── Update ────────────────────────────────────────────────────
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_phone_number: Optional[str] = None


# ── Read (response) ───────────────────────────────────────────
class UserRead(BaseModel):
    id: int
    name: str
    email: str
    provider: str
    picture: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Login request ─────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Google token request ──────────────────────────────────────
class GoogleAuthRequest(BaseModel):
    token: str   # Google credential (JWT from Google One Tap)


# ── JWT token response ────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead