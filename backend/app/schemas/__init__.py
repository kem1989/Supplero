"""
Pydantic schemas for the Supplero application.
"""

from .auth import UserCreate, UserLogin, UserResponse, TokenResponse, TokenData
from .organization import OrganizationCreate, OrganizationResponse
from .audit import (
    AuditLogBase, AuditLogCreate, AuditLogResponse, 
    AIRequestBase, AIRequestCreate, AIRequestResponse,
    AuditLogFilter, AuditLogSummary
)
# Simplified schemas for SQL-based natural language query processing
from .ai_assistant import (
    IntentType, NaturalLanguageQueryRequest, NaturalLanguageQueryResponse,
    UnifiedQueryRequest, UnifiedQueryResponse, SQLQueryRequest, SQLQueryResponse,
    ToolExecutionRequest, ToolExecutionResponse, QueryIntent, IntentClassificationResult,
    ToolInfo, AvailableToolsResponse, MultiPartQueryResponse
)

__all__ = [
    "UserCreate", "UserLogin", "UserResponse", "TokenResponse", "TokenData",
    "OrganizationCreate", "OrganizationResponse",
    "AuditLogBase", "AuditLogCreate", "AuditLogResponse",
    "AIRequestBase", "AIRequestCreate", "AIRequestResponse",
    "AuditLogFilter", "AuditLogSummary",
    # AI Assistant schemas (simplified)
    "IntentType", "NaturalLanguageQueryRequest", "NaturalLanguageQueryResponse",
    "UnifiedQueryRequest", "UnifiedQueryResponse", "SQLQueryRequest", "SQLQueryResponse",
    "ToolExecutionRequest", "ToolExecutionResponse", "QueryIntent", "IntentClassificationResult",
    "ToolInfo", "AvailableToolsResponse", "MultiPartQueryResponse"
] 