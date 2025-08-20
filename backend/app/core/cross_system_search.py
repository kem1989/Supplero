"""
Cross-System Search Service for Supplier Intelligence Hub

This service provides cross-system query capabilities that bridge suppliers and contracts,
enabling complex queries like "Find suppliers with risky contracts" or "Show suppliers 
with expiring contracts".
"""

import structlog
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text, distinct
from dataclasses import dataclass
from enum import Enum

from app.models.supplier import Supplier, SupplierRiskAssessment
from app.models.document import Document, ContractClause
from app.models.organization import Organization
from app.core.elasticsearch_service import ElasticsearchService

logger = structlog.get_logger(__name__)


class CrossSystemQueryType(str, Enum):
    """Types of cross-system queries supported"""
    SUPPLIERS_WITH_RISKY_CONTRACTS = "suppliers_with_risky_contracts"
    SUPPLIERS_WITH_EXPIRING_CONTRACTS = "suppliers_with_expiring_contracts"
    SUPPLIERS_BY_CONTRACT_CLAUSES = "suppliers_by_contract_clauses"
    SUPPLIERS_BY_CONTRACT_VALUE = "suppliers_by_contract_value"
    SUPPLIERS_WITH_CONTRACT_GAPS = "suppliers_with_contract_gaps"
    CONTRACTS_BY_SUPPLIER_RISK = "contracts_by_supplier_risk"
    UNIFIED_RISK_SEARCH = "unified_risk_search"


@dataclass
class CrossSystemSearchRequest:
    """Request model for cross-system searches"""
    query_type: CrossSystemQueryType
    query_text: Optional[str] = None
    
    # Contract-based filters
    contract_risk_level: Optional[str] = None  # low, medium, high, critical
    contract_value_min: Optional[float] = None
    contract_value_max: Optional[float] = None
    contract_expiring_days: Optional[int] = None  # contracts expiring within X days
    clause_types: Optional[List[str]] = None  # force_majeure, termination, etc.
    
    # Supplier-based filters
    supplier_risk_level: Optional[str] = None
    supplier_industries: Optional[List[str]] = None
    supplier_countries: Optional[List[str]] = None
    
    # Pagination
    page: int = 1
    page_size: int = 20
    
    # Sorting
    sort_by: str = "relevance"  # relevance, risk_score, contract_value, expiry_date
    sort_order: str = "desc"


@dataclass
class SupplierContractInfo:
    """Combined supplier and contract information"""
    # Supplier info
    supplier_id: int
    supplier_name: str
    supplier_risk_score: float
    supplier_risk_level: str
    supplier_industry: Optional[str]
    supplier_country: Optional[str]
    
    # Contract info
    contract_count: int
    total_contract_value: Optional[float]
    highest_risk_contract_id: Optional[int]
    highest_risk_contract_risk: Optional[str]
    expiring_contracts_count: int
    recent_contracts_count: int
    
    # Risk indicators
    combined_risk_score: float
    risk_factors: List[str]
    
    # Metadata
    last_assessment_date: Optional[datetime]
    created_at: datetime


@dataclass
class ContractSupplierInfo:
    """Combined contract and supplier information"""
    # Contract info
    document_id: int
    document_title: str
    contract_value: Optional[float]
    contract_start_date: Optional[datetime]
    contract_end_date: Optional[datetime]
    contract_status: str
    clause_risk_level: Optional[str]
    
    # Supplier info
    supplier_id: Optional[int]
    supplier_name: Optional[str]
    supplier_risk_score: Optional[float]
    supplier_risk_level: Optional[str]
    
    # Combined risk
    combined_risk_score: float
    risk_explanation: str
    
    # Metadata
    last_updated: datetime


@dataclass
class CrossSystemSearchResponse:
    """Response model for cross-system searches"""
    query_type: CrossSystemQueryType
    supplier_results: List[SupplierContractInfo]
    contract_results: List[ContractSupplierInfo]
    
    # Statistics
    total_suppliers: int
    total_contracts: int
    high_risk_count: int
    expiring_soon_count: int
    
    # Search metadata
    search_time_ms: float
    page: int
    page_size: int
    total_pages: int
    
    # Insights
    key_insights: List[str]
    recommended_actions: List[str]


class CrossSystemSearchService:
    """Service for cross-system queries bridging suppliers and contracts"""
    
    def __init__(self):
        self.elasticsearch_service = ElasticsearchService()
    
    async def execute_cross_system_search(
        self,
        request: CrossSystemSearchRequest,
        db: Session,
        organization_id: int
    ) -> CrossSystemSearchResponse:
        """
        Execute a cross-system search based on the query type and parameters.
        
        Args:
            request: Cross-system search request
            db: Database session
            organization_id: Organization ID for filtering
            
        Returns:
            CrossSystemSearchResponse with combined results and insights
        """
        start_time = datetime.utcnow()
        
        logger.info(
            "Starting cross-system search",
            query_type=request.query_type,
            organization_id=organization_id,
            query_text=request.query_text
        )
        
        try:
            # Route to appropriate search method based on query type
            if request.query_type == CrossSystemQueryType.SUPPLIERS_WITH_RISKY_CONTRACTS:
                response = await self._search_suppliers_with_risky_contracts(request, db, organization_id)
            elif request.query_type == CrossSystemQueryType.SUPPLIERS_WITH_EXPIRING_CONTRACTS:
                response = await self._search_suppliers_with_expiring_contracts(request, db, organization_id)
            elif request.query_type == CrossSystemQueryType.SUPPLIERS_BY_CONTRACT_CLAUSES:
                response = await self._search_suppliers_by_contract_clauses(request, db, organization_id)
            elif request.query_type == CrossSystemQueryType.SUPPLIERS_BY_CONTRACT_VALUE:
                response = await self._search_suppliers_by_contract_value(request, db, organization_id)
            elif request.query_type == CrossSystemQueryType.CONTRACTS_BY_SUPPLIER_RISK:
                response = await self._search_contracts_by_supplier_risk(request, db, organization_id)
            elif request.query_type == CrossSystemQueryType.UNIFIED_RISK_SEARCH:
                response = await self._unified_risk_search(request, db, organization_id)
            else:
                raise ValueError(f"Unsupported query type: {request.query_type}")
            
            # Calculate search time
            search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            response.search_time_ms = search_time
            
            logger.info(
                "Cross-system search completed",
                query_type=request.query_type,
                supplier_count=len(response.supplier_results),
                contract_count=len(response.contract_results),
                search_time_ms=search_time
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Cross-system search failed",
                query_type=request.query_type,
                organization_id=organization_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _search_suppliers_with_risky_contracts(
        self,
        request: CrossSystemSearchRequest,
        db: Session,
        organization_id: int
    ) -> CrossSystemSearchResponse:
        """Find suppliers that have contracts with high risk factors."""
        
        # Base query for suppliers with contracts
        query = db.query(
            Supplier,
            func.count(Document.id).label('contract_count'),
            func.coalesce(func.sum(
                func.cast(Document.extracted_metadata.op('->>')('total_value'), func.numeric())
            ), 0).label('total_value'),
            func.max(ContractClause.risk_level).label('highest_risk')
        ).join(
            Document,
            Document.extracted_metadata.op('->>')('supplier_name') == Supplier.name
        ).outerjoin(
            ContractClause,
            ContractClause.contract_id == Document.id
        ).filter(
            Supplier.organization_id == organization_id
        )
        
        # Apply risk level filter for contracts
        if request.contract_risk_level:
            risk_levels = {
                'low': ['low'],
                'medium': ['low', 'medium'],
                'high': ['low', 'medium', 'high'],
                'critical': ['low', 'medium', 'high', 'critical']
            }
            acceptable_risks = risk_levels.get(request.contract_risk_level, ['high', 'critical'])
            query = query.filter(ContractClause.risk_level.in_(acceptable_risks))
        else:
            # Default to high and critical risk contracts
            query = query.filter(ContractClause.risk_level.in_(['high', 'critical']))
        
        # Apply supplier risk filter
        if request.supplier_risk_level:
            query = query.filter(Supplier.risk_level == request.supplier_risk_level.upper())
        
        # Apply industry filter
        if request.supplier_industries:
            query = query.filter(Supplier.industry.in_(request.supplier_industries))
        
        # Apply country filter
        if request.supplier_countries:
            query = query.filter(Supplier.country.in_(request.supplier_countries))
        
        # Group by supplier
        query = query.group_by(Supplier.id)
        
        # Apply pagination
        total_count = query.count()
        offset = (request.page - 1) * request.page_size
        results = query.offset(offset).limit(request.page_size).all()
        
        # Convert to response format
        supplier_results = []
        for supplier, contract_count, total_value, highest_risk in results:
            # Calculate combined risk score
            combined_risk = self._calculate_combined_risk_score(
                supplier.risk_score,
                highest_risk,
                contract_count,
                total_value
            )
            
            # Get expiring contracts count
            expiring_count = self._get_expiring_contracts_count(db, supplier.name, 30)
            
            supplier_results.append(SupplierContractInfo(
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                supplier_risk_score=supplier.risk_score,
                supplier_risk_level=supplier.risk_level,
                supplier_industry=supplier.industry,
                supplier_country=supplier.country,
                contract_count=contract_count,
                total_contract_value=float(total_value) if total_value else None,
                highest_risk_contract_risk=highest_risk,
                expiring_contracts_count=expiring_count,
                recent_contracts_count=self._get_recent_contracts_count(db, supplier.name, 90),
                combined_risk_score=combined_risk,
                risk_factors=self._identify_risk_factors(supplier, highest_risk, contract_count),
                last_assessment_date=supplier.last_risk_assessment,
                created_at=supplier.created_at,
                highest_risk_contract_id=None  # TODO: Implement if needed
            ))
        
        # Generate insights and recommendations
        insights, recommendations = self._generate_risky_contracts_insights(supplier_results)
        
        return CrossSystemSearchResponse(
            query_type=request.query_type,
            supplier_results=supplier_results,
            contract_results=[],
            total_suppliers=len(supplier_results),
            total_contracts=sum(s.contract_count for s in supplier_results),
            high_risk_count=len([s for s in supplier_results if s.combined_risk_score >= 7.0]),
            expiring_soon_count=sum(s.expiring_contracts_count for s in supplier_results),
            search_time_ms=0.0,  # Will be set by caller
            page=request.page,
            page_size=request.page_size,
            total_pages=(total_count + request.page_size - 1) // request.page_size,
            key_insights=insights,
            recommended_actions=recommendations
        )
    
    async def _search_suppliers_with_expiring_contracts(
        self,
        request: CrossSystemSearchRequest,
        db: Session,
        organization_id: int
    ) -> CrossSystemSearchResponse:
        """Find suppliers with contracts expiring soon."""
        
        # Calculate expiry threshold
        days_ahead = request.contract_expiring_days or 90
        expiry_threshold = datetime.utcnow() + timedelta(days=days_ahead)
        
        # Query suppliers with expiring contracts
        query = db.query(
            Supplier,
            func.count(Document.id).label('contract_count'),
            func.count(
                func.case(
                    [(func.cast(Document.extracted_metadata.op('->>')('end_date'), func.DATE) <= expiry_threshold.date(), 1)],
                    else_=0
                )
            ).label('expiring_count')
        ).join(
            Document,
            Document.extracted_metadata.op('->>')('supplier_name') == Supplier.name
        ).filter(
            Supplier.organization_id == organization_id
        ).group_by(Supplier.id).having(
            func.count(
                func.case(
                    [(func.cast(Document.extracted_metadata.op('->>')('end_date'), func.DATE) <= expiry_threshold.date(), 1)],
                    else_=0
                )
            ) > 0
        )
        
        # Apply filters
        if request.supplier_risk_level:
            query = query.filter(Supplier.risk_level == request.supplier_risk_level.upper())
        
        if request.supplier_industries:
            query = query.filter(Supplier.industry.in_(request.supplier_industries))
        
        # Apply pagination
        total_count = query.count()
        offset = (request.page - 1) * request.page_size
        results = query.offset(offset).limit(request.page_size).all()
        
        # Convert to response format
        supplier_results = []
        for supplier, contract_count, expiring_count in results:
            # Get contract value
            total_value = self._get_supplier_total_contract_value(db, supplier.name)
            
            supplier_results.append(SupplierContractInfo(
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                supplier_risk_score=supplier.risk_score,
                supplier_risk_level=supplier.risk_level,
                supplier_industry=supplier.industry,
                supplier_country=supplier.country,
                contract_count=contract_count,
                total_contract_value=total_value,
                highest_risk_contract_risk=None,
                expiring_contracts_count=expiring_count,
                recent_contracts_count=self._get_recent_contracts_count(db, supplier.name, 90),
                combined_risk_score=self._calculate_expiry_risk_score(supplier.risk_score, expiring_count, total_value),
                risk_factors=[f"{expiring_count} contracts expiring within {days_ahead} days"],
                last_assessment_date=supplier.last_risk_assessment,
                created_at=supplier.created_at,
                highest_risk_contract_id=None
            ))
        
        # Generate insights
        insights = [
            f"Found {len(supplier_results)} suppliers with contracts expiring within {days_ahead} days",
            f"Total expiring contracts: {sum(s.expiring_contracts_count for s in supplier_results)}",
            f"Average supplier risk score: {sum(s.supplier_risk_score for s in supplier_results) / len(supplier_results):.2f}" if supplier_results else "No results"
        ]
        
        recommendations = [
            "Review contract renewal timelines for critical suppliers",
            "Initiate early renewal discussions for high-risk suppliers",
            "Consider backup suppliers for critical contracts"
        ]
        
        return CrossSystemSearchResponse(
            query_type=request.query_type,
            supplier_results=supplier_results,
            contract_results=[],
            total_suppliers=len(supplier_results),
            total_contracts=sum(s.contract_count for s in supplier_results),
            high_risk_count=len([s for s in supplier_results if s.supplier_risk_level in ['HIGH', 'CRITICAL']]),
            expiring_soon_count=sum(s.expiring_contracts_count for s in supplier_results),
            search_time_ms=0.0,
            page=request.page,
            page_size=request.page_size,
            total_pages=(total_count + request.page_size - 1) // request.page_size,
            key_insights=insights,
            recommended_actions=recommendations
        )
    
    async def _search_suppliers_by_contract_clauses(
        self,
        request: CrossSystemSearchRequest,
        db: Session,
        organization_id: int
    ) -> CrossSystemSearchResponse:
        """Find suppliers based on specific contract clause types."""
        
        if not request.clause_types:
            raise ValueError("clause_types must be specified for this query type")
        
        # Query suppliers with specific clause types
        query = db.query(
            Supplier,
            func.count(distinct(Document.id)).label('contract_count'),
            func.array_agg(distinct(ContractClause.clause_type)).label('clause_types'),
            func.avg(ContractClause.confidence_score).label('avg_confidence')
        ).join(
            Document,
            Document.extracted_metadata.op('->>')('supplier_name') == Supplier.name
        ).join(
            ContractClause,
            ContractClause.contract_id == Document.id
        ).filter(
            Supplier.organization_id == organization_id,
            ContractClause.clause_type.in_(request.clause_types)
        ).group_by(Supplier.id)
        
        # Apply pagination
        total_count = query.count()
        offset = (request.page - 1) * request.page_size
        results = query.offset(offset).limit(request.page_size).all()
        
        # Convert to response format
        supplier_results = []
        for supplier, contract_count, clause_types, avg_confidence in results:
            total_value = self._get_supplier_total_contract_value(db, supplier.name)
            
            supplier_results.append(SupplierContractInfo(
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                supplier_risk_score=supplier.risk_score,
                supplier_risk_level=supplier.risk_level,
                supplier_industry=supplier.industry,
                supplier_country=supplier.country,
                contract_count=contract_count,
                total_contract_value=total_value,
                highest_risk_contract_risk=None,
                expiring_contracts_count=0,
                recent_contracts_count=contract_count,
                combined_risk_score=supplier.risk_score,
                risk_factors=[f"Contains {', '.join(request.clause_types)} clauses"],
                last_assessment_date=supplier.last_risk_assessment,
                created_at=supplier.created_at,
                highest_risk_contract_id=None
            ))
        
        # Generate insights
        insights = [
            f"Found {len(supplier_results)} suppliers with {', '.join(request.clause_types)} clauses",
            f"Total contracts containing these clauses: {sum(s.contract_count for s in supplier_results)}"
        ]
        
        recommendations = [
            f"Review {', '.join(request.clause_types)} clause language for consistency",
            "Ensure proper risk mitigation for these contract provisions"
        ]
        
        return CrossSystemSearchResponse(
            query_type=request.query_type,
            supplier_results=supplier_results,
            contract_results=[],
            total_suppliers=len(supplier_results),
            total_contracts=sum(s.contract_count for s in supplier_results),
            high_risk_count=len([s for s in supplier_results if s.supplier_risk_level in ['HIGH', 'CRITICAL']]),
            expiring_soon_count=0,
            search_time_ms=0.0,
            page=request.page,
            page_size=request.page_size,
            total_pages=(total_count + request.page_size - 1) // request.page_size,
            key_insights=insights,
            recommended_actions=recommendations
        )
    
    async def _search_suppliers_by_contract_value(
        self,
        request: CrossSystemSearchRequest,
        db: Session,
        organization_id: int
    ) -> CrossSystemSearchResponse:
        """Find suppliers based on contract value ranges."""
        
        # Base query
        query = db.query(
            Supplier,
            func.count(Document.id).label('contract_count'),
            func.coalesce(func.sum(
                func.cast(Document.extracted_metadata.op('->>')('total_value'), func.numeric())
            ), 0).label('total_value')
        ).join(
            Document,
            Document.extracted_metadata.op('->>')('supplier_name') == Supplier.name
        ).filter(
            Supplier.organization_id == organization_id
        ).group_by(Supplier.id)
        
        # Apply contract value filters
        if request.contract_value_min:
            query = query.having(
                func.coalesce(func.sum(
                    func.cast(Document.extracted_metadata.op('->>')('total_value'), func.numeric())
                ), 0) >= request.contract_value_min
            )
        
        if request.contract_value_max:
            query = query.having(
                func.coalesce(func.sum(
                    func.cast(Document.extracted_metadata.op('->>')('total_value'), func.numeric())
                ), 0) <= request.contract_value_max
            )
        
        # Apply pagination
        total_count = query.count()
        offset = (request.page - 1) * request.page_size
        results = query.offset(offset).limit(request.page_size).all()
        
        # Convert to response format
        supplier_results = []
        for supplier, contract_count, total_value in results:
            supplier_results.append(SupplierContractInfo(
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                supplier_risk_score=supplier.risk_score,
                supplier_risk_level=supplier.risk_level,
                supplier_industry=supplier.industry,
                supplier_country=supplier.country,
                contract_count=contract_count,
                total_contract_value=float(total_value) if total_value else None,
                highest_risk_contract_risk=None,
                expiring_contracts_count=0,
                recent_contracts_count=contract_count,
                combined_risk_score=supplier.risk_score,
                risk_factors=[f"Total contract value: ${total_value:,.2f}" if total_value else "No contract value data"],
                last_assessment_date=supplier.last_risk_assessment,
                created_at=supplier.created_at,
                highest_risk_contract_id=None
            ))
        
        # Generate insights
        total_portfolio_value = sum(s.total_contract_value or 0 for s in supplier_results)
        insights = [
            f"Found {len(supplier_results)} suppliers matching value criteria",
            f"Total portfolio value: ${total_portfolio_value:,.2f}",
            f"Average contract value per supplier: ${total_portfolio_value / len(supplier_results):,.2f}" if supplier_results else "No results"
        ]
        
        recommendations = [
            "Review high-value contracts for additional risk controls",
            "Consider volume discounts for suppliers with large contract values"
        ]
        
        return CrossSystemSearchResponse(
            query_type=request.query_type,
            supplier_results=supplier_results,
            contract_results=[],
            total_suppliers=len(supplier_results),
            total_contracts=sum(s.contract_count for s in supplier_results),
            high_risk_count=len([s for s in supplier_results if s.supplier_risk_level in ['HIGH', 'CRITICAL']]),
            expiring_soon_count=0,
            search_time_ms=0.0,
            page=request.page,
            page_size=request.page_size,
            total_pages=(total_count + request.page_size - 1) // request.page_size,
            key_insights=insights,
            recommended_actions=recommendations
        )
    
    async def _search_contracts_by_supplier_risk(
        self,
        request: CrossSystemSearchRequest,
        db: Session,
        organization_id: int
    ) -> CrossSystemSearchResponse:
        """Find contracts based on supplier risk levels."""
        
        # Query contracts with supplier risk information
        query = db.query(
            Document,
            Supplier
        ).join(
            Supplier,
            Document.extracted_metadata.op('->>')('supplier_name') == Supplier.name
        ).filter(
            Supplier.organization_id == organization_id
        )
        
        # Apply supplier risk filter
        if request.supplier_risk_level:
            query = query.filter(Supplier.risk_level == request.supplier_risk_level.upper())
        else:
            # Default to medium and high risk suppliers
            query = query.filter(Supplier.risk_level.in_(['MEDIUM', 'HIGH', 'CRITICAL']))
        
        # Apply pagination
        total_count = query.count()
        offset = (request.page - 1) * request.page_size
        results = query.offset(offset).limit(request.page_size).all()
        
        # Convert to contract results
        contract_results = []
        for document, supplier in results:
            # Extract contract metadata
            metadata = document.extracted_metadata or {}
            
            contract_results.append(ContractSupplierInfo(
                document_id=document.id,
                document_title=document.filename,
                contract_value=float(metadata.get('total_value', 0)) if metadata.get('total_value') else None,
                contract_start_date=self._parse_date(metadata.get('start_date')),
                contract_end_date=self._parse_date(metadata.get('end_date')),
                contract_status=metadata.get('status', 'unknown'),
                clause_risk_level=None,  # TODO: Get from clauses
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                supplier_risk_score=supplier.risk_score,
                supplier_risk_level=supplier.risk_level,
                combined_risk_score=supplier.risk_score,
                risk_explanation=f"Supplier has {supplier.risk_level.lower()} risk level",
                last_updated=document.updated_at
            ))
        
        # Generate insights
        avg_supplier_risk = sum(c.supplier_risk_score or 0 for c in contract_results) / len(contract_results) if contract_results else 0
        total_value = sum(c.contract_value or 0 for c in contract_results)
        
        insights = [
            f"Found {len(contract_results)} contracts with suppliers at {request.supplier_risk_level or 'medium+'} risk",
            f"Average supplier risk score: {avg_supplier_risk:.2f}",
            f"Total contract value at risk: ${total_value:,.2f}"
        ]
        
        recommendations = [
            "Review contracts with high-risk suppliers for additional protections",
            "Consider more frequent monitoring for high-risk supplier contracts"
        ]
        
        return CrossSystemSearchResponse(
            query_type=request.query_type,
            supplier_results=[],
            contract_results=contract_results,
            total_suppliers=len(set(c.supplier_id for c in contract_results if c.supplier_id)),
            total_contracts=len(contract_results),
            high_risk_count=len([c for c in contract_results if c.supplier_risk_level in ['HIGH', 'CRITICAL']]),
            expiring_soon_count=0,
            search_time_ms=0.0,
            page=request.page,
            page_size=request.page_size,
            total_pages=(total_count + request.page_size - 1) // request.page_size,
            key_insights=insights,
            recommended_actions=recommendations
        )
    
    async def _unified_risk_search(
        self,
        request: CrossSystemSearchRequest,
        db: Session,
        organization_id: int
    ) -> CrossSystemSearchResponse:
        """Perform a unified search combining supplier and contract risk factors."""
        
        # This is a comprehensive search that combines multiple risk factors
        # For now, we'll combine suppliers with risky contracts as the base
        risky_contracts_request = CrossSystemSearchRequest(
            query_type=CrossSystemQueryType.SUPPLIERS_WITH_RISKY_CONTRACTS,
            contract_risk_level=request.contract_risk_level,
            supplier_risk_level=request.supplier_risk_level,
            supplier_industries=request.supplier_industries,
            supplier_countries=request.supplier_countries,
            page=request.page,
            page_size=request.page_size
        )
        
        base_response = await self._search_suppliers_with_risky_contracts(
            risky_contracts_request, db, organization_id
        )
        
        # Enhance with additional risk factors
        enhanced_results = []
        for supplier_info in base_response.supplier_results:
            # Add additional risk factors
            additional_factors = []
            
            # Check for expiring contracts
            if supplier_info.expiring_contracts_count > 0:
                additional_factors.append(f"{supplier_info.expiring_contracts_count} contracts expiring soon")
            
            # Check for high contract concentration
            if supplier_info.total_contract_value and supplier_info.total_contract_value > 1000000:
                additional_factors.append("High contract value concentration")
            
            # Update risk factors
            supplier_info.risk_factors.extend(additional_factors)
            
            # Recalculate combined risk score
            supplier_info.combined_risk_score = self._calculate_unified_risk_score(supplier_info)
            
            enhanced_results.append(supplier_info)
        
        # Sort by combined risk score
        enhanced_results.sort(key=lambda x: x.combined_risk_score, reverse=True)
        
        # Update response
        base_response.supplier_results = enhanced_results
        base_response.query_type = CrossSystemQueryType.UNIFIED_RISK_SEARCH
        base_response.key_insights = [
            f"Unified risk analysis identified {len(enhanced_results)} suppliers requiring attention",
            f"Average combined risk score: {sum(s.combined_risk_score for s in enhanced_results) / len(enhanced_results):.2f}" if enhanced_results else "No results",
            f"Top risk factors: contract risk, supplier risk, expiring contracts"
        ]
        
        return base_response
    
    # Helper methods
    def _calculate_combined_risk_score(
        self,
        supplier_risk: float,
        contract_risk: Optional[str],
        contract_count: int,
        total_value: Optional[float]
    ) -> float:
        """Calculate a combined risk score from supplier and contract factors."""
        
        # Base score from supplier risk
        score = supplier_risk
        
        # Add contract risk factor
        if contract_risk:
            risk_multipliers = {
                'low': 1.0,
                'medium': 1.2,
                'high': 1.5,
                'critical': 2.0
            }
            score *= risk_multipliers.get(contract_risk, 1.0)
        
        # Add contract count factor (more contracts = higher exposure)
        if contract_count > 5:
            score *= 1.1
        if contract_count > 10:
            score *= 1.2
        
        # Add value factor (high value = higher impact)
        if total_value and total_value > 500000:
            score *= 1.1
        if total_value and total_value > 1000000:
            score *= 1.2
        
        return min(score, 10.0)  # Cap at 10.0
    
    def _calculate_expiry_risk_score(
        self,
        supplier_risk: float,
        expiring_count: int,
        total_value: Optional[float]
    ) -> float:
        """Calculate risk score based on contract expiry."""
        
        score = supplier_risk
        
        # Add expiry urgency factor
        score += (expiring_count * 0.5)
        
        # Add value impact
        if total_value and total_value > 100000:
            score += 1.0
        
        return min(score, 10.0)
    
    def _calculate_unified_risk_score(self, supplier_info: SupplierContractInfo) -> float:
        """Calculate a comprehensive unified risk score."""
        
        score = supplier_info.supplier_risk_score
        
        # Contract factors
        if supplier_info.highest_risk_contract_risk in ['high', 'critical']:
            score += 1.5
        
        # Expiry factor
        if supplier_info.expiring_contracts_count > 0:
            score += (supplier_info.expiring_contracts_count * 0.3)
        
        # Value concentration factor
        if supplier_info.total_contract_value and supplier_info.total_contract_value > 1000000:
            score += 1.0
        
        # Contract count factor
        if supplier_info.contract_count > 10:
            score += 0.5
        
        return min(score, 10.0)
    
    def _identify_risk_factors(
        self,
        supplier: Supplier,
        highest_risk: Optional[str],
        contract_count: int
    ) -> List[str]:
        """Identify risk factors for a supplier."""
        
        factors = []
        
        if supplier.risk_level in ['HIGH', 'CRITICAL']:
            factors.append(f"High supplier risk ({supplier.risk_level})")
        
        if highest_risk in ['high', 'critical']:
            factors.append(f"High-risk contract clauses ({highest_risk})")
        
        if contract_count > 10:
            factors.append(f"High contract volume ({contract_count} contracts)")
        
        if supplier.is_watchlisted:
            factors.append("Supplier on watchlist")
        
        return factors
    
    def _get_expiring_contracts_count(self, db: Session, supplier_name: str, days: int) -> int:
        """Get count of contracts expiring within specified days."""
        
        expiry_threshold = datetime.utcnow() + timedelta(days=days)
        
        count = db.query(func.count(Document.id)).filter(
            Document.extracted_metadata.op('->>')('supplier_name') == supplier_name,
            func.cast(Document.extracted_metadata.op('->>')('end_date'), func.DATE) <= expiry_threshold.date()
        ).scalar()
        
        return count or 0
    
    def _get_recent_contracts_count(self, db: Session, supplier_name: str, days: int) -> int:
        """Get count of contracts created within specified days."""
        
        recent_threshold = datetime.utcnow() - timedelta(days=days)
        
        count = db.query(func.count(Document.id)).filter(
            Document.extracted_metadata.op('->>')('supplier_name') == supplier_name,
            Document.created_at >= recent_threshold
        ).scalar()
        
        return count or 0
    
    def _get_supplier_total_contract_value(self, db: Session, supplier_name: str) -> Optional[float]:
        """Get total contract value for a supplier."""
        
        total = db.query(
            func.coalesce(func.sum(
                func.cast(Document.extracted_metadata.op('->>')('total_value'), func.numeric())
            ), 0)
        ).filter(
            Document.extracted_metadata.op('->>')('supplier_name') == supplier_name
        ).scalar()
        
        return float(total) if total else None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        
        if not date_str:
            return None
        
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    def _generate_risky_contracts_insights(
        self,
        results: List[SupplierContractInfo]
    ) -> tuple[List[str], List[str]]:
        """Generate insights and recommendations for risky contracts search."""
        
        if not results:
            return (["No suppliers with risky contracts found"], ["No actions needed"])
        
        # Calculate statistics
        avg_risk = sum(s.combined_risk_score for s in results) / len(results)
        high_risk_count = len([s for s in results if s.combined_risk_score >= 7.0])
        total_value = sum(s.total_contract_value or 0 for s in results)
        
        insights = [
            f"Found {len(results)} suppliers with risky contracts",
            f"Average combined risk score: {avg_risk:.2f}",
            f"{high_risk_count} suppliers require immediate attention (risk score ≥ 7.0)",
            f"Total contract value at risk: ${total_value:,.2f}"
        ]
        
        recommendations = [
            "Prioritize review of suppliers with risk score ≥ 7.0",
            "Consider additional contract protections for high-risk suppliers",
            "Schedule risk reassessment for all identified suppliers",
            "Evaluate backup supplier options for critical contracts"
        ]
        
        return insights, recommendations
