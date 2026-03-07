from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, Annotated, Literal
import phonenumbers


def validate_phone_number(value):
    if value is None:
        return value
    try:
        phone = phonenumbers.parse(value, "IN")
        if not phonenumbers.is_valid_number(phone):
            raise ValueError("Invalid phone number")
    except phonenumbers.NumberParseException:
        raise ValueError("Invalid phone number format")
    return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)


# --------------------
# Shared fields
# --------------------
class UserBase(BaseModel):
    name: Annotated[
        str,
        Field(max_length=50, examples=["Saksham", "Sushant"])
    ]
    age: Annotated[int, Field(gt=0, le=120, strict=True)]
    gender: Annotated[Optional[Literal["male", "female", "other"]], Field(default=None)]
    email: EmailStr
    phone_number: str
    emergency_phone_number: Optional[str] = None

    @field_validator("phone_number", "emergency_phone_number")
    @classmethod
    def validate_phone(cls, value):
        return validate_phone_number(value)

    @model_validator(mode="after")
    def check_numbers_not_same(self):
        if self.emergency_phone_number and self.phone_number == self.emergency_phone_number:
            raise ValueError("Emergency contact must be different from primary number")
        return self


# --------------------
# For POST /users (registration)
# --------------------
class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=8, max_length=64)]
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


# --------------------
# For PATCH /users
# --------------------
class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[Literal["male", "female", "other"]] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    emergency_phone_number: Optional[str] = None

    @field_validator("phone_number", "emergency_phone_number")
    @classmethod
    def validate_phone(cls, value):
        return validate_phone_number(value)

    # Full conflict check must be done at the service layer
    # where the existing DB record is available


# --------------------
# For API responses
# --------------------
class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True