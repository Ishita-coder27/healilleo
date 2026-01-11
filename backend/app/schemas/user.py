from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, Annotated
import phonenumbers


# --------------------
# Shared fields
# --------------------
class UserBase(BaseModel):
    name: Annotated[
        str,
        Field(
            max_length=50,
            title="Name of the patient",
            description="Enter name below 50 chars",
            examples=["Saksham", "Sushant"]
        )
    ]
    age: Annotated[int, Field(gt=0, lt=100, strict=True)]
    email: EmailStr
    phone_number: str
    emergency_phone_number: Optional[str] = None

    @field_validator("phone_number", "emergency_phone_number")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            return value

        try:
            phone = phonenumbers.parse(value, "IN")
            if not phonenumbers.is_valid_number(phone):
                raise ValueError("Invalid phone number")
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number format")

        return phonenumbers.format_number(
            phone,
            phonenumbers.PhoneNumberFormat.E164
        )

    @model_validator(mode="after")
    def check_numbers_not_same(self):
        if self.emergency_phone_number and self.phone_number == self.emergency_phone_number:
            raise ValueError("Emergency contact must be different")
        return self

# --------------------
# For UPDATE /users
# --------------------
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    phone_number: Optional[str] = None
    emergency_phone_number: Optional[str] = None

    # @field_validator("phone_number", "emergency_phone_number")
    # @classmethod
    # def validate_phone(cls, value):
    #     if value is None:
    #         return value

    #     try:
    #         phone = phonenumbers.parse(value, "IN")
    #         if not phonenumbers.is_valid_number(phone):
    #             raise ValueError("Invalid phone number")
    #     except phonenumbers.NumberParseException:
    #         raise ValueError("Invalid phone number format")

    #     return phonenumbers.format_number(
    #         phone,
    #         phonenumbers.PhoneNumberFormat.E164
    #     )

    # @model_validator(mode="after")
    # def check_numbers_not_same(self):
    #     if self.emergency_phone_number and self.phone_number == self.emergency_phone_number:
    #         raise ValueError("Emergency contact must be different")
    #     return self

# --------------------
# For POST /users
# --------------------
class UserCreate(UserBase):
    pass


# --------------------
# For API responses
# --------------------
class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True
