Based on analysis of your existing mature RAG system and robust supplier linking, this plan prioritizes the semantic search path to deliver immediate value for all target queries. The structured clause path becomes a future enhancement rather than a prerequisite.

Phase 1: Core Semantic Pipeline (Week 1-2)
1.1 Shared Semantic Service Extraction
File: backend/app/core/semantic_contract_search.py
pythonfrom typing import List, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session

@dataclass
class SemanticMatch:
    document_id: str
    supplier_id: Optional[str]
    supplier_name: Optional[str]
    relevance_score: float
    key_excerpts: List[str]
    match_reasons: List[str]
    document_filename: Optional[str] = None
    extracted_values: dict = None

class SemanticContractSearchService:
    """Shared service for semantic contract search across all handlers"""
    
    def __init__(self):
        self.min_relevance_threshold = 0.7
        self.max_excerpts_per_match = 3
    
    async def search_contracts_semantically(
        self, 
        query_text: str, 
        db: Session, 
        organization_id: str,
        max_results: int = 50
    ) -> List[SemanticMatch]:
        """
        Refactored from contract_handlers._direct_rag_semantic_search
        Returns semantic matches with supplier linking preserved
        """
        # Use existing RAG pipeline from contract_handlers
        raw_matches = await self._execute_rag_search(query_text, db, organization_id)
        
        # Transform to SemanticMatch format
        semantic_matches = []
        for match in raw_matches:
            if match.relevance_score >= self.min_relevance_threshold:
                semantic_match = SemanticMatch(
                    document_id=match.document_id,
                    supplier_id=self._extract_supplier_id(match),
                    supplier_name=self._extract_supplier_name(match),
                    relevance_score=match.relevance_score,
                    key_excerpts=match.excerpts[:self.max_excerpts_per_match],
                    match_reasons=self._generate_match_reasons(match, query_text),
                    document_filename=match.document_filename,
                    extracted_values=self._extract_numeric_values(match.text, query_text)
                )
                semantic_matches.append(semantic_match)
        
        return semantic_matches[:max_results]
    
    def _extract_supplier_id(self, match) -> Optional[str]:
        """Extract supplier_id from document metadata"""
        if hasattr(match, 'extracted_metadata') and match.extracted_metadata:
            return match.extracted_metadata.get('supplier_id')
        return None
    
    def _extract_supplier_name(self, match) -> Optional[str]:
        """Extract supplier_name from document metadata"""
        if hasattr(match, 'extracted_metadata') and match.extracted_metadata:
            return match.extracted_metadata.get('supplier_name')
        return None
    
    def _generate_match_reasons(self, match, query_text: str) -> List[str]:
        """Generate human-readable match reasons"""
        reasons = []
        
        # Analyze query terms found in excerpts
        query_terms = query_text.lower().split()
        for excerpt in match.excerpts:
            excerpt_lower = excerpt.lower()
            found_terms = [term for term in query_terms if term in excerpt_lower]
            if found_terms:
                reasons.append(f"Contains terms: {', '.join(found_terms)}")
        
        # Add semantic similarity reason
        if match.relevance_score > 0.85:
            reasons.append("High semantic similarity to query")
        elif match.relevance_score > 0.75:
            reasons.append("Good semantic similarity to query")
        
        return list(set(reasons))  # Remove duplicates
    
    def _extract_numeric_values(self, text: str, query_text: str) -> dict:
        """Extract numeric values relevant to query"""
        import re
        
        values = {}
        
        # Days extraction
        if any(term in query_text.lower() for term in ['days', 'termination', 'notice']):
            day_matches = re.findall(r'(\d+)\s*days?', text, re.IGNORECASE)
            if day_matches:
                values['days_found'] = [int(d) for d in day_matches]
        
        # Currency extraction  
        if any(term in query_text.lower() for term in ['liability', 'cap', '$', 'amount']):
            currency_matches = re.findall(r'\$([0-9,]+(?:\.[0-9]+)?)\s*([MmKkBb])?', text)
            if currency_matches:
                values['amounts_found'] = []
                for amount, unit in currency_matches:
                    base_amount = float(amount.replace(',', ''))
                    if unit and unit.lower() in ['m', 'million']:
                        base_amount *= 1_000_000
                    elif unit and unit.lower() in ['k', 'thousand']:
                        base_amount *= 1_000
                    elif unit and unit.lower() in ['b', 'billion']:
                        base_amount *= 1_000_000_000
                    values['amounts_found'].append(base_amount)
        
        return values
1.2 Enhanced Parameter Extraction
File: backend/app/ai_assistant_utils/parameter_extractor.py
python# Add to existing parameter extraction

import re
from typing import Dict, Any, Optional

class NumericParameterExtractor:
    """Extract numeric parameters from natural language queries"""
    
    PATTERNS = {
        'termination_days_min': [
            r'termination.{0,30}(?:longer than|more than|over|above)\s*(\d+)\s*days?',
            r'(?:longer than|more than|over|above)\s*(\d+)\s*days?.{0,30}termination',
            r'termination.{0,30}(\d+)\+\s*days?',
            r'notice.{0,20}(?:longer than|more than|over|above)\s*(\d+)\s*days?',
        ],
        'liability_cap_max_amount': [
            r'liability.{0,30}(?:under|below|less than|max)\s*\$?([0-9,]+(?:\.[0-9]+)?)\s*([MmKkBb])?',
            r'cap.{0,30}(?:under|below|less than|max)\s*\$?([0-9,]+(?:\.[0-9]+)?)\s*([MmKkBb])?',
            r'(?:under|below|less than)\s*\$([0-9,]+(?:\.[0-9]+)?)\s*([MmKkBb])?.{0,30}liability',
        ],
        'payment_terms_days_min': [
            r'payment.{0,30}(?:longer than|more than|over|above)\s*(?:net\s*)?(\d+)\s*days?',
            r'(?:longer than|more than|over|above)\s*net\s*(\d+)',
            r'terms.{0,30}(?:longer than|more than|over|above)\s*(\d+)\s*days?',
        ]
    }
    
    def extract_numeric_parameters(self, query: str) -> Dict[str, Any]:
        """Extract numeric parameters from query text"""
        parameters = {}
        
        for param_name, patterns in self.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    if param_name.endswith('_amount'):
                        # Handle currency conversion
                        amount = float(match.group(1).replace(',', ''))
                        unit = match.group(2) if len(match.groups()) > 1 else None
                        
                        if unit and unit.lower() in ['m']:
                            amount *= 1_000_000
                        elif unit and unit.lower() in ['k']:
                            amount *= 1_000
                        elif unit and unit.lower() in ['b']:
                            amount *= 1_000_000_000
                            
                        parameters[param_name] = amount
                    else:
                        # Handle days/numeric values
                        parameters[param_name] = int(match.group(1))
                    break  # Use first match
        
        return parameters

# Add to existing extract_parameters function
def extract_parameters(query: str, intent: str) -> Dict[str, Any]:
    """Enhanced parameter extraction with numeric handling"""
    
    # Existing parameter extraction logic...
    base_parameters = existing_extract_parameters(query, intent)
    
    # Add numeric parameter extraction
    numeric_extractor = NumericParameterExtractor()
    numeric_parameters = numeric_extractor.extract_numeric_parameters(query)
    
    # Merge parameters
    return {**base_parameters, **numeric_parameters}
1.3 New Cross-System Query Type
File: backend/app/core/cross_system_search.py
python# Add to existing CrossSystemQueryType enum
class CrossSystemQueryType(str, Enum):
    # ... existing types ...
    SUPPLIERS_BY_SEMANTIC_CONTRACTS = "suppliers_by_semantic_contracts"

# Add new search method
async def _search_suppliers_by_semantic_contracts(
    self, 
    request: CrossSystemSearchRequest, 
    db: Session, 
    org_id: str
) -> CrossSystemSearchResponse:
    """Search suppliers based on semantic contract analysis"""
    
    from backend.app.core.semantic_contract_search import SemanticContractSearchService
    
    # Initialize semantic search service
    semantic_service = SemanticContractSearchService()
    
    # Execute semantic search on contracts
    semantic_matches = await semantic_service.search_contracts_semantically(
        query_text=request.query_text,
        db=db,
        organization_id=org_id,
        max_results=100
    )
    
    # Group matches by supplier
    supplier_groups = {}
    unlinked_matches = []
    
    for match in semantic_matches:
        if match.supplier_id:
            # Direct supplier link available
            if match.supplier_id not in supplier_groups:
                supplier_groups[match.supplier_id] = {
                    "matches": [],
                    "best_score": 0,
                    "total_matches": 0,
                    "avg_score": 0
                }
            
            group = supplier_groups[match.supplier_id]
            group["matches"].append(match)
            group["best_score"] = max(group["best_score"], match.relevance_score)
            group["total_matches"] += 1
            
        elif match.supplier_name:
            # Try fuzzy matching to find supplier
            supplier = self._find_supplier_by_name_fuzzy(match.supplier_name, db, org_id)
            if supplier:
                supplier_id = str(supplier.id)
                if supplier_id not in supplier_groups:
                    supplier_groups[supplier_id] = {
                        "matches": [],
                        "best_score": 0,
                        "total_matches": 0,
                        "avg_score": 0
                    }
                
                group = supplier_groups[supplier_id]
                group["matches"].append(match)
                group["best_score"] = max(group["best_score"], match.relevance_score)
                group["total_matches"] += 1
            else:
                unlinked_matches.append(match)
        else:
            unlinked_matches.append(match)
    
    # Calculate average scores
    for group in supplier_groups.values():
        if group["total_matches"] > 0:
            group["avg_score"] = sum(m.relevance_score for m in group["matches"]) / group["total_matches"]
    
    # Build supplier results with contract insights
    supplier_results = []
    contract_results = []
    
    # Sort supplier groups by relevance (best score, then match count)
    sorted_supplier_groups = sorted(
        supplier_groups.items(),
        key=lambda x: (x[1]["best_score"], x[1]["total_matches"]),
        reverse=True
    )
    
    for supplier_id, group in sorted_supplier_groups[:50]:  # Limit results
        # Get supplier details
        supplier = db.query(Supplier).filter(
            Supplier.id == supplier_id,
            Supplier.organization_id == org_id
        ).first()
        
        if supplier:
            # Build contract insights for this supplier
            contract_insights = []
            for match in group["matches"][:5]:  # Top 5 matches per supplier
                contract_info = ContractSupplierInfo(
                    id=match.document_id,
                    filename=match.document_filename or f"Contract {match.document_id}",
                    contract_type="semantic_match",
                    key_excerpts=match.key_excerpts,
                    match_reasons=match.match_reasons,
                    relevance_score=match.relevance_score,
                    extracted_values=match.extracted_values
                )
                contract_insights.append(contract_info)
                contract_results.append(contract_info)
            
            # Build supplier result with contract insights
            supplier_contract_info = SupplierContractInfo(
                supplier=supplier,
                contract_count=group["total_matches"],
                total_contract_value=None,  # Not available from semantic search
                contracts=contract_insights,
                match_confidence=group["best_score"],
                semantic_insights={
                    "best_relevance_score": group["best_score"],
                    "average_relevance_score": group["avg_score"],
                    "total_semantic_matches": group["total_matches"],
                    "query_text": request.query_text
                }
            )
            supplier_results.append(supplier_contract_info)
    
    # Generate insights
    key_insights = self._generate_semantic_insights(
        supplier_groups, 
        unlinked_matches, 
        request.query_text
    )
    
    # Build statistics
    statistics = CrossSystemStatistics(
        total_suppliers=len(supplier_results),
        total_contracts=len(contract_results),
        suppliers_with_contracts=len(supplier_results),
        avg_contracts_per_supplier=sum(s.contract_count for s in supplier_results) / len(supplier_results) if supplier_results else 0,
        search_method="semantic_rag",
        processing_time_ms=None  # Set by calling handler
    )
    
    return CrossSystemSearchResponse(
        suppliers=supplier_results,
        contracts=contract_results,
        statistics=statistics,
        key_insights=key_insights,
        recommended_actions=self._generate_semantic_recommendations(supplier_results, request.query_text)
    )

def _generate_semantic_insights(
    self, 
    supplier_groups: dict, 
    unlinked_matches: list, 
    query_text: str
) -> List[str]:
    """Generate insights from semantic search results"""
    insights = []
    
    total_suppliers = len(supplier_groups)
    total_matches = sum(g["total_matches"] for g in supplier_groups.values())
    
    insights.append(f"Found {total_suppliers} suppliers with contracts matching '{query_text}'")
    insights.append(f"Total semantic matches: {total_matches}")
    
    if unlinked_matches:
        insights.append(f"Note: {len(unlinked_matches)} matches could not be linked to suppliers")
    
    # Analyze confidence distribution
    high_confidence = sum(1 for g in supplier_groups.values() if g["best_score"] > 0.85)
    medium_confidence = sum(1 for g in supplier_groups.values() if 0.75 <= g["best_score"] <= 0.85)
    
    if high_confidence:
        insights.append(f"{high_confidence} suppliers have high-confidence matches (>85%)")
    if medium_confidence:
        insights.append(f"{medium_confidence} suppliers have medium-confidence matches (75-85%)")
    
    return insights

def _generate_semantic_recommendations(
    self, 
    supplier_results: List[SupplierContractInfo], 
    query_text: str
) -> List[str]:
    """Generate actionable recommendations from semantic results"""
    recommendations = []
    
    if not supplier_results:
        recommendations.append("Try rephrasing your query or using different keywords")
        recommendations.append("Consider searching for related contract terms")
        return recommendations
    
    # High-confidence recommendations
    high_confidence_suppliers = [s for s in supplier_results if s.match_confidence > 0.85]
    if high_confidence_suppliers:
        recommendations.append(f"Review contracts from {len(high_confidence_suppliers)} high-confidence suppliers first")
    
    # Contract volume recommendations
    high_volume_suppliers = [s for s in supplier_results if s.contract_count > 3]
    if high_volume_suppliers:
        recommendations.append(f"{len(high_volume_suppliers)} suppliers have multiple matching contracts - consider bulk review")
    
    # Query-specific recommendations
    if any(term in query_text.lower() for term in ['force majeure', 'termination', 'liability']):
        recommendations.append("Consider legal review of identified clauses")
    
    if any(term in query_text.lower() for term in ['security', 'data', 'privacy']):
        recommendations.append("Schedule security compliance review with identified suppliers")
    
    return recommendations

# Add to main search method dispatcher
async def search(self, request: CrossSystemSearchRequest, db: Session, org_id: str) -> CrossSystemSearchResponse:
    """Enhanced search with semantic contracts support"""
    
    start_time = time.time()
    
    if request.query_type == CrossSystemQueryType.SUPPLIERS_BY_SEMANTIC_CONTRACTS:
        response = await self._search_suppliers_by_semantic_contracts(request, db, org_id)
    # ... existing query type handlers ...
    else:
        raise ValueError(f"Unsupported query type: {request.query_type}")
    
    # Set processing time
    response.statistics.processing_time_ms = int((time.time() - start_time) * 1000)
    
    return response
1.4 Handler Wiring
File: backend/app/api/v1/handlers/cross_system_handlers.py
python# Add new handler function
async def execute_suppliers_by_semantic_contracts(
    parameters: Dict[str, Any],
    db: Session,
    current_user,
    organization_id: str
) -> Dict[str, Any]:
    """Execute semantic contract search to find suppliers"""
    
    try:
        # Extract query text
        query_text = parameters.get("query", parameters.get("query_text", ""))
        if not query_text:
            return {
                "success": False,
                "message": "No query text provided for semantic search",
                "data": None
            }
        
        # Build cross-system request
        request = CrossSystemSearchRequest(
            query_type=CrossSystemQueryType.SUPPLIERS_BY_SEMANTIC_CONTRACTS,
            query_text=query_text,
            organization_id=organization_id,
            # Add numeric parameters if extracted
            filters={
                k: v for k, v in parameters.items() 
                if k.endswith(('_min', '_max', '_amount'))
            }
        )
        
        # Execute search
        search_service = CrossSystemSearchService()
        results = await search_service.search(request, db, organization_id)
        
        # Format response
        return {
            "success": True,
            "message": f"Found {results.statistics.total_suppliers} suppliers with matching contracts",
            "data": {
                "search_results": {
                    "suppliers": [
                        {
                            "id": str(s.supplier.id),
                            "name": s.supplier.name,
                            "email": s.supplier.email,
                            "phone": s.supplier.phone,
                            "address": s.supplier.address,
                            "contract_insights": {
                                "matching_contracts": [
                                    {
                                        "document_id": c.id,
                                        "filename": c.filename,
                                        "relevance_score": c.relevance_score,
                                        "key_excerpts": c.key_excerpts,
                                        "match_reasons": c.match_reasons,
                                        "clause_badges": self._generate_clause_badges(c, request.query_text),
                                        "extracted_values": c.extracted_values
                                    }
                                    for c in s.contracts[:3]  # Top 3 contracts per supplier
                                ],
                                "total_contracts": s.contract_count,
                                "confidence_score": s.match_confidence
                            }
                        }
                        for s in results.suppliers
                    ],
                    "contracts": [
                        {
                            "id": c.id,
                            "filename": c.filename,
                            "relevance_score": c.relevance_score,
                            "key_excerpts": c.key_excerpts,
                            "match_reasons": c.match_reasons
                        }
                        for c in results.contracts
                    ]
                },
                "statistics": {
                    "total_suppliers": results.statistics.total_suppliers,
                    "total_contracts": results.statistics.total_contracts,
                    "processing_time_ms": results.statistics.processing_time_ms,
                    "search_method": results.statistics.search_method
                },
                "key_insights": results.key_insights,
                "recommended_actions": results.recommended_actions,
                "query_processing": {
                    "original_query": query_text,
                    "extracted_parameters": parameters,
                    "search_method": "semantic_rag"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error in semantic contract search: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Error searching contracts: {str(e)}",
            "data": None
        }

def _generate_clause_badges(self, contract_info, query_text: str) -> List[str]:
    """Generate visual badges for contract clauses"""
    badges = []
    
    query_lower = query_text.lower()
    
    # Query-based badges
    if any(term in query_lower for term in ['force majeure', 'act of god']):
        badges.append("Force Majeure")
    
    if any(term in query_lower for term in ['termination', 'notice']):
        # Check for extracted days
        if contract_info.extracted_values and 'days_found' in contract_info.extracted_values:
            max_days = max(contract_info.extracted_values['days_found'])
            badges.append(f"Termination ({max_days} days)")
        else:
            badges.append("Termination Clause")
    
    if any(term in query_lower for term in ['liability', 'cap']):
        if contract_info.extracted_values and 'amounts_found' in contract_info.extracted_values:
            max_amount = max(contract_info.extracted_values['amounts_found'])
            if max_amount >= 1_000_000:
                badges.append(f"Liability Cap (${max_amount/1_000_000:.1f}M)")
            else:
                badges.append(f"Liability Cap (${max_amount:,.0f})")
        else:
            badges.append("Liability Cap")
    
    if any(term in query_lower for term in ['payment', 'net']):
        badges.append("Payment Terms")
    
    if any(term in query_lower for term in ['security', 'data', 'privacy']):
        badges.append("Data Security")
    
    # Confidence-based badge
    if contract_info.relevance_score > 0.9:
        badges.append("High Confidence")
    elif contract_info.relevance_score > 0.8:
        badges.append("Good Match")
    
    return badges
1.5 Intent Classification Enhancement
File: backend/app/ai_assistant_utils/intent_classifier.py
python# Add to existing intent definitions
INTENT_DEFINITIONS = {
    # ... existing intents ...
    
    "SUPPLIERS_BY_SEMANTIC_CONTRACTS": {
        "description": "Find suppliers based on semantic analysis of contract content",
        "keywords": [
            "suppliers with contracts containing",
            "vendors with clauses",
            "force majeure", "termination clauses", "liability caps",
            "payment terms", "data security requirements",
            "contracts mention", "contract terms",
            "longer than X days", "under $X", "more than net"
        ],
        "examples": [
            "Show me suppliers who have contracts with force majeure clauses",
            "Which vendors have termination clauses longer than 30 days?",
            "Find suppliers with liability caps under $1M",
            "Show me all suppliers with payment terms longer than Net 30",
            "Which contracts mention data security requirements?",
            "Suppliers with indemnification clauses",
            "Vendors with renewal terms"
        ],
        "required_parameters": ["query"],
        "optional_parameters": [
            "termination_days_min", "liability_cap_max_amount", 
            "payment_terms_days_min", "confidence_threshold"
        ]
    }
}

# Update classification logic
def classify_intent(query: str) -> Dict[str, Any]:
    """Enhanced intent classification with semantic contract support"""
    
    query_lower = query.lower()
    
    # Check for semantic contract search patterns
    semantic_contract_indicators = [
        # Supplier + contract content patterns
        ("suppliers" in query_lower or "vendors" in query_lower) and 
        any(term in query_lower for term in [
            "contracts", "clauses", "terms", "agreements",
            "force majeure", "termination", "liability", "payment", "security"
        ]),
        
        # Threshold/comparison patterns
        any(pattern in query_lower for pattern in [
            "longer than", "more than", "over", "above",
            "under", "below", "less than", "shorter than"
        ]) and any(term in query_lower for term in [
            "days", "dollars", "$", "net"
        ]),
        
        # Direct clause mentions with supplier context
        any(clause in query_lower for clause in [
            "force majeure", "termination clause", "liability cap",
            "payment terms", "data security", "indemnification"
        ]) and ("suppliers" in query_lower or "vendors" in query_lower)
    ]
    
    if any(semantic_contract_indicators):
        confidence = 0.9 if sum(semantic_contract_indicators) > 1 else 0.8
        return {
            "intent": "SUPPLIERS_BY_SEMANTIC_CONTRACTS",
            "confidence": confidence,
            "reasoning": "Query requests suppliers based on contract content analysis"
        }
    
    # Fall back to existing classification logic
    return existing_classify_intent(query)
1.6 AI Assistant Integration
File: backend/app/api/v1/ai_assistant.py
python# Add to handler mapping
INTENT_HANDLERS = {
    # ... existing handlers ...
    "SUPPLIERS_BY_SEMANTIC_CONTRACTS": cross_system_handlers.execute_suppliers_by_semantic_contracts,
}

# Update execute method (if needed - likely already handles new intents dynamically)