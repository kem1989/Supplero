"""
Supplier search schemas for API request/response handling.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum


class SortOptions(str, Enum):
    """Available sorting options for supplier search."""
    NAME = "name"
    RISK_SCORE = "risk_score"
    RISK_LEVEL = "risk_level"
    INDUSTRY = "industry"
    LOCATION = "location"
    COUNTRY = "country"
    COMPANY_SIZE = "company_size"
    LAST_ASSESSMENT = "last_assessment"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class SupplierSearchFilters(BaseModel):
    """Filters for supplier search."""
    
    supplier_name: Optional[str] = Field(None, description="Filter by supplier name (partial match)")
    industry: Optional[str] = Field(None, description="Filter by industry")
    location: Optional[str] = Field(None, description="Filter by location")
    country: Optional[str] = Field(None, description="Filter by country")
    risk_level: Optional[Union[str, List[str]]] = Field(None, description="Filter by risk level(s)")
    company_size: Optional[Union[str, List[str]]] = Field(None, description="Filter by company size(s)")
    risk_score_min: Optional[float] = Field(None, ge=0.0, le=100.0, description="Minimum risk score")
    risk_score_max: Optional[float] = Field(None, ge=0.0, le=100.0, description="Maximum risk score")
    employee_count_min: Optional[int] = Field(None, ge=1, description="Minimum employee count")
    employee_count_max: Optional[int] = Field(None, ge=1, description="Maximum employee count")
    is_watchlisted: Optional[bool] = Field(None, description="Filter by watchlist status")
    has_contracts: Optional[bool] = Field(None, description="Filter suppliers with/without contracts")
    contract_count_min: Optional[int] = Field(None, ge=0, description="Minimum number of contracts")
    last_assessment_after: Optional[datetime] = Field(None, description="Last assessment after date")
    last_assessment_before: Optional[datetime] = Field(None, description="Last assessment before date")
    
    @validator('risk_score_max')
    def validate_risk_score_range(cls, v, values):
        """Validate that max risk score is greater than min."""
        if v is not None and 'risk_score_min' in values and values['risk_score_min'] is not None:
            if v < values['risk_score_min']:
                raise ValueError('risk_score_max must be greater than or equal to risk_score_min')
        return v
    
    @validator('employee_count_max')
    def validate_employee_count_range(cls, v, values):
        """Validate that max employee count is greater than min."""
        if v is not None and 'employee_count_min' in values and values['employee_count_min'] is not None:
            if v < values['employee_count_min']:
                raise ValueError('employee_count_max must be greater than or equal to employee_count_min')
        return v


class SupplierSearchRequest(BaseModel):
    """Request schema for supplier search."""
    
    query: Optional[str] = Field(None, description="Natural language search query")
    filters: Optional[SupplierSearchFilters] = Field(None, description="Search filters")
    sort_by: SortOptions = Field(SortOptions.NAME, description="Sort field")
    sort_order: SortOrder = Field(SortOrder.ASC, description="Sort order")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Number of results per page")
    include_contract_stats: bool = Field(True, description="Include contract statistics")
    include_risk_details: bool = Field(False, description="Include detailed risk factors")


class SupplierSearchResult(BaseModel):
    """Single supplier search result."""
    
    id: int
    name: str
    industry: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    company_size: Optional[str] = None
    employee_count: Optional[int] = None
    revenue_range: Optional[str] = None
    risk_score: float
    risk_level: str
    risk_factors: Optional[Dict[str, Any]] = None
    is_active: bool
    is_watchlisted: bool
    watchlist_reason: Optional[str] = None
    last_risk_assessment: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Search-specific fields
    relevance_score: float = Field(description="Relevance to search query (0.0-1.0)")
    contract_count: Optional[int] = Field(None, description="Number of associated contracts")
    total_contract_value: Optional[float] = Field(None, description="Total value of contracts")
    latest_contract_date: Optional[datetime] = Field(None, description="Date of most recent contract")
    
    # Risk indicators
    alert_level: Optional[str] = Field(None, description="Alert level based on risk score")
    days_since_assessment: Optional[int] = Field(None, description="Days since last risk assessment")
    
    class Config:
        from_attributes = True


class SearchStatistics(BaseModel):
    """Statistics about the search results."""
    
    total_suppliers_in_org: int = Field(description="Total suppliers in organization")
    matched_suppliers: int = Field(description="Number of suppliers matching search")
    risk_level_distribution: Dict[str, int] = Field(description="Distribution by risk level")
    industry_distribution: Dict[str, int] = Field(description="Distribution by industry")
    country_distribution: Dict[str, int] = Field(description="Distribution by country")
    company_size_distribution: Dict[str, int] = Field(description="Distribution by company size")
    average_risk_score: float = Field(description="Average risk score of matched suppliers")
    watchlisted_suppliers: int = Field(description="Number of watchlisted suppliers in results")


class SupplierSearchResponse(BaseModel):
    """Response schema for supplier search."""
    
    suppliers: List[SupplierSearchResult]
    total_count: int = Field(description="Total number of matching suppliers")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of results per page")
    total_pages: int = Field(description="Total number of pages")
    search_time_ms: float = Field(description="Search execution time in milliseconds")
    performance_met: bool = Field(description="Whether search met performance threshold")
    statistics: SearchStatistics = Field(description="Search result statistics")
    filters_applied: List[str] = Field(description="Summary of applied filters")
    query_used: str = Field(description="Search query that was executed")


class SupplierSearchSuggestion(BaseModel):
    """Search suggestion for autocomplete."""
    
    text: str = Field(description="Suggested search text")
    type: str = Field(description="Type of suggestion (name, industry, location, etc.)")
    count: Optional[int] = Field(None, description="Number of suppliers matching this suggestion")


class SupplierSearchSuggestionsResponse(BaseModel):
    """Response schema for search suggestions."""
    
    suggestions: List[SupplierSearchSuggestion]
    query: str = Field(description="Partial query used for suggestions")


class PopularSearchesResponse(BaseModel):
    """Response schema for popular searches."""
    
    searches: List[str] = Field(description="List of popular search queries")


# Semantic search specific schemas
class SemanticSearchRequest(BaseModel):
    """Request for semantic supplier search."""
    
    query: str = Field(..., min_length=1, max_length=500, description="Natural language query")
    max_results: int = Field(20, ge=1, le=100, description="Maximum number of results")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    include_snippets: bool = Field(True, description="Include text snippets in results")


class SemanticSearchResult(BaseModel):
    """Result from semantic search."""
    
    supplier_id: int
    supplier_name: str
    similarity_score: float = Field(description="Semantic similarity score (0.0-1.0)")
    matched_fields: List[str] = Field(description="Fields that contributed to the match")
    snippets: Optional[List[str]] = Field(None, description="Relevant text snippets")
    metadata: Dict[str, Any] = Field(description="Additional supplier metadata")


class SemanticSearchResponse(BaseModel):
    """Response for semantic search."""
    
    results: List[SemanticSearchResult]
    query: str = Field(description="Original search query")
    total_results: int = Field(description="Total number of results found")
    search_time_ms: float = Field(description="Search execution time")
    semantic_analysis: Dict[str, Any] = Field(description="Analysis of the search query")


# AI-powered search insights
class SearchInsights(BaseModel):
    """AI-generated insights about search results."""
    
    summary: str = Field(description="Summary of search results")
    key_trends: List[str] = Field(description="Key trends identified in results")
    risk_assessment: str = Field(description="Overall risk assessment of results")
    recommendations: List[str] = Field(description="Recommendations based on results")
    outliers: List[Dict[str, Any]] = Field(description="Suppliers that stand out")


class EnhancedSupplierSearchResponse(SupplierSearchResponse):
    """Enhanced search response with AI insights."""
    
    insights: Optional[SearchInsights] = Field(None, description="AI-generated insights")
    similar_searches: List[str] = Field(description="Similar search queries")
    export_options: List[str] = Field(description="Available export formats")
