import re
from typing import Optional
from pydantic import BaseModel, field_validator

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email address format")
        return v

class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "passenger"  # passenger or user / dispatcher

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email address format")
        return v

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    name: str
    email: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True
