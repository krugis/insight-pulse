from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Base schema for common user attributes
class UserBase(BaseModel):
    email: EmailStr

# Schema for user creation (includes password)
class UserCreate(UserBase):
    password: str = Field(..., min_length=6) #

# Schema for updating user details
class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=6) #
    is_active: Optional[bool] = None

# Schema for user response (excluding hashed password)
class UserResponse(UserBase):
    id: int
    is_active: bool

    class ConfigDict:
        from_attributes = True # Enable ORM mode for Pydantic v2

# Schema for login request
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Schema for JWT token response
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"