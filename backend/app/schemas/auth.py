from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignUpRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "passenger"  # passenger or user / dispatcher

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
