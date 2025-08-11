"""
Audit log schemas for API responses and data validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLogBase(BaseModel):
    """Base audit log schema."""
    
    action: str = Field(..., description="Action performed")
    resource_type: Optional[str] = Field(None, description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of resource affected")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    ip_address: Optional[str] = Field(None, description="IP address of the request")
    user_agent: Optional[str] = Field(None, description="User agent string")


class AuditLogCreate(AuditLogBase):
    """Schema for creating audit logs."""
    
    organization_id: int = Field(..., description="Organization ID")
    user_id: Optional[int] = Field(None, description="User ID who performed the action")


class AuditLogResponse(AuditLogBase):
    """Schema for audit log responses."""
    
    id: int = Field(..., description="Audit log ID")
    organization_id: int = Field(..., description="Organization ID")
    user_id: Optional[int] = Field(None, description="User ID who performed the action")
    created_at: datetime = Field(..., description="When the action was performed")
    
    class Config:
        from_attributes = True


class AIRequestBase(BaseModel):
    """Base AI request schema."""
    
    request_type: str = Field(..., description="Type of AI request")
    model_used: Optional[str] = Field(None, description="AI model used")
    status: str = Field(default="completed", description="Request status")


class AIRequestCreate(AIRequestBase):
    """Schema for creating AI request logs."""
    
    organization_id: int = Field(..., description="Organization ID")
    user_id: Optional[int] = Field(None, description="User ID who made the request")
    prompt_tokens: Optional[str] = Field(None, description="Redacted prompt token count")
    completion_tokens: Optional[str] = Field(None, description="Redacted completion token count")
    total_tokens: Optional[str] = Field(None, description="Redacted total token count")
    processing_time_ms: Optional[str] = Field(None, description="Redacted processing time")
    cost_usd: Optional[str] = Field(None, description="Redacted cost in USD")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class AIRequestResponse(AIRequestBase):
    """Schema for AI request responses."""
    
    id: int = Field(..., description="AI request ID")
    organization_id: int = Field(..., description="Organization ID")
    user_id: Optional[int] = Field(None, description="User ID who made the request")
    prompt_tokens: Optional[str] = Field(None, description="Redacted prompt token count")
    completion_tokens: Optional[str] = Field(None, description="Redacted completion token count")
    total_tokens: Optional[str] = Field(None, description="Redacted total token count")
    processing_time_ms: Optional[str] = Field(None, description="Redacted processing time")
    cost_usd: Optional[str] = Field(None, description="Redacted cost in USD")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="When the request was made")
    
    class Config:
        from_attributes = True


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs."""
    
    organization_id: Optional[int] = Field(None, description="Filter by organization")
    user_id: Optional[int] = Field(None, description="Filter by user")
    action: Optional[str] = Field(None, description="Filter by action")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


class AuditLogSummary(BaseModel):
    """Schema for audit log summary statistics."""
    
    total_actions: int = Field(..., description="Total number of actions")
    actions_by_type: Dict[str, int] = Field(..., description="Count of actions by type")
    actions_by_user: Dict[str, int] = Field(..., description="Count of actions by user")
    recent_activity: list[AuditLogResponse] = Field(..., description="Recent audit log entries") 