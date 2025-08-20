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
from .document import (
    DocumentUploadRequest, DocumentUploadResponse, DocumentStatusResponse,
    DocumentListResponse, DocumentSearchRequest, DocumentProcessingResult,
    DocumentVersionHistory, ProcessingJobStatus, DocumentFeedbackRequest,
    DocumentFeedbackResponse, DocumentIngestionStats, ExtractedMetadata
)
from .supplier import (
    SupplierCreate, SupplierUpdate, SupplierResponse, SupplierRiskResponse,
    SupplierListResponse, RiskAssessmentCreate, RiskAssessmentResponse,
    RiskLevel, CompanySize
)
from .supplier_search import (
    SupplierSearchRequest, SupplierSearchResponse, SupplierSearchResult,
    SupplierSearchFilters, SortOptions, SortOrder, SearchStatistics,
    SupplierSearchSuggestion, SupplierSearchSuggestionsResponse, PopularSearchesResponse,
    SemanticSearchRequest, SemanticSearchResult, SemanticSearchResponse,
    SearchInsights, EnhancedSupplierSearchResponse
)
from .ai_assistant import (
    IntentType, NaturalLanguageQueryRequest, NaturalLanguageQueryResponse,
    UnifiedQueryRequest, UnifiedQueryResponse, SupplierSearchQueryRequest,
    SupplierSearchResult, SupplierSearchResponse, SupplierRiskAnalysisRequest,
    SupplierRiskAnalysisResult, SupplierRiskAnalysisResponse, SupplierComparisonRequest,
    SupplierComparisonData, SupplierComparisonResponse, SupplierInsightsRequest,
    SupplierInsightsResponse, ToolExecutionRequest, ToolExecutionResponse,
    QueryIntent, IntentClassificationResult, ToolInfo, AvailableToolsResponse
)

__all__ = [
    "UserCreate", "UserLogin", "UserResponse", "TokenResponse", "TokenData",
    "OrganizationCreate", "OrganizationResponse",
    "AuditLogBase", "AuditLogCreate", "AuditLogResponse",
    "AIRequestBase", "AIRequestCreate", "AIRequestResponse",
    "AuditLogFilter", "AuditLogSummary",
    "DocumentUploadRequest", "DocumentUploadResponse", "DocumentStatusResponse",
    "DocumentListResponse", "DocumentSearchRequest", "DocumentProcessingResult",
    "DocumentVersionHistory", "ProcessingJobStatus", "DocumentFeedbackRequest",
    "DocumentFeedbackResponse", "DocumentIngestionStats", "ExtractedMetadata",
    "SupplierCreate", "SupplierUpdate", "SupplierResponse", "SupplierRiskResponse",
    "SupplierListResponse", "RiskAssessmentCreate", "RiskAssessmentResponse",
    "RiskLevel", "CompanySize",
    # Supplier search schemas
    "SupplierSearchRequest", "SupplierSearchResponse", "SupplierSearchResult",
    "SupplierSearchFilters", "SortOptions", "SortOrder", "SearchStatistics",
    "SupplierSearchSuggestion", "SupplierSearchSuggestionsResponse", "PopularSearchesResponse",
    "SemanticSearchRequest", "SemanticSearchResult", "SemanticSearchResponse",
    "SearchInsights", "EnhancedSupplierSearchResponse",
    # AI Assistant schemas
    "IntentType", "NaturalLanguageQueryRequest", "NaturalLanguageQueryResponse",
    "UnifiedQueryRequest", "UnifiedQueryResponse", "SupplierSearchQueryRequest",
    "SupplierSearchResult", "SupplierSearchResponse", "SupplierRiskAnalysisRequest",
    "SupplierRiskAnalysisResult", "SupplierRiskAnalysisResponse", "SupplierComparisonRequest",
    "SupplierComparisonData", "SupplierComparisonResponse", "SupplierInsightsRequest",
    "SupplierInsightsResponse", "ToolExecutionRequest", "ToolExecutionResponse",
    "QueryIntent", "IntentClassificationResult", "ToolInfo", "AvailableToolsResponse"
] 