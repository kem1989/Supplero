"""
Pydantic schemas for Cross-System Intelligence API.

These schemas define the request and response models for the enhanced intelligence
capabilities in Phase 2 of the supplier build.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum


class IntelligenceQueryTypeSchema(str, Enum):
    """Available intelligence query types."""
    PORTFOLIO_RISK_ANALYSIS = "PORTFOLIO_RISK_ANALYSIS"
    GEOGRAPHIC_RISK_CLUSTERING = "GEOGRAPHIC_RISK_CLUSTERING"
    INDUSTRY_RISK_CLUSTERING = "INDUSTRY_RISK_CLUSTERING"
    CONTRACT_IMPACT_ASSESSMENT = "CONTRACT_IMPACT_ASSESSMENT"
    SUPPLIER_TREND_ANALYSIS = "SUPPLIER_TREND_ANALYSIS"
    PREDICTIVE_RISK_MODELING = "PREDICTIVE_RISK_MODELING"
    CROSS_SYSTEM_CORRELATION = "CROSS_SYSTEM_CORRELATION"
    INTELLIGENT_RECOMMENDATIONS = "INTELLIGENT_RECOMMENDATIONS"


class IntelligenceRequestSchema(BaseModel):
    """Request schema for intelligence analysis."""
    
    query_type: IntelligenceQueryTypeSchema = Field(
        ..., 
        description="Type of intelligence analysis to perform"
    )
    
    query_text: Optional[str] = Field(
        None,
        description="Optional natural language query text",
        max_length=500
    )
    
    # Filtering options
    supplier_ids: Optional[List[int]] = Field(
        None,
        description="Specific suppliers to analyze"
    )
    
    industries: Optional[List[str]] = Field(
        None,
        description="Industries to include in analysis"
    )
    
    countries: Optional[List[str]] = Field(
        None,
        description="Countries to include in analysis"
    )
    
    risk_levels: Optional[List[str]] = Field(
        None,
        description="Risk levels to include (LOW, MEDIUM, HIGH, CRITICAL)"
    )
    
    # Time range for analysis
    analysis_start_date: Optional[datetime] = Field(
        None,
        description="Start date for historical analysis"
    )
    
    analysis_end_date: Optional[datetime] = Field(
        None,
        description="End date for historical analysis"
    )
    
    # Analysis parameters
    include_predictions: bool = Field(
        True,
        description="Include predictive analysis in results"
    )
    
    include_recommendations: bool = Field(
        True,
        description="Include AI-powered recommendations"
    )
    
    confidence_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for analysis results"
    )
    
    max_results: int = Field(
        50,
        ge=1,
        le=200,
        description="Maximum number of results to return"
    )
    
    @validator('risk_levels')
    def validate_risk_levels(cls, v):
        if v is not None:
            valid_levels = {'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'}
            for level in v:
                if level.upper() not in valid_levels:
                    raise ValueError(f"Invalid risk level: {level}")
            return [level.upper() for level in v]
        return v
    
    @validator('analysis_end_date')
    def validate_date_range(cls, v, values):
        if v is not None and 'analysis_start_date' in values and values['analysis_start_date'] is not None:
            if v <= values['analysis_start_date']:
                raise ValueError("End date must be after start date")
        return v


class PortfolioAnalysisSchema(BaseModel):
    """Portfolio analysis results schema."""
    
    total_suppliers: int = Field(..., description="Total number of suppliers")
    total_contract_value: float = Field(..., description="Total contract value")
    risk_distribution: Dict[str, int] = Field(..., description="Risk level distribution")
    geographic_distribution: Dict[str, int] = Field(..., description="Geographic distribution")
    industry_distribution: Dict[str, int] = Field(..., description="Industry distribution")
    
    # Portfolio-level metrics
    portfolio_risk_score: float = Field(
        ..., 
        ge=0.0, 
        le=10.0, 
        description="Overall portfolio risk score"
    )
    diversification_index: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Portfolio diversification index"
    )
    concentration_risk: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Portfolio concentration risk"
    )
    
    # Risk trends
    risk_trend_30d: str = Field(..., description="30-day risk trend")
    risk_trend_90d: str = Field(..., description="90-day risk trend")
    risk_trend_365d: str = Field(..., description="365-day risk trend")
    
    # Key insights
    top_risk_contributors: List[Dict[str, Any]] = Field(
        ..., 
        description="Top risk contributing suppliers"
    )
    optimization_opportunities: List[str] = Field(
        ..., 
        description="Portfolio optimization opportunities"
    )
    strategic_recommendations: List[str] = Field(
        ..., 
        description="Strategic recommendations"
    )
    
    # Predictive indicators
    suppliers_at_risk: List[int] = Field(..., description="Supplier IDs at risk")
    contracts_requiring_attention: List[int] = Field(
        ..., 
        description="Contract IDs requiring attention"
    )
    emerging_risk_areas: List[str] = Field(..., description="Emerging risk areas")


class GeographicClusterSchema(BaseModel):
    """Geographic risk cluster schema."""
    
    region: str = Field(..., description="Geographic region name")
    country_codes: List[str] = Field(..., description="Country codes in cluster")
    supplier_count: int = Field(..., description="Number of suppliers in region")
    average_risk_score: float = Field(
        ..., 
        ge=0.0, 
        le=10.0, 
        description="Average risk score for region"
    )
    total_contract_value: float = Field(..., description="Total contract value in region")
    risk_factors: List[str] = Field(..., description="Regional risk factors")
    trend_direction: str = Field(..., description="Risk trend direction")
    risk_level: str = Field(..., description="Overall regional risk level")
    
    # Specific risk indicators
    political_risk: float = Field(..., ge=0.0, le=10.0, description="Political risk score")
    economic_risk: float = Field(..., ge=0.0, le=10.0, description="Economic risk score")
    regulatory_risk: float = Field(..., ge=0.0, le=10.0, description="Regulatory risk score")
    natural_disaster_risk: float = Field(
        ..., 
        ge=0.0, 
        le=10.0, 
        description="Natural disaster risk score"
    )
    
    # Recommendations
    mitigation_strategies: List[str] = Field(..., description="Risk mitigation strategies")
    monitoring_priorities: List[str] = Field(..., description="Monitoring priorities")


class IndustryClusterSchema(BaseModel):
    """Industry risk cluster schema."""
    
    industry: str = Field(..., description="Industry name")
    sub_industries: List[str] = Field(..., description="Sub-industries included")
    supplier_count: int = Field(..., description="Number of suppliers in industry")
    average_risk_score: float = Field(
        ..., 
        ge=0.0, 
        le=10.0, 
        description="Average risk score for industry"
    )
    total_contract_value: float = Field(..., description="Total contract value in industry")
    market_volatility: float = Field(..., description="Market volatility measure")
    regulatory_burden: str = Field(..., description="Regulatory burden level")
    
    # Risk factors specific to industry
    supply_chain_risk: float = Field(..., ge=0.0, le=10.0, description="Supply chain risk")
    technology_disruption_risk: float = Field(
        ..., 
        ge=0.0, 
        le=10.0, 
        description="Technology disruption risk"
    )
    regulatory_change_risk: float = Field(
        ..., 
        ge=0.0, 
        le=10.0, 
        description="Regulatory change risk"
    )
    market_demand_risk: float = Field(..., ge=0.0, le=10.0, description="Market demand risk")
    
    # Trends and predictions
    growth_outlook: str = Field(..., description="Industry growth outlook")
    emerging_risks: List[str] = Field(..., description="Emerging risks in industry")
    opportunities: List[str] = Field(..., description="Opportunities in industry")


class ContractImpactSchema(BaseModel):
    """Contract impact assessment schema."""
    
    supplier_id: int = Field(..., description="Supplier ID")
    supplier_name: str = Field(..., description="Supplier name")
    base_risk_score: float = Field(
        ..., 
        ge=0.0, 
        le=10.0, 
        description="Base supplier risk score"
    )
    contract_adjusted_risk_score: float = Field(
        ..., 
        ge=0.0, 
        le=10.0, 
        description="Contract-adjusted risk score"
    )
    impact_magnitude: float = Field(..., description="Impact magnitude of contracts")
    
    # Contract-specific factors
    high_risk_clauses: List[Dict[str, Any]] = Field(
        ..., 
        description="High-risk contract clauses"
    )
    contract_concentration: float = Field(..., description="Contract concentration factor")
    value_exposure: float = Field(..., description="Total value exposure")
    expiry_risk: float = Field(..., ge=0.0, le=1.0, description="Contract expiry risk")
    
    # Risk explanation
    risk_drivers: List[str] = Field(..., description="Primary risk drivers")
    mitigation_suggestions: List[str] = Field(..., description="Risk mitigation suggestions")
    monitoring_requirements: List[str] = Field(..., description="Monitoring requirements")


class TrendAnalysisSchema(BaseModel):
    """Supplier trend analysis schema."""
    
    supplier_id: int = Field(..., description="Supplier ID")
    supplier_name: str = Field(..., description="Supplier name")
    
    # Historical trends (as string tuples for JSON serialization)
    risk_score_trend: List[Tuple[str, float]] = Field(
        ..., 
        description="Risk score trend over time"
    )
    contract_value_trend: List[Tuple[str, float]] = Field(
        ..., 
        description="Contract value trend over time"
    )
    performance_trend: List[Tuple[str, float]] = Field(
        ..., 
        description="Performance trend over time"
    )
    
    # Trend indicators
    risk_direction: str = Field(..., description="Risk direction (improving/deteriorating/stable)")
    velocity: float = Field(..., description="Rate of change")
    acceleration: float = Field(..., description="Change in rate of change")
    
    # Predictions
    predicted_risk_30d: float = Field(
        ..., 
        ge=0.0, 
        le=10.0, 
        description="Predicted risk in 30 days"
    )
    predicted_risk_90d: float = Field(
        ..., 
        ge=0.0, 
        le=10.0, 
        description="Predicted risk in 90 days"
    )
    confidence_interval: Tuple[float, float] = Field(
        ..., 
        description="Confidence interval for predictions"
    )
    
    # Alerts
    trend_alerts: List[str] = Field(..., description="Trend-based alerts")
    recommended_actions: List[str] = Field(..., description="Recommended actions")


class IntelligenceResponseSchema(BaseModel):
    """Intelligence analysis response schema."""
    
    query_type: str = Field(..., description="Type of analysis performed")
    analysis_timestamp: datetime = Field(..., description="When analysis was performed")
    
    # Core analysis results (optional based on query type)
    portfolio_analysis: Optional[PortfolioAnalysisSchema] = Field(
        None, 
        description="Portfolio analysis results"
    )
    geographic_clusters: List[GeographicClusterSchema] = Field(
        default_factory=list,
        description="Geographic risk clusters"
    )
    industry_clusters: List[IndustryClusterSchema] = Field(
        default_factory=list,
        description="Industry risk clusters"
    )
    contract_impacts: List[ContractImpactSchema] = Field(
        default_factory=list,
        description="Contract impact assessments"
    )
    trend_analyses: List[TrendAnalysisSchema] = Field(
        default_factory=list,
        description="Trend analysis results"
    )
    
    # AI-generated insights
    key_insights: List[str] = Field(
        default_factory=list,
        description="Key insights from analysis"
    )
    strategic_recommendations: List[str] = Field(
        default_factory=list,
        description="Strategic recommendations"
    )
    risk_alerts: List[str] = Field(
        default_factory=list,
        description="Risk alerts requiring attention"
    )
    opportunities: List[str] = Field(
        default_factory=list,
        description="Identified opportunities"
    )
    
    # Performance metrics
    analysis_time_ms: float = Field(..., description="Analysis time in milliseconds")
    confidence_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Overall confidence in analysis"
    )
    data_quality_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Quality of underlying data"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class IntelligenceErrorSchema(BaseModel):
    """Error response schema for intelligence API."""
    
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Additional utility schemas

class QueryTypeInfoSchema(BaseModel):
    """Information about a specific query type."""
    
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Detailed description")
    examples: List[str] = Field(..., description="Example queries")
    parameters: List[str] = Field(..., description="Available parameters")


class AvailableQueryTypesSchema(BaseModel):
    """Available query types response."""
    
    query_types: Dict[str, QueryTypeInfoSchema] = Field(
        ..., 
        description="Available query types and their information"
    )
    total_count: int = Field(..., description="Total number of available query types")


class HealthCheckSchema(BaseModel):
    """Health check response schema."""
    
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
