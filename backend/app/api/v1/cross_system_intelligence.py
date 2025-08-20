"""
Cross-System Intelligence API endpoints for Phase 2 implementation.

This module provides API endpoints for advanced intelligence capabilities that bridge
suppliers and contracts, enabling sophisticated analysis and AI-powered insights.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.cross_system_intelligence import (
    CrossSystemIntelligenceService, 
    IntelligenceRequest, 
    IntelligenceResponse,
    IntelligenceQueryType
)
from app.models.user import User
from app.schemas.cross_system_intelligence import (
    IntelligenceRequestSchema,
    IntelligenceResponseSchema,
    PortfolioAnalysisSchema,
    GeographicClusterSchema,
    IndustryClusterSchema,
    ContractImpactSchema,
    TrendAnalysisSchema
)

logger = structlog.get_logger(__name__)

router = APIRouter()

# Initialize the intelligence service
intelligence_service = CrossSystemIntelligenceService()


@router.post("/analyze", response_model=IntelligenceResponseSchema)
async def execute_intelligence_analysis(
    request: IntelligenceRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> IntelligenceResponseSchema:
    """
    Execute an enhanced intelligence analysis query.
    
    This endpoint provides access to advanced cross-system intelligence capabilities
    including portfolio analysis, geographic clustering, trend analysis, and AI-powered insights.
    
    Args:
        request: Intelligence analysis request
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        IntelligenceResponse with comprehensive analysis results
        
    Raises:
        HTTPException: If analysis fails or user lacks permissions
    """
    try:
        logger.info(
            "Starting intelligence analysis",
            query_type=request.query_type,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            query_text=request.query_text
        )
        
        # Convert schema to service request
        intelligence_request = IntelligenceRequest(
            query_type=IntelligenceQueryType(request.query_type),
            query_text=request.query_text,
            supplier_ids=request.supplier_ids,
            industries=request.industries,
            countries=request.countries,
            risk_levels=request.risk_levels,
            analysis_start_date=request.analysis_start_date,
            analysis_end_date=request.analysis_end_date,
            include_predictions=request.include_predictions,
            include_recommendations=request.include_recommendations,
            confidence_threshold=request.confidence_threshold,
            max_results=request.max_results
        )
        
        # Execute intelligence analysis
        response = await intelligence_service.execute_intelligence_query(
            intelligence_request,
            db,
            current_user.organization_id
        )
        
        logger.info(
            "Intelligence analysis completed",
            query_type=request.query_type,
            analysis_time_ms=response.analysis_time_ms,
            confidence_score=response.confidence_score
        )
        
        # Convert service response to API schema
        return _convert_to_response_schema(response)
        
    except ValueError as e:
        logger.error("Invalid intelligence request", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "Intelligence analysis failed",
            error=str(e),
            user_id=current_user.id,
            query_type=request.query_type,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Intelligence analysis failed. Please try again."
        )


@router.get("/query-types")
async def get_available_query_types(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get available intelligence query types and their descriptions.
    
    Returns:
        Dictionary of available query types with descriptions and examples
    """
    try:
        query_types = {
            "PORTFOLIO_RISK_ANALYSIS": {
                "name": "Portfolio Risk Analysis",
                "description": "Comprehensive supplier portfolio risk analysis with diversification metrics",
                "examples": [
                    "Analyze my supplier portfolio risk",
                    "Show portfolio diversification analysis",
                    "What's my overall supplier risk exposure?"
                ],
                "parameters": [
                    "supplier_ids: Optional list of specific suppliers to analyze",
                    "industries: Optional list of industries to include",
                    "countries: Optional list of countries to include",
                    "include_predictions: Whether to include predictive analysis"
                ]
            },
            "GEOGRAPHIC_RISK_CLUSTERING": {
                "name": "Geographic Risk Clustering",
                "description": "Analyze geographic risk clustering and regional risk factors",
                "examples": [
                    "Analyze geographic risk clusters",
                    "Show regional supplier risk distribution",
                    "Which regions have the highest supplier risk?"
                ],
                "parameters": [
                    "countries: Optional list of countries to focus on",
                    "include_political_risk: Include political risk factors",
                    "include_economic_risk: Include economic risk factors"
                ]
            },
            "INDUSTRY_RISK_CLUSTERING": {
                "name": "Industry Risk Clustering", 
                "description": "Analyze industry risk clustering and sector-specific risk factors",
                "examples": [
                    "Analyze industry risk clusters",
                    "Show sector-specific supplier risks",
                    "Which industries have emerging risks?"
                ],
                "parameters": [
                    "industries: Optional list of industries to focus on",
                    "include_market_volatility: Include market volatility analysis",
                    "include_disruption_risk: Include technology disruption risk"
                ]
            },
            "CONTRACT_IMPACT_ASSESSMENT": {
                "name": "Contract Impact Assessment",
                "description": "Assess how contract risk factors impact supplier risk evaluation",
                "examples": [
                    "How do contracts impact supplier risk scores?",
                    "Assess contract risk impact on supplier evaluation",
                    "Show contract-adjusted supplier risk"
                ],
                "parameters": [
                    "supplier_ids: Optional list of suppliers to assess",
                    "include_clause_analysis: Include contract clause analysis",
                    "risk_threshold: Risk threshold for analysis"
                ]
            },
            "SUPPLIER_TREND_ANALYSIS": {
                "name": "Supplier Trend Analysis",
                "description": "Analyze supplier risk and performance trends over time",
                "examples": [
                    "Show supplier risk trends",
                    "Analyze supplier performance over time",
                    "Which suppliers are improving or deteriorating?"
                ],
                "parameters": [
                    "supplier_ids: Optional list of suppliers to analyze",
                    "analysis_start_date: Start date for trend analysis",
                    "analysis_end_date: End date for trend analysis",
                    "include_predictions: Include future predictions"
                ]
            },
            "PREDICTIVE_RISK_MODELING": {
                "name": "Predictive Risk Modeling",
                "description": "Generate predictive risk scenarios and forecasts",
                "examples": [
                    "Predict future supplier risks",
                    "Generate risk scenario forecasts",
                    "What suppliers might become high-risk?"
                ],
                "parameters": [
                    "prediction_horizon: Time horizon for predictions",
                    "confidence_threshold: Confidence level for predictions",
                    "scenario_types: Types of scenarios to model"
                ]
            },
            "INTELLIGENT_RECOMMENDATIONS": {
                "name": "Intelligent Recommendations",
                "description": "Generate AI-powered strategic recommendations for supplier management",
                "examples": [
                    "Give me strategic supplier recommendations",
                    "What should I do to optimize my supplier portfolio?",
                    "Provide intelligent supplier management advice"
                ],
                "parameters": [
                    "focus_areas: Areas to focus recommendations on",
                    "priority_level: Priority level for recommendations",
                    "include_implementation: Include implementation guidance"
                ]
            }
        }
        
        return {
            "query_types": query_types,
            "total_count": len(query_types)
        }
        
    except Exception as e:
        logger.error("Failed to get query types", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve query types"
        )


@router.post("/portfolio-analysis", response_model=PortfolioAnalysisSchema)
async def analyze_portfolio_risk(
    supplier_ids: Optional[list] = None,
    industries: Optional[list] = None,
    countries: Optional[list] = None,
    include_predictions: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PortfolioAnalysisSchema:
    """
    Analyze supplier portfolio risk with comprehensive metrics.
    
    This is a convenience endpoint for portfolio risk analysis with direct parameters.
    
    Args:
        supplier_ids: Optional list of specific suppliers to analyze
        industries: Optional list of industries to include
        countries: Optional list of countries to include  
        include_predictions: Whether to include predictive analysis
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Portfolio analysis results
    """
    try:
        # Create intelligence request
        request = IntelligenceRequest(
            query_type=IntelligenceQueryType.PORTFOLIO_RISK_ANALYSIS,
            supplier_ids=supplier_ids,
            industries=industries,
            countries=countries,
            include_predictions=include_predictions,
            include_recommendations=True
        )
        
        # Execute analysis
        response = await intelligence_service.execute_intelligence_query(
            request,
            db,
            current_user.organization_id
        )
        
        if not response.portfolio_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No portfolio data found for analysis"
            )
        
        # Convert to schema
        return _convert_portfolio_to_schema(response.portfolio_analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Portfolio analysis failed",
            error=str(e),
            user_id=current_user.id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Portfolio analysis failed"
        )


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for the intelligence service."""
    return {
        "status": "healthy",
        "service": "cross-system-intelligence",
        "version": "2.0"
    }


# Helper functions

def _convert_to_response_schema(response: IntelligenceResponse) -> IntelligenceResponseSchema:
    """Convert service response to API schema."""
    
    return IntelligenceResponseSchema(
        query_type=response.query_type.value,
        analysis_timestamp=response.analysis_timestamp,
        portfolio_analysis=_convert_portfolio_to_schema(response.portfolio_analysis) if response.portfolio_analysis else None,
        geographic_clusters=[_convert_geographic_cluster_to_schema(cluster) for cluster in response.geographic_clusters] if response.geographic_clusters else [],
        industry_clusters=[_convert_industry_cluster_to_schema(cluster) for cluster in response.industry_clusters] if response.industry_clusters else [],
        contract_impacts=[_convert_contract_impact_to_schema(impact) for impact in response.contract_impacts] if response.contract_impacts else [],
        trend_analyses=[_convert_trend_analysis_to_schema(trend) for trend in response.trend_analyses] if response.trend_analyses else [],
        key_insights=response.key_insights or [],
        strategic_recommendations=response.strategic_recommendations or [],
        risk_alerts=response.risk_alerts or [],
        opportunities=response.opportunities or [],
        analysis_time_ms=response.analysis_time_ms,
        confidence_score=response.confidence_score,
        data_quality_score=response.data_quality_score
    )


def _convert_portfolio_to_schema(portfolio) -> PortfolioAnalysisSchema:
    """Convert portfolio analysis to schema."""
    
    return PortfolioAnalysisSchema(
        total_suppliers=portfolio.total_suppliers,
        total_contract_value=portfolio.total_contract_value,
        risk_distribution=portfolio.risk_distribution,
        geographic_distribution=portfolio.geographic_distribution,
        industry_distribution=portfolio.industry_distribution,
        portfolio_risk_score=portfolio.portfolio_risk_score,
        diversification_index=portfolio.diversification_index,
        concentration_risk=portfolio.concentration_risk,
        risk_trend_30d=portfolio.risk_trend_30d,
        risk_trend_90d=portfolio.risk_trend_90d,
        risk_trend_365d=portfolio.risk_trend_365d,
        top_risk_contributors=portfolio.top_risk_contributors,
        optimization_opportunities=portfolio.optimization_opportunities,
        strategic_recommendations=portfolio.strategic_recommendations,
        suppliers_at_risk=portfolio.suppliers_at_risk,
        contracts_requiring_attention=portfolio.contracts_requiring_attention,
        emerging_risk_areas=portfolio.emerging_risk_areas
    )


def _convert_geographic_cluster_to_schema(cluster) -> GeographicClusterSchema:
    """Convert geographic cluster to schema."""
    
    return GeographicClusterSchema(
        region=cluster.region,
        country_codes=cluster.country_codes,
        supplier_count=cluster.supplier_count,
        average_risk_score=cluster.average_risk_score,
        total_contract_value=cluster.total_contract_value,
        risk_factors=cluster.risk_factors,
        trend_direction=cluster.trend_direction,
        risk_level=cluster.risk_level,
        political_risk=cluster.political_risk,
        economic_risk=cluster.economic_risk,
        regulatory_risk=cluster.regulatory_risk,
        natural_disaster_risk=cluster.natural_disaster_risk,
        mitigation_strategies=cluster.mitigation_strategies,
        monitoring_priorities=cluster.monitoring_priorities
    )


def _convert_industry_cluster_to_schema(cluster) -> IndustryClusterSchema:
    """Convert industry cluster to schema."""
    
    return IndustryClusterSchema(
        industry=cluster.industry,
        sub_industries=cluster.sub_industries,
        supplier_count=cluster.supplier_count,
        average_risk_score=cluster.average_risk_score,
        total_contract_value=cluster.total_contract_value,
        market_volatility=cluster.market_volatility,
        regulatory_burden=cluster.regulatory_burden,
        supply_chain_risk=cluster.supply_chain_risk,
        technology_disruption_risk=cluster.technology_disruption_risk,
        regulatory_change_risk=cluster.regulatory_change_risk,
        market_demand_risk=cluster.market_demand_risk,
        growth_outlook=cluster.growth_outlook,
        emerging_risks=cluster.emerging_risks,
        opportunities=cluster.opportunities
    )


def _convert_contract_impact_to_schema(impact) -> ContractImpactSchema:
    """Convert contract impact to schema."""
    
    return ContractImpactSchema(
        supplier_id=impact.supplier_id,
        supplier_name=impact.supplier_name,
        base_risk_score=impact.base_risk_score,
        contract_adjusted_risk_score=impact.contract_adjusted_risk_score,
        impact_magnitude=impact.impact_magnitude,
        high_risk_clauses=impact.high_risk_clauses,
        contract_concentration=impact.contract_concentration,
        value_exposure=impact.value_exposure,
        expiry_risk=impact.expiry_risk,
        risk_drivers=impact.risk_drivers,
        mitigation_suggestions=impact.mitigation_suggestions,
        monitoring_requirements=impact.monitoring_requirements
    )


def _convert_trend_analysis_to_schema(trend) -> TrendAnalysisSchema:
    """Convert trend analysis to schema."""
    
    return TrendAnalysisSchema(
        supplier_id=trend.supplier_id,
        supplier_name=trend.supplier_name,
        risk_score_trend=[(t.isoformat(), score) for t, score in trend.risk_score_trend],
        contract_value_trend=[(t.isoformat(), value) for t, value in trend.contract_value_trend],
        performance_trend=[(t.isoformat(), perf) for t, perf in trend.performance_trend],
        risk_direction=trend.risk_direction,
        velocity=trend.velocity,
        acceleration=trend.acceleration,
        predicted_risk_30d=trend.predicted_risk_30d,
        predicted_risk_90d=trend.predicted_risk_90d,
        confidence_interval=trend.confidence_interval,
        trend_alerts=trend.trend_alerts,
        recommended_actions=trend.recommended_actions
    )
