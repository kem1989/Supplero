"""
Authentication schemas for user registration, login, and token management.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    password: str = Field(..., min_length=8, description="User's password")
    first_name: Optional[str] = Field(None, max_length=100, description="User's first name")
    last_name: Optional[str] = Field(None, max_length=100, description="User's last name")
    organization_id: int = Field(..., description="ID of the organization the user belongs to")
    role: UserRole = Field(default=UserRole.VIEWER, description="User's role")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)."""
    id: int
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    organization_id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token data payload."""
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None
    organization_id: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str 