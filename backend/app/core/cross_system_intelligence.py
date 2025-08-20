"""
Cross-System Intelligence Service - Phase 2 Implementation

This service provides advanced intelligence capabilities that bridge suppliers and contracts,
enabling sophisticated cross-system queries with AI-powered insights, trend analysis,
geographic clustering, and portfolio-level risk assessment.

Enhanced Features:
- Advanced cross-system query processing
- Geographic and industry risk clustering
- Supplier portfolio analysis
- Contract risk impact on supplier assessment
- Predictive risk indicators
- AI-powered insights generation
"""

import structlog
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text, distinct, case
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from openai import OpenAI

from app.models.supplier import Supplier, SupplierRiskAssessment
from app.models.document import Document, ContractClause
from app.models.organization import Organization
from app.core.elasticsearch_service import ElasticsearchService
from app.core.cross_system_search import (
    CrossSystemSearchService, CrossSystemSearchRequest, CrossSystemSearchResponse,
    SupplierContractInfo, ContractSupplierInfo, CrossSystemQueryType
)
from app.core.config import settings

logger = structlog.get_logger(__name__)


class IntelligenceQueryType(str, Enum):
    """Enhanced intelligence query types"""
    PORTFOLIO_RISK_ANALYSIS = "portfolio_risk_analysis"
    GEOGRAPHIC_RISK_CLUSTERING = "geographic_risk_clustering"
    INDUSTRY_RISK_CLUSTERING = "industry_risk_clustering"
    CONTRACT_IMPACT_ASSESSMENT = "contract_impact_assessment"
    SUPPLIER_TREND_ANALYSIS = "supplier_trend_analysis"
    PREDICTIVE_RISK_MODELING = "predictive_risk_modeling"
    CROSS_SYSTEM_CORRELATION = "cross_system_correlation"
    INTELLIGENT_RECOMMENDATIONS = "intelligent_recommendations"


@dataclass
class GeographicRiskCluster:
    """Geographic risk cluster information"""
    region: str
    country_codes: List[str]
    supplier_count: int
    average_risk_score: float
    total_contract_value: float
    risk_factors: List[str]
    trend_direction: str  # "increasing", "decreasing", "stable"
    risk_level: str  # "low", "medium", "high", "critical"
    
    # Specific risk indicators
    political_risk: float
    economic_risk: float
    regulatory_risk: float
    natural_disaster_risk: float
    
    # Recommendations
    mitigation_strategies: List[str]
    monitoring_priorities: List[str]


@dataclass
class IndustryRiskCluster:
    """Industry risk cluster information"""
    industry: str
    sub_industries: List[str]
    supplier_count: int
    average_risk_score: float
    total_contract_value: float
    market_volatility: float
    regulatory_burden: str
    
    # Risk factors specific to industry
    supply_chain_risk: float
    technology_disruption_risk: float
    regulatory_change_risk: float
    market_demand_risk: float
    
    # Trends and predictions
    growth_outlook: str
    emerging_risks: List[str]
    opportunities: List[str]


@dataclass
class PortfolioAnalysis:
    """Comprehensive supplier portfolio analysis"""
    total_suppliers: int
    total_contract_value: float
    risk_distribution: Dict[str, int]
    geographic_distribution: Dict[str, int]
    industry_distribution: Dict[str, int]
    
    # Portfolio-level metrics
    portfolio_risk_score: float
    diversification_index: float
    concentration_risk: float
    
    # Risk trends
    risk_trend_30d: str
    risk_trend_90d: str
    risk_trend_365d: str
    
    # Key insights
    top_risk_contributors: List[Dict[str, Any]]
    optimization_opportunities: List[str]
    strategic_recommendations: List[str]
    
    # Predictive indicators
    suppliers_at_risk: List[int]
    contracts_requiring_attention: List[int]
    emerging_risk_areas: List[str]


@dataclass
class ContractImpactAssessment:
    """Assessment of contract risk impact on supplier evaluation"""
    supplier_id: int
    supplier_name: str
    base_risk_score: float
    contract_adjusted_risk_score: float
    impact_magnitude: float
    
    # Contract-specific factors
    high_risk_clauses: List[Dict[str, Any]]
    contract_concentration: float
    value_exposure: float
    expiry_risk: float
    
    # Risk explanation
    risk_drivers: List[str]
    mitigation_suggestions: List[str]
    monitoring_requirements: List[str]


@dataclass
class TrendAnalysisResult:
    """Supplier trend analysis result"""
    supplier_id: int
    supplier_name: str
    
    # Historical trends
    risk_score_trend: List[Tuple[datetime, float]]
    contract_value_trend: List[Tuple[datetime, float]]
    performance_trend: List[Tuple[datetime, float]]
    
    # Trend indicators
    risk_direction: str  # "improving", "deteriorating", "stable"
    velocity: float  # Rate of change
    acceleration: float  # Change in rate of change
    
    # Predictions
    predicted_risk_30d: float
    predicted_risk_90d: float
    confidence_interval: Tuple[float, float]
    
    # Alerts
    trend_alerts: List[str]
    recommended_actions: List[str]


@dataclass
class IntelligenceRequest:
    """Enhanced intelligence request"""
    query_type: IntelligenceQueryType
    query_text: Optional[str] = None
    
    # Filtering options
    supplier_ids: Optional[List[int]] = None
    industries: Optional[List[str]] = None
    countries: Optional[List[str]] = None
    risk_levels: Optional[List[str]] = None
    
    # Time range for analysis
    analysis_start_date: Optional[datetime] = None
    analysis_end_date: Optional[datetime] = None
    
    # Analysis parameters
    include_predictions: bool = True
    include_recommendations: bool = True
    confidence_threshold: float = 0.7
    max_results: int = 50


@dataclass
class IntelligenceResponse:
    """Enhanced intelligence response"""
    query_type: IntelligenceQueryType
    analysis_timestamp: datetime
    
    # Core analysis results
    portfolio_analysis: Optional[PortfolioAnalysis] = None
    geographic_clusters: List[GeographicRiskCluster] = None
    industry_clusters: List[IndustryRiskCluster] = None
    contract_impacts: List[ContractImpactAssessment] = None
    trend_analyses: List[TrendAnalysisResult] = None
    
    # AI-generated insights
    key_insights: List[str] = None
    strategic_recommendations: List[str] = None
    risk_alerts: List[str] = None
    opportunities: List[str] = None
    
    # Performance metrics
    analysis_time_ms: float = 0.0
    confidence_score: float = 0.0
    data_quality_score: float = 0.0


class CrossSystemIntelligenceService:
    """Enhanced cross-system intelligence service with advanced AI capabilities"""
    
    def __init__(self):
        self.elasticsearch_service = ElasticsearchService()
        self.cross_system_service = CrossSystemSearchService()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Geographic risk mappings (in production, this would come from external APIs)
        self.geographic_risk_data = self._initialize_geographic_risk_data()
        
        # Industry risk mappings
        self.industry_risk_data = self._initialize_industry_risk_data()
    
    async def execute_intelligence_query(
        self,
        request: IntelligenceRequest,
        db: Session,
        organization_id: int
    ) -> IntelligenceResponse:
        """
        Execute an enhanced intelligence query with AI-powered analysis.
        
        Args:
            request: Intelligence request with query type and parameters
            db: Database session
            organization_id: Organization ID for filtering
            
        Returns:
            IntelligenceResponse with comprehensive analysis results
        """
        start_time = datetime.utcnow()
        
        logger.info(
            "Starting enhanced intelligence query",
            query_type=request.query_type,
            organization_id=organization_id,
            query_text=request.query_text
        )
        
        try:
            # Route to appropriate analysis method
            if request.query_type == IntelligenceQueryType.PORTFOLIO_RISK_ANALYSIS:
                response = await self._analyze_portfolio_risk(request, db, organization_id)
            elif request.query_type == IntelligenceQueryType.GEOGRAPHIC_RISK_CLUSTERING:
                response = await self._analyze_geographic_risk_clusters(request, db, organization_id)
            elif request.query_type == IntelligenceQueryType.INDUSTRY_RISK_CLUSTERING:
                response = await self._analyze_industry_risk_clusters(request, db, organization_id)
            elif request.query_type == IntelligenceQueryType.CONTRACT_IMPACT_ASSESSMENT:
                response = await self._assess_contract_impact(request, db, organization_id)
            elif request.query_type == IntelligenceQueryType.SUPPLIER_TREND_ANALYSIS:
                response = await self._analyze_supplier_trends(request, db, organization_id)
            elif request.query_type == IntelligenceQueryType.PREDICTIVE_RISK_MODELING:
                response = await self._predict_risk_scenarios(request, db, organization_id)
            elif request.query_type == IntelligenceQueryType.CROSS_SYSTEM_CORRELATION:
                response = await self._analyze_cross_system_correlations(request, db, organization_id)
            elif request.query_type == IntelligenceQueryType.INTELLIGENT_RECOMMENDATIONS:
                response = await self._generate_intelligent_recommendations(request, db, organization_id)
            else:
                raise ValueError(f"Unsupported intelligence query type: {request.query_type}")
            
            # Calculate analysis time
            analysis_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            response.analysis_time_ms = analysis_time
            response.analysis_timestamp = datetime.utcnow()
            
            # Generate AI-powered insights if requested
            if request.include_recommendations:
                await self._enhance_with_ai_insights(response, request, db, organization_id)
            
            logger.info(
                "Enhanced intelligence query completed",
                query_type=request.query_type,
                analysis_time_ms=analysis_time,
                confidence_score=response.confidence_score
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Enhanced intelligence query failed",
                query_type=request.query_type,
                organization_id=organization_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _analyze_portfolio_risk(
        self,
        request: IntelligenceRequest,
        db: Session,
        organization_id: int
    ) -> IntelligenceResponse:
        """Analyze comprehensive supplier portfolio risk."""
        
        # Get all suppliers for the organization
        suppliers_query = db.query(Supplier).filter(
            Supplier.organization_id == organization_id,
            Supplier.is_active == True
        )
        
        # Apply filters if specified
        if request.supplier_ids:
            suppliers_query = suppliers_query.filter(Supplier.id.in_(request.supplier_ids))
        if request.industries:
            suppliers_query = suppliers_query.filter(Supplier.industry.in_(request.industries))
        if request.countries:
            suppliers_query = suppliers_query.filter(Supplier.country.in_(request.countries))
        if request.risk_levels:
            suppliers_query = suppliers_query.filter(Supplier.risk_level.in_(request.risk_levels))
        
        suppliers = suppliers_query.all()
        
        if not suppliers:
            return IntelligenceResponse(
                query_type=request.query_type,
                analysis_timestamp=datetime.utcnow(),
                key_insights=["No suppliers found matching the criteria"],
                confidence_score=0.0
            )
        
        # Calculate portfolio-level metrics
        total_suppliers = len(suppliers)
        
        # Get contract values for suppliers
        total_contract_value = 0.0
        supplier_contract_values = {}
        
        for supplier in suppliers:
            contract_value = await self._get_supplier_total_contract_value(db, supplier.name)
            supplier_contract_values[supplier.id] = contract_value or 0.0
            total_contract_value += contract_value or 0.0
        
        # Risk distribution
        risk_distribution = {}
        for supplier in suppliers:
            risk_level = supplier.risk_level or "UNKNOWN"
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        # Geographic distribution
        geographic_distribution = {}
        for supplier in suppliers:
            country = supplier.country or "Unknown"
            geographic_distribution[country] = geographic_distribution.get(country, 0) + 1
        
        # Industry distribution
        industry_distribution = {}
        for supplier in suppliers:
            industry = supplier.industry or "Unknown"
            industry_distribution[industry] = industry_distribution.get(industry, 0) + 1
        
        # Calculate portfolio risk score (weighted by contract value)
        portfolio_risk_score = 0.0
        total_weight = 0.0
        
        for supplier in suppliers:
            weight = supplier_contract_values[supplier.id] or 1.0  # Minimum weight of 1
            # Normalize risk score from 0-100 to 0-10 scale
            normalized_risk_score = supplier.risk_score / 10.0
            portfolio_risk_score += normalized_risk_score * weight
            total_weight += weight
        
        if total_weight > 0:
            portfolio_risk_score /= total_weight
        
        # Calculate diversification index (higher = more diversified)
        diversification_index = self._calculate_diversification_index(
            geographic_distribution, industry_distribution
        )
        
        # Calculate concentration risk
        concentration_risk = self._calculate_concentration_risk(supplier_contract_values)
        
        # Identify top risk contributors
        top_risk_contributors = []
        for supplier in sorted(suppliers, key=lambda s: s.risk_score, reverse=True)[:5]:
            contract_value = supplier_contract_values[supplier.id]
            contribution = supplier.risk_score * (contract_value / total_contract_value if total_contract_value > 0 else 1.0)
            
            top_risk_contributors.append({
                "supplier_id": supplier.id,
                "supplier_name": supplier.name,
                "risk_score": supplier.risk_score,
                "contract_value": contract_value,
                "risk_contribution": contribution,
                "risk_level": supplier.risk_level
            })
        
        # Generate trend analysis (simplified for now)
        risk_trends = await self._analyze_portfolio_risk_trends(db, suppliers, organization_id)
        
        # Identify optimization opportunities
        optimization_opportunities = self._identify_optimization_opportunities(
            suppliers, supplier_contract_values, risk_distribution, geographic_distribution
        )
        
        # Generate strategic recommendations
        strategic_recommendations = self._generate_portfolio_recommendations(
            portfolio_risk_score, diversification_index, concentration_risk, risk_distribution
        )
        
        # Identify at-risk suppliers and contracts
        suppliers_at_risk = [s.id for s in suppliers if s.risk_score >= 7.0 or s.risk_level in ['HIGH', 'CRITICAL']]
        contracts_requiring_attention = await self._identify_high_risk_contracts(db, suppliers_at_risk)
        
        # Create portfolio analysis
        portfolio_analysis = PortfolioAnalysis(
            total_suppliers=total_suppliers,
            total_contract_value=total_contract_value,
            risk_distribution=risk_distribution,
            geographic_distribution=geographic_distribution,
            industry_distribution=industry_distribution,
            portfolio_risk_score=portfolio_risk_score,
            diversification_index=diversification_index,
            concentration_risk=concentration_risk,
            risk_trend_30d=risk_trends.get("30d", "stable"),
            risk_trend_90d=risk_trends.get("90d", "stable"),
            risk_trend_365d=risk_trends.get("365d", "stable"),
            top_risk_contributors=top_risk_contributors,
            optimization_opportunities=optimization_opportunities,
            strategic_recommendations=strategic_recommendations,
            suppliers_at_risk=suppliers_at_risk,
            contracts_requiring_attention=contracts_requiring_attention,
            emerging_risk_areas=[]  # Will be populated by AI analysis
        )
        
        # Calculate confidence score based on data completeness
        confidence_score = self._calculate_portfolio_confidence_score(suppliers, supplier_contract_values)
        
        return IntelligenceResponse(
            query_type=request.query_type,
            analysis_timestamp=datetime.utcnow(),
            portfolio_analysis=portfolio_analysis,
            confidence_score=confidence_score
        )
    
    async def _analyze_geographic_risk_clusters(
        self,
        request: IntelligenceRequest,
        db: Session,
        organization_id: int
    ) -> IntelligenceResponse:
        """Analyze geographic risk clustering."""
        
        # Get suppliers grouped by country
        suppliers = db.query(Supplier).filter(
            Supplier.organization_id == organization_id,
            Supplier.is_active == True,
            Supplier.country.isnot(None)
        ).all()
        
        # Group suppliers by geographic regions
        geographic_clusters = {}
        
        for supplier in suppliers:
            country = supplier.country
            region = self._map_country_to_region(country)
            
            if region not in geographic_clusters:
                geographic_clusters[region] = {
                    "suppliers": [],
                    "countries": set(),
                    "total_contract_value": 0.0
                }
            
            geographic_clusters[region]["suppliers"].append(supplier)
            geographic_clusters[region]["countries"].add(country)
            
            # Get contract value for this supplier
            contract_value = await self._get_supplier_total_contract_value(db, supplier.name)
            geographic_clusters[region]["total_contract_value"] += contract_value or 0.0
        
        # Create cluster analysis
        cluster_results = []
        
        for region, data in geographic_clusters.items():
            suppliers_in_region = data["suppliers"]
            
            if not suppliers_in_region:
                continue
            
            # Calculate cluster metrics
            # Normalize risk scores from 0-100 to 0-10 scale
            normalized_risk_scores = [s.risk_score / 10.0 for s in suppliers_in_region]
            average_risk_score = sum(normalized_risk_scores) / len(normalized_risk_scores)
            
            # Get regional risk factors from external data
            regional_risk_data = self.geographic_risk_data.get(region, {})
            
            # Determine overall risk level
            risk_level = self._determine_cluster_risk_level(average_risk_score, regional_risk_data)
            
            # Generate risk factors
            risk_factors = self._identify_geographic_risk_factors(region, suppliers_in_region, regional_risk_data)
            
            # Analyze trends
            trend_direction = await self._analyze_geographic_trend(db, region, suppliers_in_region)
            
            # Generate mitigation strategies
            mitigation_strategies = self._generate_geographic_mitigation_strategies(region, risk_factors)
            
            cluster = GeographicRiskCluster(
                region=region,
                country_codes=list(data["countries"]),
                supplier_count=len(suppliers_in_region),
                average_risk_score=average_risk_score,
                total_contract_value=data["total_contract_value"],
                risk_factors=risk_factors,
                trend_direction=trend_direction,
                risk_level=risk_level,
                political_risk=regional_risk_data.get("political_risk", 3.0),
                economic_risk=regional_risk_data.get("economic_risk", 3.0),
                regulatory_risk=regional_risk_data.get("regulatory_risk", 3.0),
                natural_disaster_risk=regional_risk_data.get("natural_disaster_risk", 2.0),
                mitigation_strategies=mitigation_strategies,
                monitoring_priorities=self._generate_monitoring_priorities(region, risk_factors)
            )
            
            cluster_results.append(cluster)
        
        # Sort clusters by risk level
        cluster_results.sort(key=lambda c: c.average_risk_score, reverse=True)
        
        return IntelligenceResponse(
            query_type=request.query_type,
            analysis_timestamp=datetime.utcnow(),
            geographic_clusters=cluster_results,
            confidence_score=0.85  # High confidence for geographic analysis
        )
    
    async def _analyze_industry_risk_clusters(
        self,
        request: IntelligenceRequest,
        db: Session,
        organization_id: int
    ) -> IntelligenceResponse:
        """Analyze industry risk clustering."""
        
        # Get suppliers grouped by industry
        suppliers = db.query(Supplier).filter(
            Supplier.organization_id == organization_id,
            Supplier.is_active == True,
            Supplier.industry.isnot(None)
        ).all()
        
        # Group suppliers by industry
        industry_clusters = {}
        
        for supplier in suppliers:
            industry = supplier.industry
            
            if industry not in industry_clusters:
                industry_clusters[industry] = {
                    "suppliers": [],
                    "total_contract_value": 0.0
                }
            
            industry_clusters[industry]["suppliers"].append(supplier)
            
            # Get contract value for this supplier
            contract_value = await self._get_supplier_total_contract_value(db, supplier.name)
            industry_clusters[industry]["total_contract_value"] += contract_value or 0.0
        
        # Create cluster analysis
        cluster_results = []
        
        for industry, data in industry_clusters.items():
            suppliers_in_industry = data["suppliers"]
            
            if not suppliers_in_industry:
                continue
            
            # Calculate cluster metrics
            # Normalize risk scores from 0-100 to 0-10 scale
            normalized_risk_scores = [s.risk_score / 10.0 for s in suppliers_in_industry]
            average_risk_score = sum(normalized_risk_scores) / len(normalized_risk_scores)
            
            # Get industry risk data
            industry_risk_data = self.industry_risk_data.get(industry, {})
            
            # Calculate market volatility based on risk score variance
            risk_scores = [s.risk_score for s in suppliers_in_industry]
            market_volatility = np.std(risk_scores) if len(risk_scores) > 1 else 0.0
            
            # Generate industry-specific insights
            cluster = IndustryRiskCluster(
                industry=industry,
                sub_industries=[],  # Could be enhanced with more detailed classification
                supplier_count=len(suppliers_in_industry),
                average_risk_score=average_risk_score,
                total_contract_value=data["total_contract_value"],
                market_volatility=market_volatility,
                regulatory_burden=industry_risk_data.get("regulatory_burden", "medium"),
                supply_chain_risk=industry_risk_data.get("supply_chain_risk", 5.0),
                technology_disruption_risk=industry_risk_data.get("technology_disruption_risk", 4.0),
                regulatory_change_risk=industry_risk_data.get("regulatory_change_risk", 4.0),
                market_demand_risk=industry_risk_data.get("market_demand_risk", 4.0),
                growth_outlook=industry_risk_data.get("growth_outlook", "stable"),
                emerging_risks=industry_risk_data.get("emerging_risks", []),
                opportunities=industry_risk_data.get("opportunities", [])
            )
            
            cluster_results.append(cluster)
        
        # Sort clusters by risk level
        cluster_results.sort(key=lambda c: c.average_risk_score, reverse=True)
        
        return IntelligenceResponse(
            query_type=request.query_type,
            analysis_timestamp=datetime.utcnow(),
            industry_clusters=cluster_results,
            confidence_score=0.80
        )
    
    async def _assess_contract_impact(
        self,
        request: IntelligenceRequest,
        db: Session,
        organization_id: int
    ) -> IntelligenceResponse:
        """Assess contract risk impact on supplier evaluation."""
        
        # Get suppliers with their contract information
        suppliers_query = db.query(Supplier).filter(
            Supplier.organization_id == organization_id,
            Supplier.is_active == True
        )
        
        if request.supplier_ids:
            suppliers_query = suppliers_query.filter(Supplier.id.in_(request.supplier_ids))
        
        suppliers = suppliers_query.all()
        
        contract_impacts = []
        
        for supplier in suppliers:
            # Get contracts for this supplier
            contracts = db.query(Document).filter(
                Document.extracted_metadata.op('->>')('supplier_name') == supplier.name
            ).all()
            
            if not contracts:
                continue
            
            # Analyze contract risk factors
            high_risk_clauses = []
            total_contract_value = 0.0
            expiring_soon_count = 0
            
            for contract in contracts:
                # Get contract clauses
                clauses = db.query(ContractClause).filter(
                    ContractClause.contract_id == contract.id,
                    ContractClause.risk_level.in_(['high', 'critical'])
                ).all()
                
                for clause in clauses:
                    high_risk_clauses.append({
                        "contract_id": contract.id,
                        "clause_type": clause.clause_type,
                        "risk_level": clause.risk_level,
                        "confidence_score": clause.confidence_score
                    })
                
                # Calculate contract value
                metadata = contract.extracted_metadata or {}
                contract_value = float(metadata.get('total_value', 0)) if metadata.get('total_value') else 0.0
                total_contract_value += contract_value
                
                # Check for expiring contracts
                end_date_str = metadata.get('end_date')
                if end_date_str:
                    try:
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                        if end_date <= datetime.utcnow() + timedelta(days=90):
                            expiring_soon_count += 1
                    except ValueError:
                        pass
            
            # Calculate contract-adjusted risk score
            base_risk_score = supplier.risk_score
            contract_risk_adjustment = 0.0
            
            # Adjust for high-risk clauses
            if high_risk_clauses:
                clause_risk_factor = len([c for c in high_risk_clauses if c['risk_level'] == 'critical']) * 0.5
                clause_risk_factor += len([c for c in high_risk_clauses if c['risk_level'] == 'high']) * 0.3
                contract_risk_adjustment += min(clause_risk_factor, 2.0)
            
            # Adjust for contract concentration
            contract_concentration = len(contracts) / 10.0  # Normalize by expected contract count
            if contract_concentration > 1.0:
                contract_risk_adjustment += min(contract_concentration - 1.0, 1.0)
            
            # Adjust for expiring contracts
            if expiring_soon_count > 0:
                contract_risk_adjustment += min(expiring_soon_count * 0.2, 1.0)
            
            contract_adjusted_risk_score = min(base_risk_score + contract_risk_adjustment, 10.0)
            impact_magnitude = contract_adjusted_risk_score - base_risk_score
            
            # Generate risk drivers and suggestions
            risk_drivers = []
            mitigation_suggestions = []
            monitoring_requirements = []
            
            if high_risk_clauses:
                risk_drivers.append(f"{len(high_risk_clauses)} high-risk contract clauses")
                mitigation_suggestions.append("Review and renegotiate high-risk clauses")
                monitoring_requirements.append("Regular clause compliance monitoring")
            
            if contract_concentration > 1.0:
                risk_drivers.append("High contract concentration")
                mitigation_suggestions.append("Consider diversifying contract portfolio")
            
            if expiring_soon_count > 0:
                risk_drivers.append(f"{expiring_soon_count} contracts expiring soon")
                mitigation_suggestions.append("Initiate early renewal discussions")
                monitoring_requirements.append("Contract expiration tracking")
            
            contract_impact = ContractImpactAssessment(
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                base_risk_score=base_risk_score,
                contract_adjusted_risk_score=contract_adjusted_risk_score,
                impact_magnitude=impact_magnitude,
                high_risk_clauses=high_risk_clauses,
                contract_concentration=contract_concentration,
                value_exposure=total_contract_value,
                expiry_risk=expiring_soon_count / max(len(contracts), 1),
                risk_drivers=risk_drivers,
                mitigation_suggestions=mitigation_suggestions,
                monitoring_requirements=monitoring_requirements
            )
            
            contract_impacts.append(contract_impact)
        
        # Sort by impact magnitude
        contract_impacts.sort(key=lambda c: c.impact_magnitude, reverse=True)
        
        return IntelligenceResponse(
            query_type=request.query_type,
            analysis_timestamp=datetime.utcnow(),
            contract_impacts=contract_impacts,
            confidence_score=0.75
        )
    
    async def _analyze_supplier_trends(
        self,
        request: IntelligenceRequest,
        db: Session,
        organization_id: int
    ) -> IntelligenceResponse:
        """Analyze supplier risk and performance trends."""
        
        # Get suppliers and their historical risk assessments
        suppliers_query = db.query(Supplier).filter(
            Supplier.organization_id == organization_id,
            Supplier.is_active == True
        )
        
        if request.supplier_ids:
            suppliers_query = suppliers_query.filter(Supplier.id.in_(request.supplier_ids))
        
        suppliers = suppliers_query.all()
        
        trend_analyses = []
        
        for supplier in suppliers:
            # Get historical risk assessments
            assessments = db.query(SupplierRiskAssessment).filter(
                SupplierRiskAssessment.supplier_id == supplier.id
            ).order_by(SupplierRiskAssessment.created_at).all()
            
            if len(assessments) < 2:
                continue  # Need at least 2 points for trend analysis
            
            # Extract risk score trend
            risk_score_trend = [(a.created_at, a.risk_score) for a in assessments]
            
            # Calculate trend indicators
            risk_scores = [a.risk_score for a in assessments]
            dates = [a.created_at for a in assessments]
            
            # Simple linear trend analysis
            risk_direction = "stable"
            velocity = 0.0
            
            if len(risk_scores) >= 2:
                recent_score = risk_scores[-1]
                older_score = risk_scores[-2]
                score_change = recent_score - older_score
                
                if score_change > 0.5:
                    risk_direction = "deteriorating"
                elif score_change < -0.5:
                    risk_direction = "improving"
                
                # Calculate velocity (change per month)
                time_diff = (dates[-1] - dates[-2]).days
                if time_diff > 0:
                    velocity = score_change / (time_diff / 30.0)
            
            # Simple predictions (in production, use more sophisticated models)
            current_risk = supplier.risk_score
            predicted_risk_30d = max(0.0, min(10.0, current_risk + velocity))
            predicted_risk_90d = max(0.0, min(10.0, current_risk + velocity * 3))
            
            # Generate alerts and recommendations
            trend_alerts = []
            recommended_actions = []
            
            if risk_direction == "deteriorating" and velocity > 0.1:
                trend_alerts.append("Risk score increasing - requires attention")
                recommended_actions.append("Conduct immediate risk reassessment")
            
            if predicted_risk_30d > 7.0:
                trend_alerts.append("Predicted high risk within 30 days")
                recommended_actions.append("Consider risk mitigation measures")
            
            trend_analysis = TrendAnalysisResult(
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                risk_score_trend=risk_score_trend,
                contract_value_trend=[],  # Could be enhanced with contract value history
                performance_trend=[],     # Could be enhanced with performance metrics
                risk_direction=risk_direction,
                velocity=velocity,
                acceleration=0.0,  # Could be calculated with more data points
                predicted_risk_30d=predicted_risk_30d,
                predicted_risk_90d=predicted_risk_90d,
                confidence_interval=(predicted_risk_30d * 0.8, predicted_risk_30d * 1.2),
                trend_alerts=trend_alerts,
                recommended_actions=recommended_actions
            )
            
            trend_analyses.append(trend_analysis)
        
        return IntelligenceResponse(
            query_type=request.query_type,
            analysis_timestamp=datetime.utcnow(),
            trend_analyses=trend_analyses,
            confidence_score=0.70
        )
    
    async def _predict_risk_scenarios(
        self,
        request: IntelligenceRequest,
        db: Session,
        organization_id: int
    ) -> IntelligenceResponse:
        """Generate predictive risk modeling scenarios."""
        
        # This is a placeholder for advanced predictive modeling
        # In production, this would use machine learning models
        
        return IntelligenceResponse(
            query_type=request.query_type,
            analysis_timestamp=datetime.utcnow(),
            key_insights=["Predictive risk modeling - feature coming soon"],
            confidence_score=0.50
        )
    
    async def _analyze_cross_system_correlations(
        self,
        request: IntelligenceRequest,
        db: Session,
        organization_id: int
    ) -> IntelligenceResponse:
        """Analyze correlations between supplier and contract risk factors."""
        
        # This is a placeholder for cross-system correlation analysis
        # In production, this would analyze correlations between various risk factors
        
        return IntelligenceResponse(
            query_type=request.query_type,
            analysis_timestamp=datetime.utcnow(),
            key_insights=["Cross-system correlation analysis - feature coming soon"],
            confidence_score=0.50
        )
    
    async def _generate_intelligent_recommendations(
        self,
        request: IntelligenceRequest,
        db: Session,
        organization_id: int
    ) -> IntelligenceResponse:
        """Generate AI-powered intelligent recommendations."""
        
        # Get portfolio analysis first
        portfolio_request = IntelligenceRequest(
            query_type=IntelligenceQueryType.PORTFOLIO_RISK_ANALYSIS,
            supplier_ids=request.supplier_ids,
            industries=request.industries,
            countries=request.countries,
            include_recommendations=False
        )
        
        portfolio_response = await self._analyze_portfolio_risk(portfolio_request, db, organization_id)
        
        if not portfolio_response.portfolio_analysis:
            return IntelligenceResponse(
                query_type=request.query_type,
                analysis_timestamp=datetime.utcnow(),
                key_insights=["No data available for generating recommendations"],
                confidence_score=0.0
            )
        
        portfolio = portfolio_response.portfolio_analysis
        
        # Generate AI-powered recommendations using OpenAI
        recommendations_prompt = self._build_recommendations_prompt(portfolio)
        
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a procurement and supplier risk management expert."},
                    {"role": "user", "content": recommendations_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            ai_recommendations = response.choices[0].message.content
            
            # Parse the AI response into structured recommendations
            strategic_recommendations = self._parse_ai_recommendations(ai_recommendations)
            
        except Exception as e:
            logger.warning("Failed to generate AI recommendations", error=str(e))
            strategic_recommendations = portfolio.strategic_recommendations
        
        return IntelligenceResponse(
            query_type=request.query_type,
            analysis_timestamp=datetime.utcnow(),
            strategic_recommendations=strategic_recommendations,
            confidence_score=0.85
        )
    
    async def _enhance_with_ai_insights(
        self,
        response: IntelligenceResponse,
        request: IntelligenceRequest,
        db: Session,
        organization_id: int
    ):
        """Enhance response with AI-generated insights."""
        
        # Generate contextual insights based on the analysis results
        insights_prompt = self._build_insights_prompt(response, request)
        
        try:
            ai_response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert procurement analyst providing strategic insights."},
                    {"role": "user", "content": insights_prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            ai_insights = ai_response.choices[0].message.content
            
            # Parse and structure the insights
            parsed_insights = self._parse_ai_insights(ai_insights)
            
            response.key_insights = parsed_insights.get("insights", [])
            response.risk_alerts = parsed_insights.get("alerts", [])
            response.opportunities = parsed_insights.get("opportunities", [])
            
        except Exception as e:
            logger.warning("Failed to generate AI insights", error=str(e))
    
    # Helper methods
    
    def _initialize_geographic_risk_data(self) -> Dict[str, Dict[str, Any]]:
        """Initialize geographic risk data mappings."""
        return {
            "North America": {
                "political_risk": 2.0,
                "economic_risk": 3.0,
                "regulatory_risk": 4.0,
                "natural_disaster_risk": 3.0
            },
            "Europe": {
                "political_risk": 2.5,
                "economic_risk": 3.5,
                "regulatory_risk": 5.0,
                "natural_disaster_risk": 2.0
            },
            "Asia-Pacific": {
                "political_risk": 4.0,
                "economic_risk": 4.0,
                "regulatory_risk": 4.5,
                "natural_disaster_risk": 4.0
            },
            "Latin America": {
                "political_risk": 5.0,
                "economic_risk": 5.0,
                "regulatory_risk": 4.0,
                "natural_disaster_risk": 4.5
            },
            "Middle East & Africa": {
                "political_risk": 6.0,
                "economic_risk": 5.5,
                "regulatory_risk": 4.5,
                "natural_disaster_risk": 3.5
            }
        }
    
    def _initialize_industry_risk_data(self) -> Dict[str, Dict[str, Any]]:
        """Initialize industry risk data mappings."""
        return {
            "Technology": {
                "regulatory_burden": "medium",
                "supply_chain_risk": 4.0,
                "technology_disruption_risk": 7.0,
                "regulatory_change_risk": 3.0,
                "market_demand_risk": 5.0,
                "growth_outlook": "positive",
                "emerging_risks": ["AI regulation", "data privacy"],
                "opportunities": ["digital transformation", "automation"]
            },
            "Healthcare": {
                "regulatory_burden": "high",
                "supply_chain_risk": 6.0,
                "technology_disruption_risk": 4.0,
                "regulatory_change_risk": 8.0,
                "market_demand_risk": 2.0,
                "growth_outlook": "positive",
                "emerging_risks": ["regulatory changes", "patent expiry"],
                "opportunities": ["aging population", "personalized medicine"]
            },
            "Manufacturing": {
                "regulatory_burden": "medium",
                "supply_chain_risk": 7.0,
                "technology_disruption_risk": 5.0,
                "regulatory_change_risk": 4.0,
                "market_demand_risk": 6.0,
                "growth_outlook": "stable",
                "emerging_risks": ["supply chain disruption", "automation"],
                "opportunities": ["Industry 4.0", "sustainability"]
            }
        }
    
    def _map_country_to_region(self, country: str) -> str:
        """Map country to geographic region."""
        region_mapping = {
            "United States": "North America",
            "Canada": "North America",
            "Mexico": "North America",
            "United Kingdom": "Europe",
            "Germany": "Europe",
            "France": "Europe",
            "China": "Asia-Pacific",
            "Japan": "Asia-Pacific",
            "India": "Asia-Pacific",
            "Brazil": "Latin America",
            "Argentina": "Latin America",
            "South Africa": "Middle East & Africa",
            "UAE": "Middle East & Africa"
        }
        return region_mapping.get(country, "Other")
    
    def _calculate_diversification_index(
        self, 
        geographic_dist: Dict[str, int], 
        industry_dist: Dict[str, int]
    ) -> float:
        """Calculate portfolio diversification index."""
        # Simple Herfindahl-Hirschman Index calculation
        total_suppliers = sum(geographic_dist.values())
        
        if total_suppliers == 0:
            return 0.0
        
        # Geographic concentration
        geo_hhi = sum((count / total_suppliers) ** 2 for count in geographic_dist.values())
        
        # Industry concentration
        ind_hhi = sum((count / total_suppliers) ** 2 for count in industry_dist.values())
        
        # Combined diversification index (inverted HHI, higher = more diversified)
        diversification = 1.0 - (geo_hhi + ind_hhi) / 2.0
        
        return max(0.0, min(1.0, diversification))
    
    def _calculate_concentration_risk(self, supplier_contract_values: Dict[int, float]) -> float:
        """Calculate concentration risk based on contract value distribution."""
        values = list(supplier_contract_values.values())
        total_value = sum(values)
        
        if total_value == 0:
            return 0.0
        
        # Calculate Gini coefficient as concentration measure
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n == 0:
            return 0.0
        
        cumsum = np.cumsum(sorted_values)
        gini = (n + 1 - 2 * sum((n + 1 - i) * v for i, v in enumerate(sorted_values, 1))) / (n * total_value)
        
        return max(0.0, min(1.0, gini))
    
    async def _get_supplier_total_contract_value(self, db: Session, supplier_name: str) -> Optional[float]:
        """Get total contract value for a supplier."""
        try:
            # Use a simpler approach to avoid SQLAlchemy type issues
            contracts = db.query(Document).filter(
                Document.extracted_metadata.op('->>')('supplier_name') == supplier_name
            ).all()
            
            total_value = 0.0
            for contract in contracts:
                metadata = contract.extracted_metadata or {}
                contract_value = metadata.get('total_value')
                if contract_value:
                    try:
                        total_value += float(contract_value)
                    except (ValueError, TypeError):
                        continue
            
            return total_value if total_value > 0 else None
            
        except Exception as e:
            logger.warning(f"Failed to get contract value for supplier {supplier_name}: {str(e)}")
            return None
    
    async def _analyze_portfolio_risk_trends(
        self, 
        db: Session, 
        suppliers: List[Supplier], 
        organization_id: int
    ) -> Dict[str, str]:
        """Analyze portfolio risk trends over different time periods."""
        
        # This is a simplified implementation
        # In production, this would analyze historical risk data
        
        return {
            "30d": "stable",
            "90d": "stable", 
            "365d": "improving"
        }
    
    def _identify_optimization_opportunities(
        self,
        suppliers: List[Supplier],
        supplier_contract_values: Dict[int, float],
        risk_distribution: Dict[str, int],
        geographic_distribution: Dict[str, int]
    ) -> List[str]:
        """Identify portfolio optimization opportunities."""
        
        opportunities = []
        
        # Check for high-risk concentration
        high_risk_count = risk_distribution.get('HIGH', 0) + risk_distribution.get('CRITICAL', 0)
        if high_risk_count > len(suppliers) * 0.2:
            opportunities.append("Reduce high-risk supplier concentration")
        
        # Check for geographic concentration
        max_geographic_concentration = max(geographic_distribution.values()) if geographic_distribution else 0
        if max_geographic_concentration > len(suppliers) * 0.5:
            opportunities.append("Diversify geographic supplier base")
        
        # Check for contract value concentration
        total_value = sum(supplier_contract_values.values())
        if total_value > 0:
            max_supplier_value = max(supplier_contract_values.values())
            if max_supplier_value > total_value * 0.3:
                opportunities.append("Reduce contract value concentration with single suppliers")
        
        return opportunities
    
    def _generate_portfolio_recommendations(
        self,
        portfolio_risk_score: float,
        diversification_index: float,
        concentration_risk: float,
        risk_distribution: Dict[str, int]
    ) -> List[str]:
        """Generate strategic portfolio recommendations."""
        
        recommendations = []
        
        if portfolio_risk_score > 6.0:
            recommendations.append("Portfolio risk score is high - consider risk reduction strategies")
        
        if diversification_index < 0.5:
            recommendations.append("Increase supplier diversification across geographies and industries")
        
        if concentration_risk > 0.6:
            recommendations.append("Address high contract value concentration risk")
        
        high_risk_suppliers = risk_distribution.get('HIGH', 0) + risk_distribution.get('CRITICAL', 0)
        if high_risk_suppliers > 0:
            recommendations.append(f"Prioritize risk mitigation for {high_risk_suppliers} high-risk suppliers")
        
        return recommendations
    
    async def _identify_high_risk_contracts(self, db: Session, supplier_ids: List[int]) -> List[int]:
        """Identify contracts requiring attention based on supplier risk."""
        
        if not supplier_ids:
            return []
        
        # Get supplier names for high-risk suppliers
        suppliers = db.query(Supplier.name).filter(Supplier.id.in_(supplier_ids)).all()
        supplier_names = [s.name for s in suppliers]
        
        # Find contracts with these suppliers
        contracts = db.query(Document.id).filter(
            Document.extracted_metadata.op('->>')('supplier_name').in_(supplier_names)
        ).all()
        
        return [c.id for c in contracts]
    
    def _calculate_portfolio_confidence_score(
        self, 
        suppliers: List[Supplier], 
        supplier_contract_values: Dict[int, float]
    ) -> float:
        """Calculate confidence score based on data completeness."""
        
        if not suppliers:
            return 0.0
        
        # Check data completeness
        complete_suppliers = 0
        
        for supplier in suppliers:
            completeness_score = 0
            
            # Check basic data
            if supplier.name: completeness_score += 1
            if supplier.industry: completeness_score += 1
            if supplier.country: completeness_score += 1
            if supplier.risk_score is not None: completeness_score += 1
            if supplier.last_risk_assessment: completeness_score += 1
            
            # Check contract data
            if supplier_contract_values.get(supplier.id, 0) > 0:
                completeness_score += 1
            
            # Consider supplier complete if it has most data
            if completeness_score >= 4:
                complete_suppliers += 1
        
        return complete_suppliers / len(suppliers)
    
    def _determine_cluster_risk_level(self, average_risk_score: float, regional_risk_data: Dict[str, Any]) -> str:
        """Determine overall risk level for a cluster."""
        
        # Combine supplier risk score with regional factors
        political_risk = regional_risk_data.get("political_risk", 3.0)
        economic_risk = regional_risk_data.get("economic_risk", 3.0)
        
        combined_risk = (average_risk_score + political_risk + economic_risk) / 3.0
        
        if combined_risk >= 7.0:
            return "critical"
        elif combined_risk >= 5.0:
            return "high"
        elif combined_risk >= 3.0:
            return "medium"
        else:
            return "low"
    
    def _identify_geographic_risk_factors(
        self, 
        region: str, 
        suppliers: List[Supplier], 
        regional_risk_data: Dict[str, Any]
    ) -> List[str]:
        """Identify risk factors for a geographic region."""
        
        risk_factors = []
        
        # Regional factors
        if regional_risk_data.get("political_risk", 0) > 5.0:
            risk_factors.append("High political risk in region")
        
        if regional_risk_data.get("economic_risk", 0) > 5.0:
            risk_factors.append("Economic instability in region")
        
        if regional_risk_data.get("regulatory_risk", 0) > 5.0:
            risk_factors.append("Complex regulatory environment")
        
        # Supplier-specific factors
        high_risk_suppliers = [s for s in suppliers if s.risk_level in ['HIGH', 'CRITICAL']]
        if len(high_risk_suppliers) > len(suppliers) * 0.3:
            risk_factors.append("High concentration of risky suppliers")
        
        return risk_factors
    
    def _generate_geographic_mitigation_strategies(self, region: str, risk_factors: List[str]) -> List[str]:
        """Generate mitigation strategies for geographic risks."""
        
        strategies = []
        
        if "political risk" in ' '.join(risk_factors).lower():
            strategies.append("Implement political risk insurance")
            strategies.append("Diversify suppliers across stable countries")
        
        if "economic" in ' '.join(risk_factors).lower():
            strategies.append("Use local currency hedging")
            strategies.append("Establish backup suppliers in stable regions")
        
        if "regulatory" in ' '.join(risk_factors).lower():
            strategies.append("Engage local compliance experts")
            strategies.append("Monitor regulatory changes actively")
        
        return strategies
    
    def _generate_monitoring_priorities(self, region: str, risk_factors: List[str]) -> List[str]:
        """Generate monitoring priorities for a region."""
        
        priorities = []
        
        priorities.append("Political stability indicators")
        priorities.append("Economic performance metrics")
        priorities.append("Regulatory change tracking")
        priorities.append("Supplier performance monitoring")
        
        return priorities
    
    async def _analyze_geographic_trend(
        self, 
        db: Session, 
        region: str, 
        suppliers: List[Supplier]
    ) -> str:
        """Analyze geographic risk trend."""
        
        # This is a simplified implementation
        # In production, this would analyze historical data
        
        return "stable"
    
    def _build_recommendations_prompt(self, portfolio: PortfolioAnalysis) -> str:
        """Build prompt for AI-powered recommendations."""
        
        return f"""
        Analyze this supplier portfolio and provide strategic recommendations:
        
        Portfolio Overview:
        - Total suppliers: {portfolio.total_suppliers}
        - Total contract value: ${portfolio.total_contract_value:,.2f}
        - Portfolio risk score: {portfolio.portfolio_risk_score:.2f}/10
        - Diversification index: {portfolio.diversification_index:.2f}
        - Concentration risk: {portfolio.concentration_risk:.2f}
        
        Risk Distribution: {portfolio.risk_distribution}
        Geographic Distribution: {portfolio.geographic_distribution}
        Industry Distribution: {portfolio.industry_distribution}
        
        Current Optimization Opportunities:
        {chr(10).join('- ' + opp for opp in portfolio.optimization_opportunities)}
        
        Provide 5-7 strategic recommendations focusing on:
        1. Risk reduction strategies
        2. Portfolio optimization
        3. Diversification improvements
        4. Operational efficiencies
        5. Strategic supplier management
        
        Format as a numbered list with actionable recommendations.
        """
    
    def _parse_ai_recommendations(self, ai_response: str) -> List[str]:
        """Parse AI response into structured recommendations."""
        
        # Extract numbered recommendations
        import re
        
        recommendations = []
        lines = ai_response.split('\n')
        
        for line in lines:
            # Look for numbered items
            match = re.match(r'^\d+\.?\s+(.+)', line.strip())
            if match:
                recommendations.append(match.group(1))
            # Also look for bullet points
            elif line.strip().startswith('- '):
                recommendations.append(line.strip()[2:])
        
        return recommendations if recommendations else [ai_response]
    
    def _build_insights_prompt(self, response: IntelligenceResponse, request: IntelligenceRequest) -> str:
        """Build prompt for AI-powered insights generation."""
        
        analysis_summary = f"Analysis Type: {request.query_type}\n"
        
        if response.portfolio_analysis:
            analysis_summary += f"Portfolio Risk Score: {response.portfolio_analysis.portfolio_risk_score:.2f}\n"
        
        if response.geographic_clusters:
            analysis_summary += f"Geographic Clusters: {len(response.geographic_clusters)}\n"
        
        if response.industry_clusters:
            analysis_summary += f"Industry Clusters: {len(response.industry_clusters)}\n"
        
        return f"""
        Based on this supplier intelligence analysis, provide key insights, risk alerts, and opportunities:
        
        {analysis_summary}
        
        Generate:
        1. Key Insights: 3-5 important findings from the analysis
        2. Risk Alerts: Critical risks requiring immediate attention
        3. Opportunities: Strategic opportunities identified
        
        Return as JSON with keys: "insights", "alerts", "opportunities"
        """
    
    def _parse_ai_insights(self, ai_response: str) -> Dict[str, List[str]]:
        """Parse AI insights response."""
        
        try:
            # Try to parse as JSON
            import json
            return json.loads(ai_response)
        except json.JSONDecodeError:
            # Fallback parsing
            return {
                "insights": [ai_response],
                "alerts": [],
                "opportunities": []
            }
