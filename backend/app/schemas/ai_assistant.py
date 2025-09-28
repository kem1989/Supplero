"""
AI Assistant schemas for natural language query processing.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class IntentType(str, Enum):
    """Simplified intent types for natural language to SQL conversion"""
    
    # Core SQL-based intents - all queries go through SQL generation
    SQL_QUERY = "SQL_QUERY"  # Generic SQL query for any data request
    SQL_ANALYTICS = "SQL_ANALYTICS"  # Analytics and reporting queries
    SQL_COMPLEX_QUERY = "SQL_COMPLEX_QUERY"  # Complex cross-system queries
    
    # Specialized intents for better SQL generation context
    CONTRACT_QUERY = "CONTRACT_QUERY"  # Contract-related queries
    # SUPPLIER_QUERY removed - now handled by SQL_QUERY
    RISK_ANALYSIS = "RISK_ANALYSIS"  # Risk analysis queries
    COMPARISON_QUERY = "COMPARISON_QUERY"  # Comparison queries
    
    # Multi-part query intents (simplified)
    GENERATE_EXPLANATION = "GENERATE_EXPLANATION"
    GENERATE_INSIGHTS = "GENERATE_INSIGHTS"
    
    UNKNOWN = "UNKNOWN"


class APICreditUsage(BaseModel):
    """API credit usage information"""
    model_config = {"protected_namespaces": ()}
    
    model_name: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    processing_time_ms: Optional[int] = None


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
    api_credit_usage: Optional[APICreditUsage] = None


# Simplified SQL-based query schemas
class SQLQueryRequest(BaseModel):
    """Request schema for SQL-based queries"""
    query: str = Field(..., description="Natural language query")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class SQLQueryResponse(BaseModel):
    """Response schema for SQL-based queries"""
    message: str
    results: List[Dict[str, Any]]
    total_found: int
    sql_query: str
    query_confidence: float
    query_complexity: str
    execution_time_ms: float
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
    api_credit_usage: Optional[APICreditUsage] = None


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


# Multi-part query schemas (simplified)
class MultiPartQueryResponse(BaseModel):
    """Response schema for multi-part queries"""
    query: str
    is_multi_part: bool
    success: bool
    timestamp: str
    execution_time_ms: float
    intent_classification: Dict[str, Any]
    results: Dict[str, Any]
    summary: Dict[str, Any]
    error: Optional[str] = None
