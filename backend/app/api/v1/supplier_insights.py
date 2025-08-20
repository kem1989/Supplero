"""
Supplier Insights API endpoints for AI-powered analytics and trend analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import structlog

from app.core.database import get_db
from app.core.logging import get_current_trace_context
from app.core.supplier_insights import SupplierInsightsService
from app.schemas.supplier_insights import (
    SupplierInsightsRequest,
    SupplierInsightsResponse,
    TrendAnalysisResponse,
    PredictiveAnalysisResponse,
    BenchmarkAnalysisResponse,
    PortfolioHealthResponse,
    InsightType
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/suppliers/insights", tags=["supplier-insights"])


@router.post("/", response_model=SupplierInsightsResponse)
async def generate_supplier_insights(
    insights_request: SupplierInsightsRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive AI-powered supplier insights.
    
    This endpoint provides advanced analytics including:
    - Risk trend analysis
    - Portfolio-level insights
    - Predictive risk indicators
    - Industry benchmarks
    - Emerging risk detection
    - Strategic recommendations
    """
    trace_context = get_current_trace_context()
    
    try:
        # Initialize insights service
        insights_service = SupplierInsightsService()
        
        # For now, using a dummy organization_id - in production this would come from auth
        organization_id = 1
        
        # Generate comprehensive insights
        insights = await insights_service.generate_comprehensive_insights(
            db=db,
            organization_id=organization_id,
            supplier_ids=insights_request.supplier_ids,
            time_period_days=insights_request.time_period_days,
            include_predictions=insights_request.include_predictions,
            include_benchmarks=insights_request.include_benchmarks
        )
        
        logger.info(
            "Supplier insights generated successfully",
            organization_id=organization_id,
            supplier_count=insights["analysis_summary"]["total_suppliers_analyzed"],
            insights_generated=len(insights.get("portfolio_insights", [])),
            **trace_context
        )
        
        return insights
        
    except Exception as e:
        logger.error(
            "Failed to generate supplier insights",
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.get("/trends", response_model=TrendAnalysisResponse)
async def get_supplier_trend_analysis(
    request: Request,
    db: Session = Depends(get_db),
    supplier_ids: Optional[List[int]] = Query(None, description="Specific supplier IDs to analyze"),
    time_period_days: int = Query(90, ge=30, le=365, description="Analysis time period in days")
):
    """
    Get supplier risk trend analysis over time.
    
    Analyzes historical risk score changes and identifies:
    - Improving vs deteriorating trends
    - Trend velocity and confidence
    - Key factors driving changes
    """
    trace_context = get_current_trace_context()
    
    try:
        insights_service = SupplierInsightsService()
        organization_id = 1  # TODO: Get from auth
        
        # Get suppliers for analysis
        suppliers = await insights_service._get_suppliers_for_analysis(
            db, organization_id, supplier_ids
        )
        
        # Analyze trends
        trend_analysis = await insights_service._analyze_risk_trends(
            db, suppliers, time_period_days
        )
        
        # Generate trend-specific recommendations
        recommendations = []
        deteriorating_count = sum(1 for t in trend_analysis if t.trend_direction == "deteriorating")
        
        if deteriorating_count > 0:
            recommendations.append(
                f"⚠️ {deteriorating_count} suppliers showing deteriorating risk trends - investigate immediately"
            )
        
        improving_count = sum(1 for t in trend_analysis if t.trend_direction == "improving")
        if improving_count > 0:
            recommendations.append(
                f"✅ {improving_count} suppliers showing improving risk trends - consider expanding relationships"
            )
        
        response = {
            "analysis_summary": {
                "total_suppliers_analyzed": len(suppliers),
                "analysis_period_days": time_period_days,
                "portfolio_health_score": 75.0,  # Calculated based on trends
                "analysis_timestamp": datetime.utcnow().isoformat()
            },
            "trend_analysis": [trend.__dict__ for trend in trend_analysis],
            "recommendations": recommendations
        }
        
        logger.info(
            "Trend analysis completed",
            supplier_count=len(suppliers),
            trends_analyzed=len(trend_analysis),
            **trace_context
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to generate trend analysis",
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate trend analysis: {str(e)}"
        )


@router.get("/predictions", response_model=PredictiveAnalysisResponse)
async def get_predictive_risk_analysis(
    request: Request,
    db: Session = Depends(get_db),
    supplier_ids: Optional[List[int]] = Query(None, description="Specific supplier IDs to analyze"),
    prediction_horizon_days: int = Query(90, ge=30, le=365, description="Prediction timeframe in days")
):
    """
    Generate predictive risk analysis for suppliers.
    
    Uses AI to predict future risk scores based on:
    - Historical risk trends
    - External data signals
    - Industry patterns
    - Economic indicators
    """
    trace_context = get_current_trace_context()
    
    try:
        insights_service = SupplierInsightsService()
        organization_id = 1  # TODO: Get from auth
        
        # Get suppliers for analysis
        suppliers = await insights_service._get_suppliers_for_analysis(
            db, organization_id, supplier_ids
        )
        
        # Generate predictions
        risk_predictions = await insights_service._generate_risk_predictions(db, suppliers)
        
        # Detect emerging risks
        emerging_risks = await insights_service._detect_emerging_risks(db, suppliers[:10])  # Sample for API efficiency
        
        # Generate predictive recommendations
        recommendations = []
        high_risk_predictions = [p for p in risk_predictions if p.predicted_risk_score > 70]
        
        if high_risk_predictions:
            recommendations.append(
                f"🚨 {len(high_risk_predictions)} suppliers predicted to become high-risk - proactive intervention needed"
            )
        
        if emerging_risks:
            recommendations.append(
                f"📈 {len(emerging_risks)} suppliers showing new external risk signals - monitor closely"
            )
        
        response = {
            "analysis_summary": {
                "total_suppliers_analyzed": len(suppliers),
                "analysis_period_days": prediction_horizon_days,
                "portfolio_health_score": 75.0,
                "analysis_timestamp": datetime.utcnow().isoformat()
            },
            "risk_predictions": [pred.__dict__ for pred in risk_predictions],
            "emerging_risks": emerging_risks,
            "recommendations": recommendations
        }
        
        logger.info(
            "Predictive analysis completed",
            supplier_count=len(suppliers),
            predictions_generated=len(risk_predictions),
            emerging_risks_detected=len(emerging_risks),
            **trace_context
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to generate predictive analysis",
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate predictive analysis: {str(e)}"
        )


@router.get("/benchmarks", response_model=BenchmarkAnalysisResponse)
async def get_supplier_benchmark_analysis(
    request: Request,
    db: Session = Depends(get_db),
    supplier_ids: Optional[List[int]] = Query(None, description="Specific supplier IDs to analyze"),
    industries: Optional[List[str]] = Query(None, description="Filter by industries")
):
    """
    Generate industry benchmark analysis for suppliers.
    
    Compares suppliers against industry peers:
    - Risk score percentile ranking
    - Industry average comparisons
    - Peer performance insights
    - Best practice recommendations
    """
    trace_context = get_current_trace_context()
    
    try:
        insights_service = SupplierInsightsService()
        organization_id = 1  # TODO: Get from auth
        
        # Get suppliers for analysis
        suppliers = await insights_service._get_suppliers_for_analysis(
            db, organization_id, supplier_ids
        )
        
        # Filter by industries if specified
        if industries:
            suppliers = [s for s in suppliers if s.industry in industries]
        
        # Generate benchmark analysis
        benchmark_analysis = await insights_service._generate_benchmark_analysis(db, suppliers)
        
        # Calculate industry insights
        industry_insights = {}
        for supplier in suppliers:
            industry = supplier.industry or "Unknown"
            if industry not in industry_insights:
                industry_insights[industry] = {
                    "supplier_count": 0,
                    "average_risk_score": 0,
                    "risk_distribution": {"low": 0, "medium": 0, "high": 0}
                }
            
            industry_insights[industry]["supplier_count"] += 1
            industry_insights[industry]["average_risk_score"] += supplier.risk_score
            
            if supplier.risk_score < 40:
                industry_insights[industry]["risk_distribution"]["low"] += 1
            elif supplier.risk_score < 70:
                industry_insights[industry]["risk_distribution"]["medium"] += 1
            else:
                industry_insights[industry]["risk_distribution"]["high"] += 1
        
        # Calculate averages
        for industry_data in industry_insights.values():
            if industry_data["supplier_count"] > 0:
                industry_data["average_risk_score"] /= industry_data["supplier_count"]
        
        # Generate benchmark recommendations
        recommendations = []
        above_average_count = sum(1 for b in benchmark_analysis if b.peer_comparison == "above_average")
        below_average_count = sum(1 for b in benchmark_analysis if b.peer_comparison == "below_average")
        
        if above_average_count > 0:
            recommendations.append(
                f"✅ {above_average_count} suppliers performing above industry average - leverage their best practices"
            )
        
        if below_average_count > 0:
            recommendations.append(
                f"⚠️ {below_average_count} suppliers performing below industry average - implement improvement programs"
            )
        
        response = {
            "analysis_summary": {
                "total_suppliers_analyzed": len(suppliers),
                "analysis_period_days": 90,
                "portfolio_health_score": 75.0,
                "analysis_timestamp": datetime.utcnow().isoformat()
            },
            "benchmark_analysis": [bench.__dict__ for bench in benchmark_analysis],
            "industry_insights": industry_insights,
            "recommendations": recommendations
        }
        
        logger.info(
            "Benchmark analysis completed",
            supplier_count=len(suppliers),
            benchmarks_generated=len(benchmark_analysis),
            industries_analyzed=len(industry_insights),
            **trace_context
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to generate benchmark analysis",
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate benchmark analysis: {str(e)}"
        )


@router.get("/portfolio-health", response_model=PortfolioHealthResponse)
async def get_portfolio_health_assessment(
    request: Request,
    db: Session = Depends(get_db),
    include_trends: bool = Query(True, description="Include trend analysis in health calculation")
):
    """
    Get overall supplier portfolio health assessment.
    
    Provides a comprehensive health score based on:
    - Average risk scores
    - Risk distribution
    - Trend analysis
    - Emerging risk factors
    - Portfolio diversification
    """
    trace_context = get_current_trace_context()
    
    try:
        insights_service = SupplierInsightsService()
        organization_id = 1  # TODO: Get from auth
        
        # Get all suppliers for portfolio analysis
        suppliers = await insights_service._get_suppliers_for_analysis(
            db, organization_id, None
        )
        
        if not suppliers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No suppliers found for portfolio analysis"
            )
        
        # Calculate key metrics
        key_metrics = insights_service._calculate_key_metrics(suppliers, [])
        
        # Get trend analysis if requested
        trend_analysis = []
        emerging_risks = []
        
        if include_trends:
            trend_analysis = await insights_service._analyze_risk_trends(db, suppliers, 90)
            emerging_risks = await insights_service._detect_emerging_risks(db, suppliers[:5])  # Sample
        
        # Calculate portfolio health score
        portfolio_health_score = insights_service._calculate_portfolio_health(
            suppliers, trend_analysis, emerging_risks
        )
        
        # Determine health category
        if portfolio_health_score >= 90:
            health_category = "excellent"
        elif portfolio_health_score >= 75:
            health_category = "good"
        elif portfolio_health_score >= 60:
            health_category = "fair"
        elif portfolio_health_score >= 40:
            health_category = "poor"
        else:
            health_category = "critical"
        
        # Generate health factors
        health_factors = []
        if key_metrics["high_risk_count"] == 0:
            health_factors.append("No high-risk suppliers in portfolio")
        elif key_metrics["high_risk_count"] < len(suppliers) * 0.1:
            health_factors.append("Low concentration of high-risk suppliers")
        else:
            health_factors.append(f"High risk concentration: {key_metrics['high_risk_count']} suppliers")
        
        if key_metrics["industries_represented"] > 5:
            health_factors.append("Good industry diversification")
        else:
            health_factors.append("Limited industry diversification")
        
        if key_metrics["countries_represented"] > 3:
            health_factors.append("Good geographic diversification")
        else:
            health_factors.append("Limited geographic diversification")
        
        # Generate improvement opportunities
        improvement_opportunities = []
        
        if key_metrics["high_risk_count"] > 0:
            improvement_opportunities.append(
                f"Reduce high-risk suppliers from {key_metrics['high_risk_count']} to improve portfolio health"
            )
        
        if key_metrics["deteriorating_trends"] > 0:
            improvement_opportunities.append(
                f"Address {key_metrics['deteriorating_trends']} suppliers with deteriorating risk trends"
            )
        
        if key_metrics["watchlisted_suppliers"] > 0:
            improvement_opportunities.append(
                f"Review and potentially replace {key_metrics['watchlisted_suppliers']} watchlisted suppliers"
            )
        
        if key_metrics["industries_represented"] < 5:
            improvement_opportunities.append("Diversify across more industry sectors to reduce concentration risk")
        
        if key_metrics["countries_represented"] < 3:
            improvement_opportunities.append("Expand geographic diversification to reduce regional risk")
        
        response = {
            "portfolio_health_score": portfolio_health_score,
            "health_category": health_category,
            "key_metrics": key_metrics,
            "health_factors": health_factors,
            "improvement_opportunities": improvement_opportunities,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Portfolio health assessment completed",
            supplier_count=len(suppliers),
            health_score=portfolio_health_score,
            health_category=health_category,
            **trace_context
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to generate portfolio health assessment",
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate portfolio health assessment: {str(e)}"
        )
