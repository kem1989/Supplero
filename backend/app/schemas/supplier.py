"""
Supplier schemas for API request/response handling.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CompanySize(str, Enum):
    """Company size enumeration."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class SupplierCreate(BaseModel):
    """Schema for creating a new supplier."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Supplier company name")
    industry: Optional[str] = Field(None, max_length=100, description="Primary industry")
    location: Optional[str] = Field(None, max_length=255, description="City/region")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    
    # Contact information
    contact_email: Optional[str] = Field(None, max_length=255, description="Primary contact email")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Primary contact phone")
    website: Optional[str] = Field(None, max_length=255, description="Company website")
    address: Optional[str] = Field(None, description="Full address")
    
    # Business information
    company_size: Optional[CompanySize] = Field(None, description="Company size category")
    revenue_range: Optional[str] = Field(None, max_length=100, description="Annual revenue range")
    employee_count: Optional[int] = Field(None, ge=1, description="Number of employees")
    
    # Integration data
    external_id: Optional[str] = Field(None, max_length=255, description="External system ID")
    source_system: Optional[str] = Field(None, max_length=100, description="Source system name")
    
    # Organization context (will be set from auth context)
    organization_id: Optional[int] = Field(None, description="Organization ID")


class SupplierUpdate(BaseModel):
    """Schema for updating an existing supplier."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=100)
    
    # Contact information
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None)
    
    # Business information
    company_size: Optional[CompanySize] = Field(None)
    revenue_range: Optional[str] = Field(None, max_length=100)
    employee_count: Optional[int] = Field(None, ge=1)
    
    # Risk management
    is_watchlisted: Optional[bool] = Field(None)
    watchlist_reason: Optional[str] = Field(None)
    
    # Integration data
    external_id: Optional[str] = Field(None, max_length=255)
    source_system: Optional[str] = Field(None, max_length=100)


class SupplierResponse(BaseModel):
    """Schema for supplier response."""
    
    id: int
    name: str
    industry: Optional[str]
    location: Optional[str]
    country: Optional[str]
    
    # Contact information
    contact_email: Optional[str]
    contact_phone: Optional[str]
    website: Optional[str]
    address: Optional[str]
    
    # Business information
    company_size: Optional[str]
    revenue_range: Optional[str]
    employee_count: Optional[int]
    
    # Risk assessment
    risk_score: float
    risk_level: str
    risk_factors: Optional[Dict[str, Any]]
    
    # Integration data
    external_id: Optional[str]
    source_system: Optional[str]
    
    # Status
    is_active: bool
    is_watchlisted: bool
    watchlist_reason: Optional[str]
    
    # Organization
    organization_id: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_risk_assessment: Optional[datetime]
    
    class Config:
        from_attributes = True


class SupplierRiskResponse(BaseModel):
    """Schema for supplier risk assessment response."""
    
    supplier_id: int
    supplier_name: str
    risk_score: float
    risk_level: str
    risk_factors: Optional[Dict[str, Any]]
    last_assessment: Optional[datetime]
    assessment_method: Optional[str]
    
    # Risk breakdown
    news_sentiment: Optional[float]
    financial_health: Optional[str]
    compliance_status: Optional[str]
    
    # Recommendations
    recommendations: Optional[List[str]] = Field(default_factory=list)
    watchlist_status: bool
    alert_level: str = Field(..., description="Alert level: INFO, WARNING, ALERT, CRITICAL")

    # External data (optional, present for enhanced assessments)
    latest_news: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of recent relevant news articles with basic metadata (title, url, source, published_at, sentiment_score, relevance_score, risk_keywords)"
    )


class SupplierListResponse(BaseModel):
    """Schema for supplier list response with pagination."""
    
    suppliers: List[SupplierResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class RiskAssessmentCreate(BaseModel):
    """Schema for creating a new risk assessment."""
    
    supplier_id: int = Field(..., description="Supplier ID to assess")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Risk score (0-100)")
    risk_level: RiskLevel = Field(..., description="Risk level")
    risk_factors: Optional[Dict[str, Any]] = Field(None, description="Detailed risk factors")
    assessment_method: str = Field(..., max_length=100, description="Assessment method used")
    
    # Data sources
    data_sources: Optional[List[str]] = Field(None, description="Data sources used")
    news_sentiment: Optional[float] = Field(None, ge=-1.0, le=1.0, description="News sentiment score")
    financial_health: Optional[str] = Field(None, max_length=50, description="Financial health status")
    compliance_status: Optional[str] = Field(None, max_length=50, description="Compliance status")
    
    # Assessment metadata
    assessed_by: Optional[str] = Field(None, max_length=100, description="Who performed assessment")
    notes: Optional[str] = Field(None, description="Assessment notes")


class RiskAssessmentResponse(BaseModel):
    """Schema for risk assessment response."""
    
    id: int
    supplier_id: int
    risk_score: float
    risk_level: str
    risk_factors: Optional[Dict[str, Any]]
    assessment_method: str
    data_sources: Optional[List[str]]
    news_sentiment: Optional[float]
    financial_health: Optional[str]
    compliance_status: Optional[str]
    assessed_by: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

