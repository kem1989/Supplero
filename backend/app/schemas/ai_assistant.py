"""
AI Assistant schemas for natural language query processing.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class IntentType(str, Enum):
    """Supported intent types for natural language queries"""
    SEARCH_CONTRACTS = "SEARCH_CONTRACTS"
    SEARCH_CLAUSES = "SEARCH_CLAUSES"
    ANALYZE_RISK = "ANALYZE_RISK"
    COMPARE_CLAUSES = "COMPARE_CLAUSES"
    GET_DETAILS = "GET_DETAILS"
    EXPORT = "EXPORT"
    # Supplier-specific intents
    SEARCH_SUPPLIERS = "SEARCH_SUPPLIERS"
    ANALYZE_SUPPLIER_RISK = "ANALYZE_SUPPLIER_RISK"
    COMPARE_SUPPLIERS = "COMPARE_SUPPLIERS"
    SUPPLIER_INSIGHTS = "SUPPLIER_INSIGHTS"
    # Cross-system intents
    SUPPLIERS_WITH_RISKY_CONTRACTS = "SUPPLIERS_WITH_RISKY_CONTRACTS"
    SUPPLIERS_WITH_EXPIRING_CONTRACTS = "SUPPLIERS_WITH_EXPIRING_CONTRACTS"
    SUPPLIERS_BY_CONTRACT_CLAUSES = "SUPPLIERS_BY_CONTRACT_CLAUSES"
    CONTRACTS_BY_SUPPLIER_RISK = "CONTRACTS_BY_SUPPLIER_RISK"
    UNIFIED_RISK_SEARCH = "UNIFIED_RISK_SEARCH"
    UNKNOWN = "UNKNOWN"


class NaturalLanguageQueryRequest(BaseModel):
    """Request schema for natural language query processing"""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")


class NaturalLanguageQueryResponse(BaseModel):
    """Response schema for natural language query processing"""
    query_id: str
    original_query: str
    intent: str
    confidence: float
    parameters: Dict[str, Any]
    confidence_threshold_met: bool
    suggested_actions: List[str]
    error_message: Optional[str] = None


class UnifiedQueryRequest(BaseModel):
    """Request schema for unified query execution"""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class UnifiedQueryResponse(BaseModel):
    """Response schema for unified query execution"""
    query_id: str
    original_query: str
    intent: str
    confidence: float
    parameters: Dict[str, Any]
    execution_result: Dict[str, Any]
    execution_time_ms: float
    performance_met: bool


# Supplier-specific query schemas
class SupplierSearchQueryRequest(BaseModel):
    """Request schema for supplier search queries"""
    query: str = Field(..., description="Natural language supplier search query")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional filters")


class SupplierSearchResult(BaseModel):
    """Single supplier search result"""
    id: int
    name: str
    industry: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    risk_score: float
    risk_level: str
    company_size: Optional[str] = None
    is_watchlisted: bool
    is_active: bool
    last_risk_assessment: Optional[datetime] = None


class SupplierSearchResponse(BaseModel):
    """Response schema for supplier search"""
    message: str
    parameters_used: Dict[str, Any]
    filters_applied: List[str]
    suppliers: List[SupplierSearchResult]
    total_count: int
    performance_met: bool


class SupplierRiskAnalysisRequest(BaseModel):
    """Request schema for supplier risk analysis"""
    query: str = Field(..., description="Natural language risk analysis query")
    supplier_ids: Optional[List[int]] = Field(default=None, description="Specific supplier IDs to analyze")
    include_enhanced: bool = Field(default=False, description="Include enhanced risk analysis with external data")


class SupplierRiskAnalysisResult(BaseModel):
    """Single supplier risk analysis result"""
    supplier_id: int
    supplier_name: str
    current_risk_score: float
    new_risk_score: float
    risk_level: str
    risk_factors: Dict[str, Any]
    recommendations: List[str]
    analysis_method: str


class SupplierRiskAnalysisResponse(BaseModel):
    """Response schema for supplier risk analysis"""
    message: str
    parameters_used: Dict[str, Any]
    risk_analyses: List[SupplierRiskAnalysisResult]
    analysis_summary: Dict[str, Any]
    performance_met: bool


class SupplierComparisonRequest(BaseModel):
    """Request schema for supplier comparison"""
    query: str = Field(..., description="Natural language comparison query")
    supplier_ids: Optional[List[int]] = Field(default=None, description="Specific supplier IDs to compare")
    comparison_criteria: Optional[List[str]] = Field(default=None, description="Criteria for comparison")


class SupplierComparisonData(BaseModel):
    """Single supplier comparison data"""
    supplier_id: int
    name: str
    industry: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    risk_score: float
    risk_level: str
    company_size: Optional[str] = None
    employee_count: Optional[int] = None
    revenue_range: Optional[str] = None
    is_watchlisted: bool
    last_risk_assessment: Optional[datetime] = None


class SupplierComparisonResponse(BaseModel):
    """Response schema for supplier comparison"""
    message: str
    parameters_used: Dict[str, Any]
    comparison_data: List[SupplierComparisonData]
    comparison_insights: List[str]
    comparison_criteria: List[str]
    performance_met: bool


class SupplierInsightsRequest(BaseModel):
    """Request schema for supplier insights"""
    query: str = Field(..., description="Natural language insights query")
    insight_type: Optional[str] = Field(default="portfolio_overview", description="Type of insights to generate")
    time_period: Optional[str] = Field(default=None, description="Time period for analysis")


class SupplierInsightsResponse(BaseModel):
    """Response schema for supplier insights"""
    message: str
    parameters_used: Dict[str, Any]
    insight_type: str
    insights: Dict[str, Any]
    recommendations: List[str]
    data_quality: Dict[str, Any]
    performance_met: bool


# Tool execution schemas
class ToolExecutionRequest(BaseModel):
    """Request schema for tool execution"""
    tool_name: str
    parameters: Dict[str, Any]


class ToolExecutionResponse(BaseModel):
    """Response schema for tool execution"""
    tool_name: str
    result: Dict[str, Any]
    execution_time_ms: float
    performance_met: bool
    error_message: Optional[str] = None


# Query intent and classification schemas
class QueryIntent(BaseModel):
    """Represents the extracted intent and parameters from a natural language query"""
    intent: IntentType
    confidence: float
    parameters: Dict[str, Any]
    raw_query: str


class IntentClassificationResult(BaseModel):
    """Result of intent classification"""
    intent: IntentType
    confidence: float
    reasoning: Optional[str] = None


# Available tools information schema
class ToolInfo(BaseModel):
    """Information about an available tool"""
    name: str
    description: str
    parameters: Dict[str, str]
    examples: List[str]


class AvailableToolsResponse(BaseModel):
    """Response schema for available tools"""
    tools: List[ToolInfo]
    total_tools: int
    categories: Dict[str, List[str]]
