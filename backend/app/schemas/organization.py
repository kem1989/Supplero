"""
Organization schemas for creation and response.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrganizationCreate(BaseModel):
    """Schema for organization creation."""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    domain: Optional[str] = Field(None, max_length=255, description="Organization domain")
    industry: Optional[str] = Field(None, max_length=100, description="Organization industry")
    size: Optional[str] = Field(None, max_length=50, description="Organization size")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    address: Optional[str] = Field(None, description="Organization address")


class OrganizationResponse(BaseModel):
    """Schema for organization response."""
    id: int
    name: str
    domain: Optional[str]
    industry: Optional[str]
    size: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    address: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 