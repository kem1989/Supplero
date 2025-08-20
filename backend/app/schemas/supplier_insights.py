"""
Pydantic schemas for supplier insights API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class InsightType(str, Enum):
    """Types of insights that can be generated"""
    PORTFOLIO_OVERVIEW = "portfolio_overview"
    RISK_TRENDS = "risk_trends"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    PREDICTIVE_ANALYSIS = "predictive_analysis"
    BENCHMARK_ANALYSIS = "benchmark_analysis"
    EMERGING_RISKS = "emerging_risks"


class TrendDirection(str, Enum):
    """Direction of trend analysis"""
    IMPROVING = "improving"
    DETERIORATING = "deteriorating"
    STABLE = "stable"


class ImpactLevel(str, Enum):
    """Impact level for insights"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PeerComparison(str, Enum):
    """Peer comparison categories"""
    ABOVE_AVERAGE = "above_average"
    BELOW_AVERAGE = "below_average"
    AVERAGE = "average"


# Request Schemas
class SupplierInsightsRequest(BaseModel):
    """Request schema for generating supplier insights"""
    supplier_ids: Optional[List[int]] = Field(None, description="Specific supplier IDs to analyze (None for all)")
    insight_types: List[InsightType] = Field(
        default=[InsightType.PORTFOLIO_OVERVIEW],
        description="Types of insights to generate"
    )
    time_period_days: int = Field(
        default=90,
        ge=30,
        le=365,
        description="Analysis time period in days"
    )
    include_predictions: bool = Field(
        default=True,
        description="Whether to include predictive analytics"
    )
    include_benchmarks: bool = Field(
        default=True,
        description="Whether to include industry benchmarks"
    )
    include_external_data: bool = Field(
        default=True,
        description="Whether to include external data analysis"
    )


# Response Schemas
class TrendAnalysisSchema(BaseModel):
    """Schema for trend analysis results"""
    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: TrendDirection
    confidence_score: float = Field(ge=0.0, le=1.0)
    time_period_days: int
    key_factors: List[str]


class RiskPredictionSchema(BaseModel):
    """Schema for risk prediction results"""
    supplier_id: int
    supplier_name: str
    current_risk_score: float = Field(ge=0.0, le=100.0)
    predicted_risk_score: float = Field(ge=0.0, le=100.0)
    prediction_timeframe_days: int
    confidence_score: float = Field(ge=0.0, le=1.0)
    risk_factors: List[str]
    early_warning_signals: List[str]
    recommended_actions: List[str]


class PortfolioInsightSchema(BaseModel):
    """Schema for portfolio-level insights"""
    insight_type: str
    title: str
    description: str
    impact_level: ImpactLevel
    affected_suppliers: List[int]
    financial_impact_estimate: Optional[float] = None
    recommended_actions: List[str]
    urgency_score: float = Field(ge=0.0, le=1.0)
    supporting_data: Dict[str, Any]


class BenchmarkAnalysisSchema(BaseModel):
    """Schema for industry benchmark analysis"""
    supplier_id: int
    supplier_name: str
    industry: str
    risk_score: float = Field(ge=0.0, le=100.0)
    industry_average: float = Field(ge=0.0, le=100.0)
    industry_median: float = Field(ge=0.0, le=100.0)
    percentile_rank: float = Field(ge=0.0, le=100.0)
    peer_comparison: PeerComparison
    benchmark_insights: List[str]


class EmergingRiskSchema(BaseModel):
    """Schema for emerging risk detection"""
    supplier_id: int
    supplier_name: str
    risk_type: str
    severity: str
    description: str
    signals: List[Dict[str, Any]]
    recommended_actions: List[str]


class PerformancePatternSchema(BaseModel):
    """Schema for performance pattern analysis"""
    risk_score_distribution: Dict[str, int]
    industry_performance: Dict[str, Dict[str, Any]]
    geographic_performance: Dict[str, Dict[str, Any]]
    size_correlation: Dict[str, Any]
    improvement_trends: List[str]
    deterioration_trends: List[str]


class KeyMetricsSchema(BaseModel):
    """Schema for key portfolio metrics"""
    total_suppliers: int
    average_risk_score: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    improving_trends: int
    deteriorating_trends: int
    stable_trends: int
    watchlisted_suppliers: int
    industries_represented: int
    countries_represented: int


class AnalysisSummarySchema(BaseModel):
    """Schema for analysis summary"""
    total_suppliers_analyzed: int
    analysis_period_days: int
    portfolio_health_score: float = Field(ge=0.0, le=100.0)
    analysis_timestamp: str


class SupplierInsightsResponse(BaseModel):
    """Comprehensive response schema for supplier insights"""
    analysis_summary: AnalysisSummarySchema
    trend_analysis: List[TrendAnalysisSchema]
    portfolio_insights: List[PortfolioInsightSchema]
    emerging_risks: List[EmergingRiskSchema]
    performance_patterns: PerformancePatternSchema
    strategic_recommendations: List[str]
    key_metrics: KeyMetricsSchema
    risk_predictions: Optional[List[RiskPredictionSchema]] = None
    benchmark_analysis: Optional[List[BenchmarkAnalysisSchema]] = None


# Specialized Response Schemas
class TrendAnalysisResponse(BaseModel):
    """Response schema for trend analysis only"""
    analysis_summary: AnalysisSummarySchema
    trend_analysis: List[TrendAnalysisSchema]
    recommendations: List[str]


class PredictiveAnalysisResponse(BaseModel):
    """Response schema for predictive analysis"""
    analysis_summary: AnalysisSummarySchema
    risk_predictions: List[RiskPredictionSchema]
    emerging_risks: List[EmergingRiskSchema]
    recommendations: List[str]


class BenchmarkAnalysisResponse(BaseModel):
    """Response schema for benchmark analysis"""
    analysis_summary: AnalysisSummarySchema
    benchmark_analysis: List[BenchmarkAnalysisSchema]
    industry_insights: Dict[str, Any]
    recommendations: List[str]


class PortfolioHealthResponse(BaseModel):
    """Response schema for portfolio health assessment"""
    portfolio_health_score: float = Field(ge=0.0, le=100.0)
    health_category: str  # "excellent", "good", "fair", "poor", "critical"
    key_metrics: KeyMetricsSchema
    health_factors: List[str]
    improvement_opportunities: List[str]
    analysis_timestamp: str


# Utility Schemas
class InsightFilter(BaseModel):
    """Schema for filtering insights"""
    industries: Optional[List[str]] = None
    countries: Optional[List[str]] = None
    risk_levels: Optional[List[str]] = None
    company_sizes: Optional[List[str]] = None
    min_risk_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    max_risk_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    watchlisted_only: bool = False
    active_only: bool = True


class InsightExportRequest(BaseModel):
    """Request schema for exporting insights"""
    insight_types: List[InsightType]
    format: str = Field(default="json", pattern="^(json|csv|excel|pdf)$")
    include_charts: bool = Field(default=True, description="Include charts in export")
    include_raw_data: bool = Field(default=False, description="Include raw data")
    filters: Optional[InsightFilter] = None


class InsightSubscriptionRequest(BaseModel):
    """Request schema for insight subscriptions/alerts"""
    insight_types: List[InsightType]
    frequency: str = Field(pattern="^(daily|weekly|monthly)$")
    email_recipients: List[str] = Field(min_items=1)
    threshold_conditions: Optional[Dict[str, Any]] = None
    filters: Optional[InsightFilter] = None


# Error Schemas
class InsightError(BaseModel):
    """Schema for insight generation errors"""
    error_code: str
    error_message: str
    failed_suppliers: Optional[List[int]] = None
    partial_results: bool = False
    recommendations: List[str] = []


# Configuration Schemas
class InsightConfiguration(BaseModel):
    """Schema for insight generation configuration"""
    enable_external_data: bool = True
    enable_predictions: bool = True
    enable_benchmarks: bool = True
    prediction_horizon_days: int = Field(default=90, ge=30, le=365)
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_suppliers_per_request: int = Field(default=100, ge=1, le=1000)
    cache_results_hours: int = Field(default=24, ge=1, le=168)  # 1 week max
