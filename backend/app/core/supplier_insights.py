"""
Supplier Insights Service for advanced AI-powered analysis and trend detection.
This service generates actionable insights from supplier data, external sources, and historical trends.
"""

import structlog
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.supplier import Supplier, SupplierRiskAssessment
from app.models.document import Document
from app.core.external_data_aggregation import ExternalDataAggregationService, RiskSignal
from app.core.supplier_risk import SupplierRiskService

logger = structlog.get_logger(__name__)


@dataclass
class TrendAnalysis:
    """Represents trend analysis for a specific metric"""
    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: str  # "improving", "deteriorating", "stable"
    confidence_score: float
    time_period_days: int
    key_factors: List[str]


@dataclass
class RiskPrediction:
    """Represents a predictive risk indicator"""
    supplier_id: int
    supplier_name: str
    current_risk_score: float
    predicted_risk_score: float
    prediction_timeframe_days: int
    confidence_score: float
    risk_factors: List[str]
    early_warning_signals: List[str]
    recommended_actions: List[str]


@dataclass
class PortfolioInsight:
    """Represents portfolio-level insights"""
    insight_type: str
    title: str
    description: str
    impact_level: str  # "low", "medium", "high", "critical"
    affected_suppliers: List[int]
    financial_impact_estimate: Optional[float]
    recommended_actions: List[str]
    urgency_score: float
    supporting_data: Dict[str, Any]


@dataclass
class BenchmarkAnalysis:
    """Industry benchmark comparison"""
    supplier_id: int
    supplier_name: str
    industry: str
    risk_score: float
    industry_average: float
    industry_median: float
    percentile_rank: float
    peer_comparison: str  # "above_average", "below_average", "average"
    benchmark_insights: List[str]


class SupplierInsightsService:
    """Advanced AI-powered supplier insights and trend analysis service."""
    
    def __init__(self):
        self.external_data_service = ExternalDataAggregationService()
    
    async def generate_comprehensive_insights(
        self,
        db: Session,
        organization_id: int,
        supplier_ids: Optional[List[int]] = None,
        time_period_days: int = 90,
        include_predictions: bool = True,
        include_benchmarks: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive AI insights for supplier portfolio.
        
        Args:
            db: Database session
            organization_id: Organization ID for scoping
            supplier_ids: Specific suppliers to analyze (None for all)
            time_period_days: Analysis time period
            include_predictions: Whether to include predictive analytics
            include_benchmarks: Whether to include industry benchmarks
        
        Returns:
            Comprehensive insights dictionary with trends, predictions, and recommendations
        """
        logger.info(
            "Generating comprehensive supplier insights",
            organization_id=organization_id,
            supplier_ids=supplier_ids,
            time_period_days=time_period_days
        )
        
        try:
            # Get suppliers for analysis
            suppliers = await self._get_suppliers_for_analysis(
                db, organization_id, supplier_ids
            )
            
            if not suppliers:
                return {
                    "message": "No suppliers found for analysis",
                    "insights": {},
                    "recommendations": [],
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
            
            # Generate different types of insights concurrently
            tasks = [
                self._analyze_risk_trends(db, suppliers, time_period_days),
                self._generate_portfolio_insights(db, suppliers, organization_id),
                self._detect_emerging_risks(db, suppliers),
                self._analyze_performance_patterns(db, suppliers, time_period_days)
            ]
            
            if include_predictions:
                tasks.append(self._generate_risk_predictions(db, suppliers))
            
            if include_benchmarks:
                tasks.append(self._generate_benchmark_analysis(db, suppliers))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            trend_analysis = results[0] if not isinstance(results[0], Exception) else []
            portfolio_insights = results[1] if not isinstance(results[1], Exception) else []
            emerging_risks = results[2] if not isinstance(results[2], Exception) else []
            performance_patterns = results[3] if not isinstance(results[3], Exception) else []
            
            risk_predictions = []
            benchmark_analysis = []
            
            if include_predictions and len(results) > 4:
                risk_predictions = results[4] if not isinstance(results[4], Exception) else []
            
            if include_benchmarks and len(results) > (5 if include_predictions else 4):
                benchmark_analysis = results[-1] if not isinstance(results[-1], Exception) else []
            
            # Generate strategic recommendations
            recommendations = await self._generate_strategic_recommendations(
                trend_analysis, portfolio_insights, emerging_risks, risk_predictions
            )
            
            # Calculate overall portfolio health score
            portfolio_health = self._calculate_portfolio_health(
                suppliers, trend_analysis, emerging_risks
            )
            
            insights = {
                "analysis_summary": {
                    "total_suppliers_analyzed": len(suppliers),
                    "analysis_period_days": time_period_days,
                    "portfolio_health_score": portfolio_health,
                    "analysis_timestamp": datetime.utcnow().isoformat()
                },
                "trend_analysis": [trend.__dict__ for trend in trend_analysis],
                "portfolio_insights": [insight.__dict__ for insight in portfolio_insights],
                "emerging_risks": emerging_risks,
                "performance_patterns": performance_patterns,
                "strategic_recommendations": recommendations,
                "key_metrics": self._calculate_key_metrics(suppliers, trend_analysis)
            }
            
            if include_predictions:
                insights["risk_predictions"] = [pred.__dict__ for pred in risk_predictions]
            
            if include_benchmarks:
                insights["benchmark_analysis"] = [bench.__dict__ for bench in benchmark_analysis]
            
            logger.info(
                "Comprehensive insights generated successfully",
                organization_id=organization_id,
                insights_generated=len(portfolio_insights),
                trends_analyzed=len(trend_analysis),
                predictions_made=len(risk_predictions) if include_predictions else 0
            )
            
            return insights
            
        except Exception as e:
            logger.error(
                "Failed to generate comprehensive insights",
                organization_id=organization_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _get_suppliers_for_analysis(
        self,
        db: Session,
        organization_id: int,
        supplier_ids: Optional[List[int]]
    ) -> List[Supplier]:
        """Get suppliers for analysis with proper filtering."""
        
        query = db.query(Supplier).filter(
            Supplier.organization_id == organization_id,
            Supplier.is_active == True
        )
        
        if supplier_ids:
            query = query.filter(Supplier.id.in_(supplier_ids))
        
        return query.all()
    
    async def _analyze_risk_trends(
        self,
        db: Session,
        suppliers: List[Supplier],
        time_period_days: int
    ) -> List[TrendAnalysis]:
        """Analyze risk trends for suppliers over time."""
        
        trends = []
        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
        
        for supplier in suppliers:
            # Get historical risk assessments
            assessments = db.query(SupplierRiskAssessment).filter(
                SupplierRiskAssessment.supplier_id == supplier.id,
                SupplierRiskAssessment.created_at >= cutoff_date
            ).order_by(SupplierRiskAssessment.created_at).all()
            
            if len(assessments) < 2:
                continue  # Need at least 2 points for trend analysis
            
            # Calculate trend metrics
            risk_scores = [a.risk_score for a in assessments]
            current_score = risk_scores[-1]
            previous_score = risk_scores[0]
            
            change_percentage = ((current_score - previous_score) / previous_score * 100) if previous_score > 0 else 0
            
            # Determine trend direction
            if abs(change_percentage) < 5:
                trend_direction = "stable"
            elif change_percentage > 0:
                trend_direction = "deteriorating"
            else:
                trend_direction = "improving"
            
            # Calculate confidence based on data points and consistency
            confidence_score = min(0.9, len(assessments) / 10)  # More data points = higher confidence
            
            # Identify key factors
            key_factors = self._identify_trend_factors(assessments, supplier)
            
            trend = TrendAnalysis(
                metric_name=f"{supplier.name}_risk_score",
                current_value=current_score,
                previous_value=previous_score,
                change_percentage=change_percentage,
                trend_direction=trend_direction,
                confidence_score=confidence_score,
                time_period_days=time_period_days,
                key_factors=key_factors
            )
            
            trends.append(trend)
        
        return trends
    
    def _identify_trend_factors(
        self,
        assessments: List[SupplierRiskAssessment],
        supplier: Supplier
    ) -> List[str]:
        """Identify key factors driving risk trends."""
        
        factors = []
        
        # Analyze changes in risk factors over time
        if len(assessments) >= 2:
            latest = assessments[-1]
            previous = assessments[0]
            
            latest_factors = latest.risk_factors or {}
            previous_factors = previous.risk_factors or {}
            
            # Check for significant changes in risk factor categories
            for category in ["financial", "operational", "compliance", "reputation"]:
                latest_score = latest_factors.get(f"{category}_risk", 0)
                previous_score = previous_factors.get(f"{category}_risk", 0)
                
                if abs(latest_score - previous_score) > 10:
                    if latest_score > previous_score:
                        factors.append(f"Increased {category} risk")
                    else:
                        factors.append(f"Improved {category} risk")
        
        # Add industry-specific factors
        if supplier.industry:
            factors.append(f"Industry: {supplier.industry}")
        
        # Add geographic factors
        if supplier.country:
            factors.append(f"Geographic: {supplier.country}")
        
        return factors[:5]  # Limit to top 5 factors
    
    async def _generate_portfolio_insights(
        self,
        db: Session,
        suppliers: List[Supplier],
        organization_id: int
    ) -> List[PortfolioInsight]:
        """Generate portfolio-level insights."""
        
        insights = []
        
        # Risk concentration analysis
        high_risk_suppliers = [s for s in suppliers if s.risk_score >= 70]
        if len(high_risk_suppliers) > len(suppliers) * 0.3:
            insight = PortfolioInsight(
                insight_type="risk_concentration",
                title="High Risk Concentration Detected",
                description=f"{len(high_risk_suppliers)} out of {len(suppliers)} suppliers ({len(high_risk_suppliers)/len(suppliers)*100:.1f}%) are high-risk, indicating potential portfolio vulnerability.",
                impact_level="high",
                affected_suppliers=[s.id for s in high_risk_suppliers],
                financial_impact_estimate=None,
                recommended_actions=[
                    "Diversify supplier base to reduce concentration risk",
                    "Implement enhanced monitoring for high-risk suppliers",
                    "Consider alternative suppliers for critical services"
                ],
                urgency_score=0.8,
                supporting_data={
                    "high_risk_count": len(high_risk_suppliers),
                    "total_suppliers": len(suppliers),
                    "concentration_percentage": len(high_risk_suppliers)/len(suppliers)*100
                }
            )
            insights.append(insight)
        
        # Geographic concentration
        country_distribution = {}
        for supplier in suppliers:
            country = supplier.country or "Unknown"
            country_distribution[country] = country_distribution.get(country, 0) + 1
        
        max_country_count = max(country_distribution.values()) if country_distribution else 0
        if max_country_count > len(suppliers) * 0.5:
            dominant_country = max(country_distribution, key=country_distribution.get)
            insight = PortfolioInsight(
                insight_type="geographic_concentration",
                title="Geographic Concentration Risk",
                description=f"{max_country_count} suppliers ({max_country_count/len(suppliers)*100:.1f}%) are concentrated in {dominant_country}, creating geographic risk exposure.",
                impact_level="medium",
                affected_suppliers=[s.id for s in suppliers if s.country == dominant_country],
                financial_impact_estimate=None,
                recommended_actions=[
                    f"Diversify suppliers across different geographic regions",
                    f"Assess {dominant_country}-specific risks (political, economic, regulatory)",
                    "Develop contingency plans for regional disruptions"
                ],
                urgency_score=0.6,
                supporting_data={
                    "dominant_country": dominant_country,
                    "concentration_count": max_country_count,
                    "concentration_percentage": max_country_count/len(suppliers)*100,
                    "geographic_distribution": country_distribution
                }
            )
            insights.append(insight)
        
        # Industry concentration
        industry_distribution = {}
        for supplier in suppliers:
            industry = supplier.industry or "Unknown"
            industry_distribution[industry] = industry_distribution.get(industry, 0) + 1
        
        max_industry_count = max(industry_distribution.values()) if industry_distribution else 0
        if max_industry_count > len(suppliers) * 0.4:
            dominant_industry = max(industry_distribution, key=industry_distribution.get)
            insight = PortfolioInsight(
                insight_type="industry_concentration",
                title="Industry Concentration Risk",
                description=f"{max_industry_count} suppliers ({max_industry_count/len(suppliers)*100:.1f}%) are in {dominant_industry}, creating sector-specific risk exposure.",
                impact_level="medium",
                affected_suppliers=[s.id for s in suppliers if s.industry == dominant_industry],
                financial_impact_estimate=None,
                recommended_actions=[
                    "Diversify across different industry sectors",
                    f"Monitor {dominant_industry} industry trends and risks",
                    "Consider suppliers from complementary industries"
                ],
                urgency_score=0.5,
                supporting_data={
                    "dominant_industry": dominant_industry,
                    "concentration_count": max_industry_count,
                    "concentration_percentage": max_industry_count/len(suppliers)*100,
                    "industry_distribution": industry_distribution
                }
            )
            insights.append(insight)
        
        return insights
    
    async def _detect_emerging_risks(
        self,
        db: Session,
        suppliers: List[Supplier]
    ) -> List[Dict[str, Any]]:
        """Detect emerging risks using external data and AI analysis."""
        
        emerging_risks = []
        
        # Sample suppliers for external data analysis (to manage API costs)
        sample_suppliers = suppliers[:10]  # Analyze top 10 suppliers
        
        for supplier in sample_suppliers:
            try:
                # Get recent external data
                external_data = await self.external_data_service.aggregate_supplier_risk_data(
                    supplier_name=supplier.name,
                    industry=supplier.industry,
                    country=supplier.country
                )
                
                # Analyze risk signals for emerging patterns
                risk_signals = external_data.get("risk_signals", [])
                
                # Look for new or escalating risk signals
                high_severity_signals = [
                    signal for signal in risk_signals 
                    if hasattr(signal, 'severity') and signal.severity in ["high", "critical"]
                ]
                
                if high_severity_signals:
                    emerging_risk = {
                        "supplier_id": supplier.id,
                        "supplier_name": supplier.name,
                        "risk_type": "external_signals",
                        "severity": "high",
                        "description": f"Detected {len(high_severity_signals)} high-severity external risk signals",
                        "signals": [
                            {
                                "type": signal.signal_type if hasattr(signal, 'signal_type') else "unknown",
                                "description": signal.description if hasattr(signal, 'description') else "No description",
                                "confidence": signal.confidence_score if hasattr(signal, 'confidence_score') else 0.5
                            }
                            for signal in high_severity_signals[:3]  # Top 3 signals
                        ],
                        "recommended_actions": [
                            "Investigate external risk signals immediately",
                            "Consider enhanced monitoring for this supplier",
                            "Review contract terms and risk mitigation strategies"
                        ]
                    }
                    emerging_risks.append(emerging_risk)
                
            except Exception as e:
                logger.warning(
                    "Failed to analyze external data for supplier",
                    supplier_name=supplier.name,
                    error=str(e)
                )
                continue
        
        return emerging_risks
    
    async def _analyze_performance_patterns(
        self,
        db: Session,
        suppliers: List[Supplier],
        time_period_days: int
    ) -> Dict[str, Any]:
        """Analyze supplier performance patterns."""
        
        patterns = {
            "risk_score_distribution": {},
            "industry_performance": {},
            "geographic_performance": {},
            "size_correlation": {},
            "improvement_trends": [],
            "deterioration_trends": []
        }
        
        # Risk score distribution
        risk_ranges = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
        for supplier in suppliers:
            score = supplier.risk_score
            if score <= 25:
                risk_ranges["0-25"] += 1
            elif score <= 50:
                risk_ranges["26-50"] += 1
            elif score <= 75:
                risk_ranges["51-75"] += 1
            else:
                risk_ranges["76-100"] += 1
        
        patterns["risk_score_distribution"] = risk_ranges
        
        # Industry performance
        industry_scores = {}
        for supplier in suppliers:
            industry = supplier.industry or "Unknown"
            if industry not in industry_scores:
                industry_scores[industry] = []
            industry_scores[industry].append(supplier.risk_score)
        
        for industry, scores in industry_scores.items():
            patterns["industry_performance"][industry] = {
                "average_risk_score": sum(scores) / len(scores),
                "supplier_count": len(scores),
                "risk_level": "high" if sum(scores) / len(scores) > 60 else "medium" if sum(scores) / len(scores) > 30 else "low"
            }
        
        # Geographic performance
        country_scores = {}
        for supplier in suppliers:
            country = supplier.country or "Unknown"
            if country not in country_scores:
                country_scores[country] = []
            country_scores[country].append(supplier.risk_score)
        
        for country, scores in country_scores.items():
            patterns["geographic_performance"][country] = {
                "average_risk_score": sum(scores) / len(scores),
                "supplier_count": len(scores),
                "risk_level": "high" if sum(scores) / len(scores) > 60 else "medium" if sum(scores) / len(scores) > 30 else "low"
            }
        
        return patterns
    
    async def _generate_risk_predictions(
        self,
        db: Session,
        suppliers: List[Supplier]
    ) -> List[RiskPrediction]:
        """Generate predictive risk indicators using AI analysis."""
        
        predictions = []
        
        for supplier in suppliers:
            try:
                # Get historical risk data
                assessments = db.query(SupplierRiskAssessment).filter(
                    SupplierRiskAssessment.supplier_id == supplier.id
                ).order_by(SupplierRiskAssessment.created_at.desc()).limit(5).all()
                
                if len(assessments) < 3:
                    continue  # Need sufficient history for prediction
                
                # Simple trend-based prediction (can be enhanced with ML models)
                recent_scores = [a.risk_score for a in assessments[:3]]
                current_score = recent_scores[0]
                
                # Calculate trend velocity
                if len(recent_scores) >= 2:
                    velocity = (recent_scores[0] - recent_scores[-1]) / len(recent_scores)
                else:
                    velocity = 0
                
                # Predict score in 90 days
                predicted_score = max(0, min(100, current_score + (velocity * 3)))  # 3 months
                
                # Determine confidence based on trend consistency
                if len(recent_scores) >= 3:
                    trend_consistency = self._calculate_trend_consistency(recent_scores)
                    confidence = min(0.9, trend_consistency)
                else:
                    confidence = 0.5
                
                # Identify risk factors and early warning signals
                risk_factors = []
                early_warnings = []
                
                if velocity > 5:  # Risk increasing
                    risk_factors.append("Upward risk trend detected")
                    early_warnings.append("Risk score has been increasing consistently")
                
                if supplier.risk_score > 70:
                    early_warnings.append("Already in high-risk category")
                
                if supplier.industry in ["financial_services", "defense", "aviation"]:
                    risk_factors.append(f"High-risk industry: {supplier.industry}")
                
                # Generate recommendations
                recommendations = []
                if predicted_score > current_score + 10:
                    recommendations.append("Implement enhanced monitoring and risk mitigation")
                    recommendations.append("Review and update contract terms")
                    recommendations.append("Consider alternative suppliers")
                elif predicted_score < current_score - 10:
                    recommendations.append("Supplier showing positive risk trend")
                    recommendations.append("Consider expanding relationship if performance continues")
                else:
                    recommendations.append("Continue standard monitoring procedures")
                
                prediction = RiskPrediction(
                    supplier_id=supplier.id,
                    supplier_name=supplier.name,
                    current_risk_score=current_score,
                    predicted_risk_score=predicted_score,
                    prediction_timeframe_days=90,
                    confidence_score=confidence,
                    risk_factors=risk_factors,
                    early_warning_signals=early_warnings,
                    recommended_actions=recommendations
                )
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.warning(
                    "Failed to generate risk prediction for supplier",
                    supplier_id=supplier.id,
                    error=str(e)
                )
                continue
        
        return predictions
    
    def _calculate_trend_consistency(self, scores: List[float]) -> float:
        """Calculate how consistent a trend is (0.0 to 1.0)."""
        if len(scores) < 3:
            return 0.5
        
        # Calculate direction consistency
        directions = []
        for i in range(1, len(scores)):
            if scores[i] > scores[i-1]:
                directions.append(1)
            elif scores[i] < scores[i-1]:
                directions.append(-1)
            else:
                directions.append(0)
        
        if not directions:
            return 0.5
        
        # Count consistent directions
        positive_count = sum(1 for d in directions if d > 0)
        negative_count = sum(1 for d in directions if d < 0)
        
        consistency = max(positive_count, negative_count) / len(directions)
        return consistency
    
    async def _generate_benchmark_analysis(
        self,
        db: Session,
        suppliers: List[Supplier]
    ) -> List[BenchmarkAnalysis]:
        """Generate industry benchmark analysis."""
        
        benchmarks = []
        
        # Group suppliers by industry
        industry_groups = {}
        for supplier in suppliers:
            industry = supplier.industry or "Unknown"
            if industry not in industry_groups:
                industry_groups[industry] = []
            industry_groups[industry].append(supplier)
        
        # Calculate benchmarks for each industry
        for industry, industry_suppliers in industry_groups.items():
            if len(industry_suppliers) < 2:
                continue  # Need at least 2 suppliers for meaningful benchmarks
            
            risk_scores = [s.risk_score for s in industry_suppliers]
            industry_average = sum(risk_scores) / len(risk_scores)
            industry_median = sorted(risk_scores)[len(risk_scores) // 2]
            
            for supplier in industry_suppliers:
                # Calculate percentile rank
                better_count = sum(1 for score in risk_scores if score < supplier.risk_score)
                percentile_rank = (better_count / len(risk_scores)) * 100
                
                # Determine peer comparison
                if supplier.risk_score < industry_average - 10:
                    peer_comparison = "above_average"  # Lower risk is better
                elif supplier.risk_score > industry_average + 10:
                    peer_comparison = "below_average"
                else:
                    peer_comparison = "average"
                
                # Generate benchmark insights
                insights = []
                if peer_comparison == "above_average":
                    insights.append(f"Performing better than {percentile_rank:.0f}% of industry peers")
                    insights.append("Risk score is significantly below industry average")
                elif peer_comparison == "below_average":
                    insights.append(f"Risk score higher than {100-percentile_rank:.0f}% of industry peers")
                    insights.append("Consider implementing best practices from better-performing peers")
                else:
                    insights.append("Risk score is close to industry average")
                    insights.append("Monitor for opportunities to improve relative performance")
                
                benchmark = BenchmarkAnalysis(
                    supplier_id=supplier.id,
                    supplier_name=supplier.name,
                    industry=industry,
                    risk_score=supplier.risk_score,
                    industry_average=industry_average,
                    industry_median=industry_median,
                    percentile_rank=percentile_rank,
                    peer_comparison=peer_comparison,
                    benchmark_insights=insights
                )
                
                benchmarks.append(benchmark)
        
        return benchmarks
    
    async def _generate_strategic_recommendations(
        self,
        trend_analysis: List[TrendAnalysis],
        portfolio_insights: List[PortfolioInsight],
        emerging_risks: List[Dict[str, Any]],
        risk_predictions: List[RiskPrediction]
    ) -> List[str]:
        """Generate strategic recommendations based on all insights."""
        
        recommendations = []
        
        # Analyze trends for recommendations
        deteriorating_trends = [t for t in trend_analysis if t.trend_direction == "deteriorating"]
        if len(deteriorating_trends) > len(trend_analysis) * 0.3:
            recommendations.append(
                f"⚠️ URGENT: {len(deteriorating_trends)} suppliers showing deteriorating risk trends - "
                "implement enhanced monitoring and risk mitigation immediately"
            )
        
        # High-impact portfolio insights
        critical_insights = [i for i in portfolio_insights if i.impact_level == "critical"]
        if critical_insights:
            recommendations.append(
                "🔴 CRITICAL: Address portfolio concentration risks to prevent systemic failures"
            )
        
        # Emerging risks
        if emerging_risks:
            recommendations.append(
                f"🚨 EMERGING RISKS: {len(emerging_risks)} suppliers have new external risk signals - "
                "investigate and update risk assessments"
            )
        
        # Predictive recommendations
        high_risk_predictions = [p for p in risk_predictions if p.predicted_risk_score > 70]
        if high_risk_predictions:
            recommendations.append(
                f"📈 PREDICTIVE ALERT: {len(high_risk_predictions)} suppliers predicted to become high-risk - "
                "proactive intervention recommended"
            )
        
        # General strategic recommendations
        recommendations.extend([
            "📊 Implement continuous monitoring dashboard for real-time risk tracking",
            "🔄 Establish quarterly supplier risk review process",
            "🤝 Develop stronger relationships with low-risk suppliers for business continuity",
            "📋 Create supplier diversification strategy to reduce concentration risks",
            "🎯 Set up automated alerts for significant risk score changes"
        ])
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _calculate_portfolio_health(
        self,
        suppliers: List[Supplier],
        trend_analysis: List[TrendAnalysis],
        emerging_risks: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall portfolio health score (0-100)."""
        
        if not suppliers:
            return 0.0
        
        # Base score from average risk scores (inverted - lower risk = higher health)
        avg_risk_score = sum(s.risk_score for s in suppliers) / len(suppliers)
        base_health = max(0, 100 - avg_risk_score)
        
        # Adjust for trends
        deteriorating_count = sum(1 for t in trend_analysis if t.trend_direction == "deteriorating")
        trend_penalty = (deteriorating_count / len(suppliers)) * 20 if suppliers else 0
        
        # Adjust for emerging risks
        emerging_risk_penalty = min(20, len(emerging_risks) * 5)
        
        # Calculate final health score
        health_score = max(0, min(100, base_health - trend_penalty - emerging_risk_penalty))
        
        return round(health_score, 1)
    
    def _calculate_key_metrics(
        self,
        suppliers: List[Supplier],
        trend_analysis: List[TrendAnalysis]
    ) -> Dict[str, Any]:
        """Calculate key portfolio metrics."""
        
        if not suppliers:
            return {}
        
        return {
            "total_suppliers": len(suppliers),
            "average_risk_score": round(sum(s.risk_score for s in suppliers) / len(suppliers), 1),
            "high_risk_count": len([s for s in suppliers if s.risk_score >= 70]),
            "medium_risk_count": len([s for s in suppliers if 40 <= s.risk_score < 70]),
            "low_risk_count": len([s for s in suppliers if s.risk_score < 40]),
            "improving_trends": len([t for t in trend_analysis if t.trend_direction == "improving"]),
            "deteriorating_trends": len([t for t in trend_analysis if t.trend_direction == "deteriorating"]),
            "stable_trends": len([t for t in trend_analysis if t.trend_direction == "stable"]),
            "watchlisted_suppliers": len([s for s in suppliers if s.is_watchlisted]),
            "industries_represented": len(set(s.industry for s in suppliers if s.industry)),
            "countries_represented": len(set(s.country for s in suppliers if s.country))
        }
