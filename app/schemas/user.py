from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=16, description="Must be between 8 and 16 characters")
    full_name: str = Field(..., min_length=2)
    role: Optional[str] = "student"
    college: Optional[str] = None
    roll_number: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    college: Optional[str] = None
    roll_number: Optional[str] = None
    streak_days: int
    last_active_date: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

class UserUpdateProfile(BaseModel):
    full_name: Optional[str] = None
    college: Optional[str] = None
    roll_number: Optional[str] = None
