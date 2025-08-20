"""
Supplier-related execution handlers for AI Assistant.
"""

import structlog
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.user import User
from app.models.supplier import Supplier, SupplierRiskAssessment
from app.core.supplier_risk import SupplierRiskService
from app.core.supplier_insights import SupplierInsightsService
from .base_handler import BaseHandler

logger = structlog.get_logger(__name__)


async def execute_search_suppliers(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute supplier search based on extracted parameters"""
    try:
        BaseHandler.log_execution_start(
            "search_suppliers",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        # Extract search parameters
        supplier_name = parameters.get("supplier_name")
        industry = parameters.get("industry")
        country = parameters.get("country")
        risk_level = parameters.get("risk_level")
        min_risk_score = parameters.get("min_risk_score")
        max_risk_score = parameters.get("max_risk_score")
        watchlisted_only = parameters.get("watchlisted_only", False)
        
        # Build query
        query = db.query(Supplier).filter(
            Supplier.organization_id == current_user.organization_id,
            Supplier.is_active == True
        )
        
        # Apply filters
        if supplier_name:
            query = query.filter(Supplier.name.ilike(f"%{supplier_name}%"))
        
        if industry:
            query = query.filter(Supplier.industry.ilike(f"%{industry}%"))
        
        if country:
            query = query.filter(Supplier.country.ilike(f"%{country}%"))
        
        if risk_level:
            query = query.filter(Supplier.risk_level == risk_level.upper())
        
        if min_risk_score is not None:
            query = query.filter(Supplier.risk_score >= min_risk_score)
        
        if max_risk_score is not None:
            query = query.filter(Supplier.risk_score <= max_risk_score)
        
        if watchlisted_only:
            query = query.filter(Supplier.is_watchlisted == True)
        
        # Execute query with ordering
        suppliers = query.order_by(desc(Supplier.risk_score)).limit(50).all()
        
        # Format results
        results = []
        for supplier in suppliers:
            results.append({
                "id": supplier.id,
                "name": supplier.name,
                "industry": supplier.industry,
                "country": supplier.country,
                "risk_score": supplier.risk_score,
                "risk_level": supplier.risk_level,
                "is_watchlisted": supplier.is_watchlisted,
                "company_size": supplier.company_size,
                "contact_email": supplier.contact_email,
                "last_risk_assessment": supplier.last_risk_assessment.isoformat() if supplier.last_risk_assessment else None
            })
        
        # Generate search insights
        if results:
            avg_risk = sum(s["risk_score"] for s in results) / len(results)
            high_risk_count = len([s for s in results if s["risk_score"] >= 70])
            industries = list(set(s["industry"] for s in results if s["industry"]))
            countries = list(set(s["country"] for s in results if s["country"]))
        else:
            avg_risk = 0
            high_risk_count = 0
            industries = []
            countries = []
        
        return BaseHandler.create_success_response(
            message=f"Found {len(results)} suppliers matching criteria",
            parameters=parameters,
            data={
                "suppliers": results,
                "total_found": len(results),
                "search_insights": {
                    "average_risk_score": round(avg_risk, 2),
                    "high_risk_count": high_risk_count,
                    "industries_represented": industries,
                    "countries_represented": countries
                },
                "search_criteria": BaseHandler.sanitize_parameters(parameters)
            }
        )
        
    except Exception as e:
        BaseHandler.log_execution_error("search_suppliers", e, parameters)
        return BaseHandler.create_error_response(
            message="Supplier search failed",
            parameters=parameters,
            error=str(e),
            additional_fields={"suppliers": [], "total_found": 0}
        )


async def execute_analyze_supplier_risk(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute supplier risk analysis based on extracted parameters"""
    try:
        BaseHandler.log_execution_start(
            "analyze_supplier_risk",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        # Extract risk analysis parameters
        supplier_ids = parameters.get("supplier_ids")
        supplier_name = parameters.get("supplier_name")
        country = parameters.get("country")
        industry = parameters.get("industry")
        risk_level = parameters.get("risk_level")
        min_risk_score = parameters.get("min_risk_score")
        max_risk_score = parameters.get("max_risk_score")
        watchlisted_only = parameters.get("watchlisted_only", False)
        risk_types = parameters.get("risk_types", ["financial", "operational", "compliance"])
        time_period = parameters.get("time_period")
        include_news = parameters.get("include_news", False)
        include_financial = parameters.get("include_financial", False)
        benchmark_industry = parameters.get("benchmark_industry", False)
        
        # Get suppliers to analyze with proper filtering
        suppliers_query = db.query(Supplier).filter(
            Supplier.organization_id == current_user.organization_id,
            Supplier.is_active == True
        )
        
        # Apply filters
        if supplier_ids:
            suppliers_query = suppliers_query.filter(Supplier.id.in_(supplier_ids))
        
        if supplier_name:
            suppliers_query = suppliers_query.filter(Supplier.name.ilike(f"%{supplier_name}%"))
        
        if country:
            suppliers_query = suppliers_query.filter(Supplier.country.ilike(f"%{country}%"))
        
        if industry:
            suppliers_query = suppliers_query.filter(Supplier.industry.ilike(f"%{industry}%"))
        
        if risk_level:
            suppliers_query = suppliers_query.filter(Supplier.risk_level == risk_level.upper())
        
        if min_risk_score is not None:
            suppliers_query = suppliers_query.filter(Supplier.risk_score >= min_risk_score)
        
        if max_risk_score is not None:
            suppliers_query = suppliers_query.filter(Supplier.risk_score <= max_risk_score)
        
        if watchlisted_only:
            suppliers_query = suppliers_query.filter(Supplier.is_watchlisted == True)
        
        # Order by risk score descending to prioritize higher risk suppliers
        suppliers = suppliers_query.order_by(desc(Supplier.risk_score)).all()
        
        if not suppliers:
            return BaseHandler.create_error_response(
                message="No suppliers found for risk analysis",
                parameters=parameters,
                error="No suppliers match the specified criteria"
            )
        
        # Perform risk analysis for each supplier
        risk_analyses = []
        for supplier in suppliers:
            # Get basic risk analysis
            risk_analysis = {
                "supplier_id": supplier.id,
                "supplier_name": supplier.name,
                "current_risk_score": supplier.risk_score,
                "current_risk_level": supplier.risk_level,
                "risk_factors": supplier.risk_factors or {},
                "last_assessment": supplier.last_risk_assessment.isoformat() if supplier.last_risk_assessment else None
            }
            
            # Add historical risk data if available
            recent_assessments = db.query(SupplierRiskAssessment).filter(
                SupplierRiskAssessment.supplier_id == supplier.id
            ).order_by(desc(SupplierRiskAssessment.created_at)).limit(5).all()
            
            if recent_assessments:
                risk_history = []
                for assessment in recent_assessments:
                    risk_history.append({
                        "date": assessment.created_at.isoformat(),
                        "risk_score": assessment.risk_score,
                        "risk_level": assessment.risk_level,
                        "assessment_method": assessment.assessment_method
                    })
                risk_analysis["risk_history"] = risk_history
                
                # Calculate trend
                if len(recent_assessments) >= 2:
                    latest_score = recent_assessments[0].risk_score
                    previous_score = recent_assessments[-1].risk_score
                    trend = "improving" if latest_score < previous_score else "deteriorating" if latest_score > previous_score else "stable"
                    risk_analysis["risk_trend"] = trend
            
            # Add enhanced analysis if requested
            if include_news or include_financial:
                try:
                    enhanced_risk = await SupplierRiskService.calculate_enhanced_risk_score(
                        supplier_name=supplier.name,
                        industry=supplier.industry,
                        country=supplier.country
                    )
                    risk_analysis["enhanced_analysis"] = enhanced_risk
                except Exception as enhanced_error:
                    logger.warning(f"Enhanced analysis failed for {supplier.name}: {enhanced_error}")
            
            # Add industry benchmark if requested
            if benchmark_industry and supplier.industry:
                industry_suppliers = db.query(Supplier).filter(
                    Supplier.organization_id == current_user.organization_id,
                    Supplier.industry == supplier.industry,
                    Supplier.is_active == True
                ).all()
                
                if len(industry_suppliers) > 1:
                    industry_scores = [s.risk_score for s in industry_suppliers]
                    industry_avg = sum(industry_scores) / len(industry_scores)
                    
                    risk_analysis["industry_benchmark"] = {
                        "industry": supplier.industry,
                        "industry_average": round(industry_avg, 2),
                        "peer_count": len(industry_suppliers),
                        "relative_performance": "above_average" if supplier.risk_score < industry_avg else "below_average"
                    }
            
            risk_analyses.append(risk_analysis)
        
        # Generate summary
        total_suppliers = len(risk_analyses)
        avg_risk = sum(analysis["current_risk_score"] for analysis in risk_analyses) / total_suppliers
        high_risk_count = len([a for a in risk_analyses if a["current_risk_score"] >= 70])
        
        return BaseHandler.create_success_response(
            message=f"Analyzed risk for {total_suppliers} suppliers",
            parameters=parameters,
            data={
                "risk_analyses": risk_analyses,
                "analysis_summary": {
                    "total_suppliers": total_suppliers,
                    "average_risk_score": round(avg_risk, 2),
                    "high_risk_count": high_risk_count,
                    "analysis_types": risk_types,
                    "enhanced_analysis_included": include_news or include_financial,
                    "industry_benchmarks_included": benchmark_industry
                }
            }
        )
        
    except Exception as e:
        BaseHandler.log_execution_error("analyze_supplier_risk", e, parameters)
        return BaseHandler.create_error_response(
            message="Supplier risk analysis failed",
            parameters=parameters,
            error=str(e),
            additional_fields={"risk_analyses": [], "analysis_summary": {}}
        )


async def execute_compare_suppliers(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute supplier comparison based on extracted parameters"""
    try:
        BaseHandler.log_execution_start(
            "compare_suppliers",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        supplier_ids = parameters.get("supplier_ids", [])
        comparison_criteria = parameters.get("comparison_criteria", ["risk_score", "industry", "country"])
        include_history = parameters.get("include_history", False)
        
        if len(supplier_ids) < 2:
            return BaseHandler.create_error_response(
                message="At least 2 suppliers are required for comparison",
                parameters=parameters,
                error="Insufficient suppliers for comparison"
            )
        
        # Get suppliers for comparison
        suppliers = db.query(Supplier).filter(
            Supplier.id.in_(supplier_ids),
            Supplier.organization_id == current_user.organization_id
        ).all()
        
        if len(suppliers) < 2:
            return BaseHandler.create_error_response(
                message="Could not find enough suppliers for comparison",
                parameters=parameters,
                error="Some specified suppliers were not found"
            )
        
        # Perform comparison
        comparisons = []
        for supplier in suppliers:
            comparison_data = {
                "supplier_id": supplier.id,
                "supplier_name": supplier.name,
                "risk_score": supplier.risk_score,
                "risk_level": supplier.risk_level,
                "industry": supplier.industry,
                "country": supplier.country,
                "company_size": supplier.company_size,
                "is_watchlisted": supplier.is_watchlisted,
                "contact_email": supplier.contact_email
            }
            
            # Add risk factors if available
            if supplier.risk_factors:
                comparison_data["risk_factors"] = supplier.risk_factors
            
            # Add historical data if requested
            if include_history:
                recent_assessments = db.query(SupplierRiskAssessment).filter(
                    SupplierRiskAssessment.supplier_id == supplier.id
                ).order_by(desc(SupplierRiskAssessment.created_at)).limit(10).all()
                
                if recent_assessments:
                    history = [{
                        "date": assessment.created_at.isoformat(),
                        "risk_score": assessment.risk_score,
                        "risk_level": assessment.risk_level
                    } for assessment in recent_assessments]
                    comparison_data["risk_history"] = history
            
            comparisons.append(comparison_data)
        
        # Generate comparison insights
        risk_scores = [c["risk_score"] for c in comparisons]
        insights = {
            "lowest_risk": {
                "supplier": min(comparisons, key=lambda x: x["risk_score"])["supplier_name"],
                "score": min(risk_scores)
            },
            "highest_risk": {
                "supplier": max(comparisons, key=lambda x: x["risk_score"])["supplier_name"],
                "score": max(risk_scores)
            },
            "average_risk": round(sum(risk_scores) / len(risk_scores), 2),
            "risk_spread": max(risk_scores) - min(risk_scores),
            "industries": list(set(c["industry"] for c in comparisons if c["industry"])),
            "countries": list(set(c["country"] for c in comparisons if c["country"]))
        }
        
        return BaseHandler.create_success_response(
            message=f"Compared {len(comparisons)} suppliers across {len(comparison_criteria)} criteria",
            parameters=parameters,
            data={
                "comparisons": comparisons,
                "comparison_insights": insights,
                "comparison_criteria": comparison_criteria,
                "suppliers_compared": len(comparisons)
            }
        )
        
    except Exception as e:
        BaseHandler.log_execution_error("compare_suppliers", e, parameters)
        return BaseHandler.create_error_response(
            message="Supplier comparison failed",
            parameters=parameters,
            error=str(e),
            additional_fields={"comparisons": [], "suppliers_compared": 0}
        )


async def execute_supplier_insights(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute supplier insights generation based on extracted parameters"""
    try:
        BaseHandler.log_execution_start(
            "supplier_insights",
            parameters,
            current_user.id,
            current_user.organization_id
        )
        
        # Extract insights parameters
        insight_type = parameters.get("insight_type", "portfolio_overview")
        time_period = parameters.get("time_period", 90)
        industry_focus = parameters.get("industry_focus")
        risk_threshold = parameters.get("risk_threshold")
        include_predictions = parameters.get("include_predictions", True)
        include_recommendations = parameters.get("include_recommendations", True)
        supplier_ids = parameters.get("supplier_ids")
        
        # Initialize insights service
        insights_service = SupplierInsightsService()
        
        # Generate comprehensive insights
        insights_data = await insights_service.generate_comprehensive_insights(
            db=db,
            organization_id=current_user.organization_id,
            supplier_ids=supplier_ids,
            time_period_days=time_period,
            include_predictions=include_predictions,
            include_benchmarks=True
        )
        
        # Format response for AI assistant
        response_data = {
            "insights": {
                "portfolio_health_score": insights_data["analysis_summary"]["portfolio_health_score"],
                "key_metrics": insights_data["key_metrics"],
                "trend_analysis": insights_data["trend_analysis"][:5],  # Top 5 trends
                "portfolio_insights": insights_data["portfolio_insights"][:3],  # Top 3 insights
                "emerging_risks": insights_data["emerging_risks"][:3],  # Top 3 risks
                "performance_patterns": insights_data["performance_patterns"]
            },
            "recommendations": insights_data["strategic_recommendations"][:10],  # Top 10 recommendations
            "data_quality": {
                "suppliers_analyzed": insights_data["analysis_summary"]["total_suppliers_analyzed"],
                "trends_detected": len(insights_data["trend_analysis"]),
                "insights_generated": len(insights_data["portfolio_insights"]),
                "predictions_made": len(insights_data.get("risk_predictions", [])),
                "benchmarks_available": len(insights_data.get("benchmark_analysis", []))
            }
        }
        
        # Add predictions if requested
        if include_predictions and "risk_predictions" in insights_data:
            response_data["insights"]["risk_predictions"] = insights_data["risk_predictions"][:5]  # Top 5 predictions
        
        # Add benchmark analysis
        if "benchmark_analysis" in insights_data:
            response_data["insights"]["benchmark_analysis"] = insights_data["benchmark_analysis"][:5]  # Top 5 benchmarks
        
        return BaseHandler.create_success_response(
            message=f"Generated {insight_type} insights for {insights_data['analysis_summary']['total_suppliers_analyzed']} suppliers",
            parameters=parameters,
            data=response_data
        )
        
    except Exception as e:
        BaseHandler.log_execution_error("supplier_insights", e, parameters)
        return BaseHandler.create_error_response(
            message="Failed to generate supplier insights",
            parameters=parameters,
            error=str(e),
            additional_fields={
                "insights": {},
                "recommendations": ["Unable to generate insights - please check system logs"],
                "data_quality": {}
            }
        )
