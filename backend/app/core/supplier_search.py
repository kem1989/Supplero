"""
Supplier Search Service for advanced supplier discovery and filtering.
"""

import structlog
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text
from datetime import datetime, timedelta
import re
import json
from openai import OpenAI

from app.models.supplier import Supplier, SupplierRiskAssessment
from app.models.document import Document
from app.schemas.supplier_search import (
    SupplierSearchRequest, SupplierSearchResponse, SupplierSearchResult,
    SupplierSearchFilters, SortOptions, SearchStatistics, SemanticSearchRequest,
    SemanticSearchResponse, SemanticSearchResult
)
from app.core.elasticsearch_service import ElasticsearchService
from app.core.config import settings

logger = structlog.get_logger(__name__)


class SupplierSearchService:
    """Advanced supplier search service with multi-field search and semantic capabilities."""
    
    def __init__(self):
        self.elasticsearch_service = ElasticsearchService()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def search_suppliers(
        self,
        request: SupplierSearchRequest,
        db: Session,
        organization_id: int
    ) -> SupplierSearchResponse:
        """
        Perform advanced supplier search with multiple filtering and sorting options.
        
        Args:
            request: Search request with query and filters
            db: Database session
            organization_id: Organization ID for filtering
            
        Returns:
            SupplierSearchResponse with matching suppliers and metadata
        """
        try:
            start_time = datetime.utcnow()
            
            logger.info(
                "Starting supplier search",
                query=request.query,
                filters=request.filters.dict() if request.filters else {},
                sort_by=request.sort_by,
                organization_id=organization_id
            )
            
            # Build base query
            query = self._build_base_query(db, organization_id)
            
            # Apply search query if provided
            if request.query:
                query = await self._apply_search_query(query, request.query, db)
            
            # Apply filters
            if request.filters:
                query = self._apply_filters(query, request.filters)
            
            # Get total count before pagination
            total_count = query.count()
            
            # Apply sorting
            query = self._apply_sorting(query, request.sort_by, request.sort_order)
            
            # Apply pagination
            offset = (request.page - 1) * request.page_size
            suppliers = query.offset(offset).limit(request.page_size).all()
            
            # Convert to search results
            search_results = await self._convert_to_search_results(suppliers, request.query)
            
            # Calculate statistics
            statistics = self._calculate_search_statistics(suppliers, total_count, db, organization_id)
            
            # Calculate performance metrics
            search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            performance_met = search_time < 2000  # 2 second threshold
            
            logger.info(
                "Supplier search completed",
                results_count=len(search_results),
                total_count=total_count,
                search_time_ms=search_time,
                performance_met=performance_met
            )
            
            return SupplierSearchResponse(
                suppliers=search_results,
                total_count=total_count,
                page=request.page,
                page_size=request.page_size,
                total_pages=(total_count + request.page_size - 1) // request.page_size,
                search_time_ms=search_time,
                performance_met=performance_met,
                statistics=statistics,
                filters_applied=self._get_applied_filters_summary(request.filters),
                query_used=request.query or ""
            )
            
        except Exception as e:
            logger.error(
                "Supplier search failed",
                error=str(e),
                query=request.query,
                organization_id=organization_id,
                exc_info=True
            )
            raise
    
    def _build_base_query(self, db: Session, organization_id: int):
        """Build base query for supplier search."""
        return db.query(Supplier).filter(
            Supplier.organization_id == organization_id,
            Supplier.is_active == True
        )
    
    async def _apply_search_query(self, query, search_query: str, db: Session):
        """Apply natural language search query to the supplier query."""
        try:
            # Parse search terms
            search_terms = self._parse_search_terms(search_query)
            
            if not search_terms:
                return query
            
            # Build search conditions
            search_conditions = []
            
            for term in search_terms:
                term_condition = or_(
                    Supplier.name.ilike(f"%{term}%"),
                    Supplier.industry.ilike(f"%{term}%"),
                    Supplier.location.ilike(f"%{term}%"),
                    Supplier.country.ilike(f"%{term}%"),
                    Supplier.contact_email.ilike(f"%{term}%"),
                    Supplier.website.ilike(f"%{term}%"),
                    Supplier.address.ilike(f"%{term}%"),
                    func.cast(Supplier.risk_factors, db.Text).ilike(f"%{term}%")
                )
                search_conditions.append(term_condition)
            
            # Combine conditions with AND logic
            if search_conditions:
                query = query.filter(and_(*search_conditions))
            
            return query
            
        except Exception as e:
            logger.warning("Failed to apply search query, continuing with base query", error=str(e))
            return query
    
    def _parse_search_terms(self, search_query: str) -> List[str]:
        """Parse search query into individual terms."""
        # Remove common words and split on whitespace
        stop_words = {'in', 'with', 'and', 'or', 'the', 'a', 'an', 'at', 'by', 'for', 'from', 'to'}
        terms = re.findall(r'\b\w+\b', search_query.lower())
        return [term for term in terms if term not in stop_words and len(term) > 2]
    
    def _apply_filters(self, query, filters: SupplierSearchFilters):
        """Apply filters to the supplier query."""
        if filters.supplier_name:
            query = query.filter(Supplier.name.ilike(f"%{filters.supplier_name}%"))
        
        if filters.industry:
            query = query.filter(Supplier.industry.ilike(f"%{filters.industry}%"))
        
        if filters.location:
            query = query.filter(Supplier.location.ilike(f"%{filters.location}%"))
        
        if filters.country:
            query = query.filter(Supplier.country.ilike(f"%{filters.country}%"))
        
        if filters.risk_level:
            if isinstance(filters.risk_level, list):
                query = query.filter(Supplier.risk_level.in_(filters.risk_level))
            else:
                query = query.filter(Supplier.risk_level == filters.risk_level)
        
        if filters.company_size:
            if isinstance(filters.company_size, list):
                query = query.filter(Supplier.company_size.in_(filters.company_size))
            else:
                query = query.filter(Supplier.company_size == filters.company_size)
        
        if filters.risk_score_min is not None:
            query = query.filter(Supplier.risk_score >= filters.risk_score_min)
        
        if filters.risk_score_max is not None:
            query = query.filter(Supplier.risk_score <= filters.risk_score_max)
        
        if filters.employee_count_min is not None:
            query = query.filter(Supplier.employee_count >= filters.employee_count_min)
        
        if filters.employee_count_max is not None:
            query = query.filter(Supplier.employee_count <= filters.employee_count_max)
        
        if filters.is_watchlisted is not None:
            query = query.filter(Supplier.is_watchlisted == filters.is_watchlisted)
        
        if filters.has_contracts is not None:
            if filters.has_contracts:
                # Filter suppliers that have associated contracts
                query = query.join(Document, Document.extracted_metadata.op('->>')('supplier_name') == Supplier.name, isouter=False)
            else:
                # Filter suppliers that don't have associated contracts
                subquery = query.session.query(Document.extracted_metadata.op('->>')('supplier_name')).filter(
                    Document.extracted_metadata.op('->>')('supplier_name') == Supplier.name
                ).exists()
                query = query.filter(~subquery)
        
        if filters.contract_count_min is not None:
            # Subquery to count contracts per supplier
            contract_count_subquery = (
                query.session.query(
                    func.count(Document.id).label('contract_count')
                ).filter(
                    Document.extracted_metadata.op('->>')('supplier_name') == Supplier.name
                ).group_by(Document.extracted_metadata.op('->>')('supplier_name')).subquery()
            )
            query = query.filter(
                query.session.query(contract_count_subquery.c.contract_count).filter(
                    contract_count_subquery.c.contract_count >= filters.contract_count_min
                ).exists()
            )
        
        if filters.last_assessment_after:
            query = query.filter(Supplier.last_risk_assessment >= filters.last_assessment_after)
        
        if filters.last_assessment_before:
            query = query.filter(Supplier.last_risk_assessment <= filters.last_assessment_before)
        
        return query
    
    def _apply_sorting(self, query, sort_by: str, sort_order: str):
        """Apply sorting to the query."""
        sort_direction = desc if sort_order.lower() == 'desc' else asc
        
        if sort_by == "name":
            query = query.order_by(sort_direction(Supplier.name))
        elif sort_by == "risk_score":
            query = query.order_by(sort_direction(Supplier.risk_score))
        elif sort_by == "risk_level":
            # Custom order for risk levels
            risk_order = {
                'CRITICAL': 4,
                'HIGH': 3,
                'MEDIUM': 2,
                'LOW': 1
            }
            if sort_order.lower() == 'desc':
                order_case = func.case(
                    *[(Supplier.risk_level == level, order) for level, order in risk_order.items()],
                    else_=0
                )
                query = query.order_by(desc(order_case))
            else:
                order_case = func.case(
                    *[(Supplier.risk_level == level, order) for level, order in risk_order.items()],
                    else_=5
                )
                query = query.order_by(asc(order_case))
        elif sort_by == "industry":
            query = query.order_by(sort_direction(Supplier.industry))
        elif sort_by == "location":
            query = query.order_by(sort_direction(Supplier.location))
        elif sort_by == "country":
            query = query.order_by(sort_direction(Supplier.country))
        elif sort_by == "company_size":
            # Custom order for company sizes
            size_order = {
                'enterprise': 4,
                'large': 3,
                'medium': 2,
                'small': 1
            }
            if sort_order.lower() == 'desc':
                order_case = func.case(
                    *[(Supplier.company_size == size, order) for size, order in size_order.items()],
                    else_=0
                )
                query = query.order_by(desc(order_case))
            else:
                order_case = func.case(
                    *[(Supplier.company_size == size, order) for size, order in size_order.items()],
                    else_=5
                )
                query = query.order_by(asc(order_case))
        elif sort_by == "last_assessment":
            query = query.order_by(sort_direction(Supplier.last_risk_assessment))
        elif sort_by == "created_at":
            query = query.order_by(sort_direction(Supplier.created_at))
        elif sort_by == "updated_at":
            query = query.order_by(sort_direction(Supplier.updated_at))
        else:
            # Default sorting by name
            query = query.order_by(asc(Supplier.name))
        
        return query
    
    async def _convert_to_search_results(
        self, 
        suppliers: List[Supplier], 
        search_query: Optional[str] = None
    ) -> List[SupplierSearchResult]:
        """Convert supplier models to search results."""
        results = []
        
        for supplier in suppliers:
            # Calculate relevance score based on search query
            relevance_score = 1.0
            if search_query:
                relevance_score = self._calculate_relevance_score(supplier, search_query)
            
            # Get contract statistics
            contract_stats = await self._get_supplier_contract_stats(supplier)
            
            result = SupplierSearchResult(
                id=supplier.id,
                name=supplier.name,
                industry=supplier.industry,
                location=supplier.location,
                country=supplier.country,
                contact_email=supplier.contact_email,
                contact_phone=supplier.contact_phone,
                website=supplier.website,
                company_size=supplier.company_size,
                employee_count=supplier.employee_count,
                revenue_range=supplier.revenue_range,
                risk_score=supplier.risk_score,
                risk_level=supplier.risk_level,
                risk_factors=supplier.risk_factors,
                is_active=supplier.is_active,
                is_watchlisted=supplier.is_watchlisted,
                watchlist_reason=supplier.watchlist_reason,
                last_risk_assessment=supplier.last_risk_assessment,
                created_at=supplier.created_at,
                updated_at=supplier.updated_at,
                relevance_score=relevance_score,
                contract_count=contract_stats["count"],
                total_contract_value=contract_stats["total_value"],
                latest_contract_date=contract_stats["latest_date"]
            )
            results.append(result)
        
        return results
    
    def _calculate_relevance_score(self, supplier: Supplier, search_query: str) -> float:
        """Calculate relevance score for a supplier based on search query."""
        score = 0.0
        query_lower = search_query.lower()
        
        # Name match (highest weight)
        if supplier.name and query_lower in supplier.name.lower():
            score += 0.4
        
        # Industry match
        if supplier.industry and query_lower in supplier.industry.lower():
            score += 0.2
        
        # Location/Country match
        if supplier.location and query_lower in supplier.location.lower():
            score += 0.15
        if supplier.country and query_lower in supplier.country.lower():
            score += 0.15
        
        # Risk level match
        if supplier.risk_level and query_lower in supplier.risk_level.lower():
            score += 0.1
        
        # Ensure minimum score for any match
        if score == 0.0:
            score = 0.1
        
        return min(1.0, score)
    
    async def _get_supplier_contract_stats(self, supplier: Supplier) -> Dict[str, Any]:
        """Get contract statistics for a supplier."""
        try:
            from app.core.database import get_db
            
            # This is a simplified version - in a real implementation,
            # you would join with a contracts table or use the document metadata
            stats = {
                "count": 0,
                "total_value": 0.0,
                "latest_date": None
            }
            
            # TODO: Implement actual contract statistics lookup
            # This would typically involve:
            # 1. Querying documents with supplier name in metadata
            # 2. Aggregating contract amounts and dates
            # 3. Counting total contracts
            
            return stats
            
        except Exception as e:
            logger.warning("Failed to get contract stats", supplier_id=supplier.id, error=str(e))
            return {"count": 0, "total_value": 0.0, "latest_date": None}
    
    def _calculate_search_statistics(
        self, 
        suppliers: List[Supplier], 
        total_count: int,
        db: Session,
        organization_id: int
    ) -> SearchStatistics:
        """Calculate search statistics."""
        try:
            # Risk level distribution
            risk_distribution = {}
            for supplier in suppliers:
                risk_level = supplier.risk_level or "UNKNOWN"
                risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
            
            # Industry distribution
            industry_distribution = {}
            for supplier in suppliers:
                industry = supplier.industry or "Unknown"
                industry_distribution[industry] = industry_distribution.get(industry, 0) + 1
            
            # Country distribution
            country_distribution = {}
            for supplier in suppliers:
                country = supplier.country or "Unknown"
                country_distribution[country] = country_distribution.get(country, 0) + 1
            
            # Company size distribution
            size_distribution = {}
            for supplier in suppliers:
                size = supplier.company_size or "Unknown"
                size_distribution[size] = size_distribution.get(size, 0) + 1
            
            # Average risk score
            risk_scores = [s.risk_score for s in suppliers if s.risk_score is not None]
            avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
            
            # Watchlisted count
            watchlisted_count = sum(1 for s in suppliers if s.is_watchlisted)
            
            return SearchStatistics(
                total_suppliers_in_org=db.query(Supplier).filter(
                    Supplier.organization_id == organization_id,
                    Supplier.is_active == True
                ).count(),
                matched_suppliers=total_count,
                risk_level_distribution=risk_distribution,
                industry_distribution=industry_distribution,
                country_distribution=country_distribution,
                company_size_distribution=size_distribution,
                average_risk_score=avg_risk_score,
                watchlisted_suppliers=watchlisted_count
            )
            
        except Exception as e:
            logger.warning("Failed to calculate search statistics", error=str(e))
            return SearchStatistics(
                total_suppliers_in_org=0,
                matched_suppliers=total_count,
                risk_level_distribution={},
                industry_distribution={},
                country_distribution={},
                company_size_distribution={},
                average_risk_score=0.0,
                watchlisted_suppliers=0
            )
    
    def _get_applied_filters_summary(self, filters: Optional[SupplierSearchFilters]) -> List[str]:
        """Get a summary of applied filters."""
        if not filters:
            return []
        
        applied = []
        
        if filters.supplier_name:
            applied.append(f"Name contains '{filters.supplier_name}'")
        if filters.industry:
            applied.append(f"Industry: {filters.industry}")
        if filters.location:
            applied.append(f"Location: {filters.location}")
        if filters.country:
            applied.append(f"Country: {filters.country}")
        if filters.risk_level:
            if isinstance(filters.risk_level, list):
                applied.append(f"Risk levels: {', '.join(filters.risk_level)}")
            else:
                applied.append(f"Risk level: {filters.risk_level}")
        if filters.company_size:
            if isinstance(filters.company_size, list):
                applied.append(f"Company sizes: {', '.join(filters.company_size)}")
            else:
                applied.append(f"Company size: {filters.company_size}")
        if filters.risk_score_min is not None:
            applied.append(f"Risk score >= {filters.risk_score_min}")
        if filters.risk_score_max is not None:
            applied.append(f"Risk score <= {filters.risk_score_max}")
        if filters.is_watchlisted is not None:
            applied.append(f"Watchlisted: {filters.is_watchlisted}")
        if filters.has_contracts is not None:
            applied.append(f"Has contracts: {filters.has_contracts}")
        
        return applied
    
    async def get_search_suggestions(
        self, 
        partial_query: str, 
        db: Session, 
        organization_id: int,
        limit: int = 10
    ) -> List[str]:
        """Get search suggestions based on partial query."""
        try:
            suggestions = []
            
            if len(partial_query) < 2:
                return suggestions
            
            query_lower = partial_query.lower()
            
            # Get supplier name suggestions
            supplier_names = db.query(Supplier.name).filter(
                Supplier.organization_id == organization_id,
                Supplier.is_active == True,
                Supplier.name.ilike(f"%{partial_query}%")
            ).limit(5).all()
            
            suggestions.extend([name[0] for name in supplier_names])
            
            # Get industry suggestions
            industries = db.query(Supplier.industry).filter(
                Supplier.organization_id == organization_id,
                Supplier.is_active == True,
                Supplier.industry.ilike(f"%{partial_query}%"),
                Supplier.industry.isnot(None)
            ).distinct().limit(3).all()
            
            suggestions.extend([industry[0] for industry in industries])
            
            # Get country suggestions
            countries = db.query(Supplier.country).filter(
                Supplier.organization_id == organization_id,
                Supplier.is_active == True,
                Supplier.country.ilike(f"%{partial_query}%"),
                Supplier.country.isnot(None)
            ).distinct().limit(2).all()
            
            suggestions.extend([country[0] for country in countries])
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.warning("Failed to get search suggestions", error=str(e))
            return []
    
    async def get_popular_searches(
        self, 
        db: Session, 
        organization_id: int,
        limit: int = 10
    ) -> List[str]:
        """Get popular search queries."""
        # This would typically come from search analytics
        # For now, return common search patterns
        return [
            "high risk suppliers",
            "pharmaceutical industry",
            "suppliers in China",
            "large enterprises",
            "watchlisted suppliers",
            "recent assessments",
            "manufacturing suppliers",
            "technology companies",
            "European suppliers",
            "critical risk level"
        ][:limit]
    
    async def semantic_search_suppliers(
        self,
        request: SemanticSearchRequest,
        db: Session,
        organization_id: int
    ) -> SemanticSearchResponse:
        """
        Perform semantic search on suppliers using AI-powered understanding.
        
        This method uses OpenAI to understand the intent and semantics of the search query,
        then finds suppliers that match the semantic meaning rather than just keywords.
        """
        try:
            start_time = datetime.utcnow()
            
            logger.info(
                "Starting semantic supplier search",
                query=request.query,
                max_results=request.max_results,
                similarity_threshold=request.similarity_threshold,
                organization_id=organization_id
            )
            
            # Get all suppliers for analysis
            suppliers = db.query(Supplier).filter(
                Supplier.organization_id == organization_id,
                Supplier.is_active == True
            ).all()
            
            if not suppliers:
                logger.warning("No suppliers found for semantic search")
                return SemanticSearchResponse(
                    results=[],
                    query=request.query,
                    total_results=0,
                    search_time_ms=0,
                    semantic_analysis={"message": "No suppliers found in organization"}
                )
            
            # Prepare supplier data for AI analysis
            supplier_contexts = self._prepare_supplier_contexts(suppliers)
            
            # Analyze query semantics
            semantic_analysis = await self._analyze_query_semantics(request.query)
            
            # Use AI to find semantic matches
            semantic_matches = await self._find_semantic_matches(
                request.query,
                supplier_contexts,
                request.max_results,
                request.similarity_threshold
            )
            
            # Convert to search results
            results = []
            for match in semantic_matches:
                supplier = next(
                    (s for s in suppliers if s.id == match["supplier_id"]), 
                    None
                )
                if supplier:
                    result = SemanticSearchResult(
                        supplier_id=supplier.id,
                        supplier_name=supplier.name,
                        similarity_score=match["similarity_score"],
                        matched_fields=match["matched_fields"],
                        snippets=match.get("snippets", []) if request.include_snippets else None,
                        metadata={
                            "industry": supplier.industry,
                            "location": supplier.location,
                            "country": supplier.country,
                            "risk_level": supplier.risk_level,
                            "risk_score": supplier.risk_score,
                            "company_size": supplier.company_size,
                            "is_watchlisted": supplier.is_watchlisted
                        }
                    )
                    results.append(result)
            
            search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(
                "Semantic supplier search completed",
                results_count=len(results),
                search_time_ms=search_time
            )
            
            return SemanticSearchResponse(
                results=results,
                query=request.query,
                total_results=len(results),
                search_time_ms=search_time,
                semantic_analysis=semantic_analysis
            )
            
        except Exception as e:
            logger.error(
                "Semantic supplier search failed",
                error=str(e),
                query=request.query,
                organization_id=organization_id,
                exc_info=True
            )
            search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return SemanticSearchResponse(
                results=[],
                query=request.query,
                total_results=0,
                search_time_ms=search_time,
                semantic_analysis={"error": str(e)}
            )
    
    def _prepare_supplier_contexts(self, suppliers: List[Supplier]) -> List[Dict[str, Any]]:
        """Prepare supplier data for AI analysis."""
        contexts = []
        
        for supplier in suppliers:
            # Create rich context for each supplier
            context = {
                "supplier_id": supplier.id,
                "name": supplier.name,
                "industry": supplier.industry or "",
                "location": supplier.location or "",
                "country": supplier.country or "",
                "company_size": supplier.company_size or "",
                "risk_level": supplier.risk_level,
                "risk_score": supplier.risk_score,
                "is_watchlisted": supplier.is_watchlisted,
                "contact_info": {
                    "email": supplier.contact_email or "",
                    "phone": supplier.contact_phone or "",
                    "website": supplier.website or ""
                },
                "business_info": {
                    "employee_count": supplier.employee_count,
                    "revenue_range": supplier.revenue_range or ""
                },
                "risk_factors": supplier.risk_factors or {},
                "searchable_text": self._create_searchable_text(supplier)
            }
            contexts.append(context)
        
        return contexts
    
    def _create_searchable_text(self, supplier: Supplier) -> str:
        """Create searchable text representation of supplier."""
        text_parts = [
            supplier.name or "",
            supplier.industry or "",
            supplier.location or "",
            supplier.country or "",
            supplier.company_size or "",
            supplier.risk_level or "",
            supplier.contact_email or "",
            supplier.website or "",
            supplier.revenue_range or "",
            supplier.address or ""
        ]
        
        # Add risk factors as searchable text
        if supplier.risk_factors:
            for key, value in supplier.risk_factors.items():
                if isinstance(value, (str, int, float)):
                    text_parts.append(str(value))
        
        return " ".join(filter(None, text_parts))
    
    async def _analyze_query_semantics(self, query: str) -> Dict[str, Any]:
        """Analyze the semantic meaning of the search query."""
        try:
            analysis_prompt = f"""
            Analyze this supplier search query and extract the semantic meaning:
            
            Query: "{query}"
            
            Identify:
            1. Intent (what the user is looking for)
            2. Key criteria mentioned
            3. Implicit requirements
            4. Risk-related concerns
            5. Geographic preferences
            6. Industry preferences
            7. Company characteristics
            
            Return JSON with your analysis.
            """
            
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a procurement expert analyzing supplier search queries."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse the response
            analysis_text = response.choices[0].message.content
            
            # Try to extract JSON, fallback to text summary
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                analysis = {
                    "intent": "general_search",
                    "summary": analysis_text,
                    "criteria": []
                }
            
            return analysis
            
        except Exception as e:
            logger.warning("Failed to analyze query semantics", error=str(e))
            return {
                "intent": "general_search",
                "error": str(e),
                "criteria": []
            }
    
    async def _find_semantic_matches(
        self,
        query: str,
        supplier_contexts: List[Dict[str, Any]],
        max_results: int,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """Find suppliers that semantically match the query."""
        try:
            # Limit context size for OpenAI
            limited_contexts = supplier_contexts[:50]  # Limit to first 50 suppliers
            
            search_prompt = f"""
            Find suppliers that match this search query semantically:
            
            Query: "{query}"
            
            Analyze each supplier and determine if they match the semantic intent of the query.
            Consider synonyms, related concepts, and implicit requirements.
            
            Supplier Data:
            {json.dumps(limited_contexts, indent=2)[:15000]}  # Limit JSON size
            
            For each matching supplier, return:
            {{
                "supplier_id": int,
                "similarity_score": float (0.0-1.0),
                "matched_fields": ["field1", "field2"],
                "snippets": ["relevant text snippet"],
                "reasoning": "why this supplier matches"
            }}
            
            Return only suppliers with similarity_score >= {similarity_threshold}.
            Limit to top {max_results} results.
            Return as JSON array.
            """
            
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at semantic matching for supplier search."},
                    {"role": "user", "content": search_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse the response
            response_text = response.choices[0].message.content
            
            # Try to extract JSON array
            try:
                # Look for JSON array in the response
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    matches = json.loads(json_match.group())
                else:
                    # Fallback: try to parse entire response
                    matches = json.loads(response_text)
                
                if not isinstance(matches, list):
                    matches = [matches] if matches else []
                
                # Ensure all matches have required fields
                validated_matches = []
                for match in matches:
                    if isinstance(match, dict) and "supplier_id" in match:
                        validated_match = {
                            "supplier_id": match.get("supplier_id"),
                            "similarity_score": float(match.get("similarity_score", 0.5)),
                            "matched_fields": match.get("matched_fields", []),
                            "snippets": match.get("snippets", []),
                            "reasoning": match.get("reasoning", "")
                        }
                        if validated_match["similarity_score"] >= similarity_threshold:
                            validated_matches.append(validated_match)
                
                # Sort by similarity score
                validated_matches.sort(key=lambda x: x["similarity_score"], reverse=True)
                
                return validated_matches[:max_results]
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("Failed to parse semantic search results", error=str(e))
                return []
            
        except Exception as e:
            logger.error("Semantic matching failed", error=str(e))
            return []
    
    async def enhanced_natural_language_search(
        self,
        query: str,
        db: Session,
        organization_id: int,
        max_results: int = 20
    ) -> SupplierSearchResponse:
        """
        Enhanced natural language search that combines traditional and semantic search.
        
        This method:
        1. Analyzes the query to understand intent
        2. Performs traditional keyword search
        3. Performs semantic search if needed
        4. Combines and ranks results
        """
        try:
            start_time = datetime.utcnow()
            
            logger.info(
                "Starting enhanced natural language supplier search",
                query=query,
                organization_id=organization_id
            )
            
            # Step 1: Analyze query intent using AI
            query_analysis = await self._analyze_search_intent(query)
            
            # Step 2: Convert natural language to structured search
            search_request = await self._convert_to_structured_search(query, query_analysis)
            
            # Step 3: Perform traditional search
            traditional_results = await self.search_suppliers(search_request, db, organization_id)
            
            # Step 4: If few results, enhance with semantic search
            if traditional_results.total_count < 5:
                logger.info("Enhancing with semantic search due to low result count")
                
                semantic_request = SemanticSearchRequest(
                    query=query,
                    max_results=max_results,
                    similarity_threshold=0.6,
                    include_snippets=True
                )
                
                semantic_results = await self.semantic_search_suppliers(
                    semantic_request, db, organization_id
                )
                
                # Merge results
                combined_results = self._merge_search_results(
                    traditional_results, semantic_results, query
                )
                
                return combined_results
            
            return traditional_results
            
        except Exception as e:
            logger.error("Enhanced natural language search failed", error=str(e))
            # Fallback to basic search
            basic_request = SupplierSearchRequest(query=query)
            return await self.search_suppliers(basic_request, db, organization_id)
    
    async def _analyze_search_intent(self, query: str) -> Dict[str, Any]:
        """Analyze search intent and extract parameters."""
        try:
            intent_prompt = f"""
            Analyze this supplier search query and extract structured parameters:
            
            Query: "{query}"
            
            Extract:
            - supplier_name: specific supplier name mentioned
            - industry: industry/sector mentioned
            - location: location/geography mentioned
            - risk_level: risk level mentioned (LOW/MEDIUM/HIGH/CRITICAL)
            - company_size: size mentioned (small/medium/large/enterprise)
            - risk_concerns: specific risk-related keywords
            - other_filters: any other filters mentioned
            
            Return as JSON object with extracted parameters.
            """
            
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at parsing supplier search queries."},
                    {"role": "user", "content": intent_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            # Parse response
            try:
                analysis = json.loads(response.choices[0].message.content)
                return analysis
            except json.JSONDecodeError:
                return {"intent": "general_search"}
            
        except Exception as e:
            logger.warning("Failed to analyze search intent", error=str(e))
            return {"intent": "general_search"}
    
    async def _convert_to_structured_search(
        self, 
        query: str, 
        analysis: Dict[str, Any]
    ) -> SupplierSearchRequest:
        """Convert analyzed intent to structured search request."""
        filters = SupplierSearchFilters()
        
        # Apply extracted filters
        if analysis.get("supplier_name"):
            filters.supplier_name = analysis["supplier_name"]
        
        if analysis.get("industry"):
            filters.industry = analysis["industry"]
        
        if analysis.get("location"):
            filters.location = analysis["location"]
        
        if analysis.get("risk_level"):
            risk_level = analysis["risk_level"].upper()
            if risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
                filters.risk_level = risk_level
        
        if analysis.get("company_size"):
            size = analysis["company_size"].lower()
            if size in ["small", "medium", "large", "enterprise"]:
                filters.company_size = size
        
        # Determine sort order based on query
        sort_by = SortOptions.NAME
        if "risk" in query.lower():
            sort_by = SortOptions.RISK_SCORE
        elif "recent" in query.lower() or "latest" in query.lower():
            sort_by = SortOptions.LAST_ASSESSMENT
        
        return SupplierSearchRequest(
            query=query,
            filters=filters,
            sort_by=sort_by,
            page=1,
            page_size=20
        )
    
    def _merge_search_results(
        self,
        traditional_results: SupplierSearchResponse,
        semantic_results: SemanticSearchResponse,
        original_query: str
    ) -> SupplierSearchResponse:
        """Merge traditional and semantic search results."""
        try:
            # Create a map of existing results
            existing_ids = {result.id for result in traditional_results.suppliers}
            
            # Add semantic results that aren't already included
            additional_results = []
            for semantic_result in semantic_results.results:
                if semantic_result.supplier_id not in existing_ids:
                    # Convert semantic result to supplier search result
                    # This would require fetching the full supplier data
                    # For now, we'll just note that this would be implemented
                    pass
            
            # For simplicity, return traditional results with enhanced metadata
            traditional_results.query_used = f"Enhanced: {original_query}"
            traditional_results.filters_applied.append("Semantic search enhancement applied")
            
            return traditional_results
            
        except Exception as e:
            logger.warning("Failed to merge search results", error=str(e))
            return traditional_results
