"""
AI Assistant service for natural language query processing and intent recognition.
Enhanced to handle complex clause-based queries using hybrid approach.
"""

import json
import re
import time
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from enum import Enum
import openai
from openai import OpenAI
import structlog

if TYPE_CHECKING:
    from app.models.document import Document

from app.core.config import settings
from app.core.logging import get_logger
from app.core.elasticsearch_service import ElasticsearchService

logger = get_logger(__name__)


class IntentType(str, Enum):
    """Supported intent types for natural language queries"""
    SEARCH_CONTRACTS = "SEARCH_CONTRACTS"
    SEARCH_CLAUSES = "SEARCH_CLAUSES"  # New: Complex clause-based queries
    ANALYZE_RISK = "ANALYZE_RISK"      # New: Risk analysis queries
    COMPARE_CLAUSES = "COMPARE_CLAUSES" # New: Clause comparison queries
    GET_DETAILS = "GET_DETAILS"
    EXPORT = "EXPORT"
    UNKNOWN = "UNKNOWN"


class ToolType(str, Enum):
    """Available tools for the AI assistant"""
    SEARCH_CONTRACTS = "SEARCH_CONTRACTS"
    SEARCH_CLAUSES = "SEARCH_CLAUSES"
    ANALYZE_RISK = "ANALYZE_RISK"
    COMPARE_CLAUSES = "COMPARE_CLAUSES"
    GET_DETAILS = "GET_DETAILS"
    EXPORT = "EXPORT"


class QueryIntent:
    """Represents the extracted intent and parameters from a natural language query"""
    
    def __init__(
        self,
        intent: IntentType,
        confidence: float,
        parameters: Dict[str, Any],
        raw_query: str
    ):
        self.intent = intent
        self.confidence = confidence
        self.parameters = parameters
        self.raw_query = raw_query
    
    def __str__(self) -> str:
        return f"Intent: {self.intent} (confidence: {self.confidence:.2f}) - Parameters: {self.parameters}"


class AIAssistantService:
    """Main service for AI-powered natural language query processing"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.tools = self._initialize_tools()
        self.elasticsearch_service = ElasticsearchService()
        
    def _initialize_tools(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the available tools registry"""
        return {
            ToolType.SEARCH_CONTRACTS: {
                "name": "SEARCH_CONTRACTS",
                "description": "Search for contracts based on various criteria like supplier, amount, date, contract type",
                "parameters": {
                    "supplier": "string - Supplier name or company",
                    "amount_min": "number - Minimum contract amount",
                    "amount_max": "number - Maximum contract amount", 
                    "date_from": "string - Start date (YYYY-MM-DD)",
                    "date_to": "string - End date (YYYY-MM-DD)",
                    "contract_type": "string - Type of contract (contract, invoice, etc.)",
                    "tags": "array - List of tags to filter by"
                },
                "examples": [
                    "Find contracts with supplier ABC Corp",
                    "Show contracts over $100,000 from last year",
                    "Get contracts with tag 'high-risk'"
                ]
            },
            ToolType.SEARCH_CLAUSES: {
                "name": "SEARCH_CLAUSES",
                "description": "Search for contracts based on specific clause content and characteristics",
                "parameters": {
                    "clause_types": "array - Types of clauses to search for (force_majeure, export_control, penalty, etc.)",
                    "clause_content": "string - Specific text or concepts to search for in clauses",
                    "clause_conditions": "object - Specific conditions within clauses (coverage, duration, amounts, etc.)",
                    "risk_factors": "array - Risk factors to consider (pandemic_coverage, restricted_countries, etc.)",
                    "supplier": "string - Supplier name to filter by",
                    "date_from": "string - Start date for contracts",
                    "date_to": "string - End date for contracts",
                    "exclude_patterns": "array - Patterns to exclude from results"
                },
                "examples": [
                    "Which contracts have force majeure clauses that don't cover pandemics?",
                    "Show contracts with export control clauses that don't cover the new restricted countries",
                    "Which agreements have penalty clauses that could trigger financial distress?"
                ]
            },
            ToolType.ANALYZE_RISK: {
                "name": "ANALYZE_RISK",
                "description": "Analyze contract risk based on clause analysis and external factors",
                "parameters": {
                    "risk_types": "array - Types of risk to analyze (financial, compliance, operational, etc.)",
                    "clause_analysis": "object - Specific clause analysis requirements",
                    "supplier_risk": "object - Supplier-specific risk factors",
                    "regulatory_changes": "array - Regulatory changes to consider",
                    "time_period": "string - Time period for analysis (last_2_years, etc.)"
                },
                "examples": [
                    "Which contracts signed in the last 2 years have clauses that are now considered outdated due to regulatory changes?",
                    "Find contracts with similar clause structures that have led to legal disputes in the past"
                ]
            },
            ToolType.COMPARE_CLAUSES: {
                "name": "COMPARE_CLAUSES",
                "description": "Compare clause structures and terms across multiple contracts",
                "parameters": {
                    "clause_type": "string - Type of clause to compare",
                    "comparison_criteria": "array - Criteria for comparison (duration, amounts, coverage, etc.)",
                    "contract_ids": "array - Specific contracts to compare",
                    "supplier_groups": "array - Groups of suppliers to compare",
                    "benchmark_standards": "array - Industry or internal standards to compare against"
                },
                "examples": [
                    "Compare force majeure clauses across our top 5 suppliers",
                    "Analyze penalty clause variations in contracts over $1M"
                ]
            },
            ToolType.GET_DETAILS: {
                "name": "GET_DETAILS", 
                "description": "Get detailed information about a specific contract or document",
                "parameters": {
                    "document_id": "string - Document ID to retrieve details for",
                    "include_metadata": "boolean - Whether to include extracted metadata",
                    "include_text": "boolean - Whether to include extracted text content",
                    "include_clauses": "boolean - Whether to include extracted clauses"
                },
                "examples": [
                    "Show me details for contract ABC-123",
                    "Get full details including text for document XYZ-456"
                ]
            },
            ToolType.EXPORT: {
                "name": "EXPORT",
                "description": "Export contract data in various formats",
                "parameters": {
                    "format": "string - Export format (csv, json, pdf)",
                    "filters": "object - Search filters to apply before export",
                    "columns": "array - Specific columns to include in export"
                },
                "examples": [
                    "Export all contracts to CSV",
                    "Export high-value contracts to PDF",
                    "Export supplier ABC contracts to JSON"
                ]
            }
        }
    
    async def process_query(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> QueryIntent:
        """
        Process a natural language query and extract intent and parameters.
        
        Args:
            query: Natural language query string
            user_context: Optional user context (organization, role, etc.)
            
        Returns:
            QueryIntent object with extracted intent and parameters
        """
        try:
            logger.info("Processing natural language query", query=query, user_context=user_context)
            
            # Use OpenAI to classify intent and extract parameters
            intent_result = await self._classify_intent(query)
            
            # Extract parameters based on the identified intent
            parameters = await self._extract_parameters(query, intent_result.intent)
            
            # Create QueryIntent object
            query_intent = QueryIntent(
                intent=intent_result.intent,
                confidence=intent_result.confidence,
                parameters=parameters,
                raw_query=query
            )
            
            logger.info(
                "Query processed successfully",
                intent=query_intent.intent,
                confidence=query_intent.confidence,
                parameters=query_intent.parameters
            )
            
            return query_intent
            
        except Exception as e:
            logger.error("Failed to process query", query=query, error=str(e))
            # Return unknown intent with low confidence
            return QueryIntent(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                parameters={},
                raw_query=query
            )
    
    async def _classify_intent(self, query: str) -> 'IntentClassificationResult':
        """
        Use OpenAI to classify the intent of a natural language query.
        
        Args:
            query: Natural language query string
            
        Returns:
            IntentClassificationResult with classified intent and confidence
        """
        try:
            # Prepare the prompt for intent classification
            system_prompt = self._build_intent_classification_prompt()
            
            response = await self._call_openai(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Classify this query: {query}"}
                ],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=200
            )
            
            # Parse the response
            intent_result = self._parse_intent_classification(response)
            
            return intent_result
            
        except Exception as e:
            logger.error("Intent classification failed", query=query, error=str(e))
            # Fallback to unknown intent
            return IntentClassificationResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0
            )
    
    def _build_intent_classification_prompt(self) -> str:
        """Build the system prompt for intent classification"""
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.tools.values()
        ])
        
        return f"""
You are an AI assistant that classifies natural language queries into specific intents for a contract management system.

Available intents:
{tools_description}

Your task is to classify the user's query into one of these intents with a confidence score (0.0 to 1.0).

**Key Classification Rules:**
1. **SEARCH_CLAUSES**: Use when query asks about specific clause content, coverage, or conditions
   - "Which contracts have force majeure clauses that don't cover pandemics?" → SEARCH_CLAUSES
   - "Show contracts with export control clauses" → SEARCH_CLAUSES
   - "Find contracts with penalty clauses over 20%" → SEARCH_CLAUSES

2. **ANALYZE_RISK**: Use when query asks about risk analysis, outdated clauses, or legal disputes
   - "Which contracts have clauses that are now outdated?" → ANALYZE_RISK
   - "Find contracts with similar clauses that led to disputes" → ANALYZE_RISK

3. **COMPARE_CLAUSES**: Use when query asks to compare clauses across contracts or suppliers
   - "Compare force majeure clauses across suppliers" → COMPARE_CLAUSES

4. **SEARCH_CONTRACTS**: Use for basic contract searches (supplier, amount, date, tags)
   - "Find contracts with supplier ABC Corp" → SEARCH_CONTRACTS

Respond in this exact JSON format:
{{
    "intent": "INTENT_NAME",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this intent was chosen"
}}

Be precise and only use the exact intent names shown above.
"""
    
    def _parse_intent_classification(self, openai_response: str) -> 'IntentClassificationResult':
        """Parse OpenAI response to extract intent and confidence"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', openai_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                intent_name = result.get("intent", "UNKNOWN")
                confidence = float(result.get("confidence", 0.0))
                
                # Validate intent name
                try:
                    intent = IntentType(intent_name)
                except ValueError:
                    intent = IntentType.UNKNOWN
                    confidence = 0.0
                
                return IntentClassificationResult(
                    intent=intent,
                    confidence=confidence
                )
            else:
                # Fallback parsing
                return self._fallback_intent_parsing(openai_response)
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse OpenAI response", response=openai_response, error=str(e))
            return self._fallback_intent_parsing(openai_response)
    
    def _fallback_intent_parsing(self, response: str) -> 'IntentClassificationResult':
        """Fallback intent parsing using keyword matching"""
        response_lower = response.lower()
        
        # Keyword-based intent detection
        if any(word in response_lower for word in ["search", "find", "show", "get", "list", "contract"]):
            return IntentClassificationResult(IntentType.SEARCH_CONTRACTS, 0.7)
        elif any(word in response_lower for word in ["details", "info", "information", "specific"]):
            return IntentClassificationResult(IntentType.GET_DETAILS, 0.7)
        elif any(word in response_lower for word in ["export", "download", "csv", "pdf", "json"]):
            return IntentClassificationResult(IntentType.EXPORT, 0.7)
        else:
            return IntentClassificationResult(IntentType.UNKNOWN, 0.3)
    
    async def _extract_parameters(self, query: str, intent: IntentType) -> Dict[str, Any]:
        """
        Extract parameters from the query based on the identified intent.
        
        Args:
            query: Natural language query string
            intent: Identified intent type
            
        Returns:
            Dictionary of extracted parameters
        """
        try:
            if intent == IntentType.UNKNOWN:
                return {}
            
            # Build parameter extraction prompt
            system_prompt = self._build_parameter_extraction_prompt(intent)
            
            response = await self._call_openai(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract parameters from: {query}"}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            # Parse parameters
            parameters = self._parse_parameters(response, intent)
            
            return parameters
            
        except Exception as e:
            logger.error("Parameter extraction failed", query=query, intent=intent, error=str(e))
            return {}
    
    def _build_parameter_extraction_prompt(self, intent: IntentType) -> str:
        """Build the system prompt for parameter extraction"""
        tool = self.tools.get(intent.value, {})
        parameters = tool.get("parameters", {})
        
        param_desc = "\n".join([
            f"- {key}: {desc}"
            for key, desc in parameters.items()
        ])
        
        return f"""
You are an AI assistant that extracts structured parameters from natural language queries.

Intent: {intent.value}
Tool: {tool.get('name', 'Unknown')}

Required parameters:
{param_desc}

**Special Instructions for Complex Queries:**

For SEARCH_CLAUSES intent:
- Extract clause types mentioned (force_majeure, export_control, penalty, etc.)
- Identify specific conditions (coverage, duration, amounts, percentages)
- Look for exclusion patterns (don't cover, doesn't include, etc.)
- Extract risk factors mentioned (pandemics, restricted countries, etc.)

For ANALYZE_RISK intent:
- Identify risk types (financial, compliance, operational)
- Extract time periods (last 2 years, recent, etc.)
- Look for regulatory context or legal dispute references

For COMPARE_CLAUSES intent:
- Extract clause types to compare
- Identify comparison criteria (duration, amounts, coverage)
- Extract supplier groups or contract sets to compare

Extract parameters from the user's query and respond in this exact JSON format:
{{
    "parameters": {{
        "param1": "value1",
        "param2": "value2"
    }}
}}

Only include parameters that are explicitly mentioned or can be reasonably inferred.
Use null for missing parameters.
"""
    
    def _parse_parameters(self, response: str, intent: IntentType) -> Dict[str, Any]:
        """Parse OpenAI response to extract parameters"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("parameters", {})
            else:
                return {}
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse parameters", response=response, error=str(e))
            return {}
    
    async def _call_openai(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Make a call to OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI API call failed", error=str(e))
            raise
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available tools"""
        return self.tools
    
    async def search_contracts(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "relevance"
    ) -> Dict[str, Any]:
        """
        Search contracts using the Elasticsearch service
        
        Args:
            query: Text query for semantic search
            filters: Search filters (supplier, amount, date, etc.)
            page: Page number for pagination
            page_size: Number of results per page
            sort_by: Sort method (relevance, date, amount)
            
        Returns:
            Dictionary containing search results and performance metrics
        """
        try:
            logger.info(
                "Executing contract search via AI assistant",
                query=query,
                filters=filters,
                page=page,
                page_size=page_size
            )
            
            # Use Elasticsearch service for fast search
            search_result = await self.elasticsearch_service.search_contracts(
                query=query,
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by=sort_by
            )
            
            # Convert to dictionary format
            result = search_result.to_dict()
            
            # **UNIVERSAL RAG FALLBACK**: If Elasticsearch returns 0 results, use RAG
            # Use the original raw query if available, or construct from filters
            fallback_query = query or self._construct_query_from_filters(filters)
            if result["total_count"] == 0 and fallback_query:
                logger.info(
                    "Elasticsearch returned 0 results, falling back to RAG semantic search",
                    original_query=query,
                    filters=filters
                )
                
                # Use RAG for semantic search
                rag_result = await self._rag_semantic_search(fallback_query, filters, page_size)
                if rag_result and rag_result.get("documents"):
                    result.update(rag_result)
                    result["search_strategy"] = "RAG_FALLBACK"
                    result["fallback_reason"] = "Elasticsearch returned 0 results"
                    
                    logger.info(
                        "RAG fallback successful",
                        results_count=len(result["documents"]),
                        search_strategy="RAG_FALLBACK"
                    )
            
            # Add AI-generated insights if query is provided
            if query and result["documents"]:
                result["ai_insights"] = await self._generate_search_insights(
                    query, result["documents"]
                )
            
            logger.info(
                "Contract search completed successfully",
                results_count=len(result["documents"]),
                search_time_ms=result["search_time_ms"],
                performance_met=result["performance_met"],
                search_strategy=result.get("search_strategy", "ELASTICSEARCH")
            )
            
            return result
            
        except Exception as e:
            logger.error("Contract search failed in AI assistant", error=str(e))
            return {
                "documents": [],
                "total_count": 0,
                "search_time_ms": 0,
                "query": query or "",
                "filters_applied": filters or {},
                "error": str(e),
                "performance_met": False
            }
    
    async def search_clauses(
        self,
        clause_types: List[str],
        clause_content: Optional[str] = None,
        clause_conditions: Optional[Dict[str, Any]] = None,
        risk_factors: Optional[List[str]] = None,
        raw_query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Search for contracts based on specific clause content and characteristics
        
        Args:
            clause_types: Types of clauses to search for
            clause_content: Specific text or concepts to search for
            clause_conditions: Specific conditions within clauses
            risk_factors: Risk factors to consider
            filters: Additional search filters
            page: Page number for pagination
            page_size: Number of results per page
            
        Returns:
            Dictionary containing clause search results and analysis
        """
        try:
            logger.info(
                "Executing clause-based search",
                clause_types=clause_types,
                clause_content=clause_content,
                risk_factors=risk_factors
            )
            
            # Build hybrid search query combining Elasticsearch and RAG
            search_result = await self._hybrid_clause_search(
                clause_types=clause_types,
                clause_content=clause_content,
                clause_conditions=clause_conditions,
                risk_factors=risk_factors,
                raw_query=raw_query,
                filters=filters,
                page=page,
                page_size=page_size
            )
            
            return search_result
            
        except Exception as e:
            logger.error("Clause search failed", error=str(e))
            return {
                "documents": [],
                "total_count": 0,
                "search_time_ms": 0,
                "clause_analysis": {},
                "risk_assessment": {},
                "error": str(e)
            }
    
    async def analyze_risk(
        self,
        risk_types: List[str],
        clause_analysis: Optional[Dict[str, Any]] = None,
        supplier_risk: Optional[Dict[str, Any]] = None,
        regulatory_changes: Optional[List[str]] = None,
        time_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze contract risk based on clause analysis and external factors
        
        Args:
            risk_types: Types of risk to analyze
            clause_analysis: Specific clause analysis requirements
            supplier_risk: Supplier-specific risk factors
            regulatory_changes: Regulatory changes to consider
            time_period: Time period for analysis
            
        Returns:
            Dictionary containing risk analysis results
        """
        try:
            logger.info(
                "Executing risk analysis",
                risk_types=risk_types,
                time_period=time_period
            )
            
            # Perform comprehensive risk analysis
            risk_result = await self._comprehensive_risk_analysis(
                risk_types=risk_types,
                clause_analysis=clause_analysis,
                supplier_risk=supplier_risk,
                regulatory_changes=regulatory_changes,
                time_period=time_period
            )
            
            return risk_result
            
        except Exception as e:
            logger.error("Risk analysis failed", error=str(e))
            return {
                "risk_assessment": {},
                "clause_analysis": {},
                "recommendations": [],
                "error": str(e)
            }
    
    async def compare_clauses(
        self,
        clause_type: str,
        comparison_criteria: List[str],
        contract_ids: Optional[List[str]] = None,
        supplier_groups: Optional[List[str]] = None,
        benchmark_standards: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare clause structures and terms across multiple contracts
        
        Args:
            clause_type: Type of clause to compare
            comparison_criteria: Criteria for comparison
            contract_ids: Specific contracts to compare
            supplier_groups: Groups of suppliers to compare
            benchmark_standards: Industry or internal standards
            
        Returns:
            Dictionary containing clause comparison results
        """
        try:
            logger.info(
                "Executing clause comparison",
                clause_type=clause_type,
                comparison_criteria=comparison_criteria
            )
            
            # Perform clause comparison analysis
            comparison_result = await self._clause_comparison_analysis(
                clause_type=clause_type,
                comparison_criteria=comparison_criteria,
                contract_ids=contract_ids,
                supplier_groups=supplier_groups,
                benchmark_standards=benchmark_standards
            )
            
            return comparison_result
            
        except Exception as e:
            logger.error("Clause comparison failed", error=str(e))
            return {
                "comparison_results": {},
                "benchmark_analysis": {},
                "recommendations": [],
                "error": str(e)
            }
    
    async def _generate_search_insights(
        self, 
        query: str, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI insights for search results"""
        try:
            # Prepare context for OpenAI
            context = f"""
            Query: {query}
            Found {len(documents)} contracts.
            
            Top results:
            {chr(10).join([f"- {doc.get('supplier_name', 'Unknown')}: ${doc.get('contract_amount', 0):,.0f} ({doc.get('contract_type', 'contract')})" for doc in documents[:5]])}
            """
            
            response = await self._call_openai(
                messages=[
                    {"role": "system", "content": "You are a procurement expert. Provide brief insights about the search results."},
                    {"role": "user", "content": f"Analyze these contract search results and provide 2-3 key insights: {context}"}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            return {
                "summary": response.strip(),
                "total_contracts": len(documents),
                "total_value": sum(doc.get("contract_amount", 0) for doc in documents if doc.get("contract_amount")),
                "suppliers_count": len(set(doc.get("supplier_name") for doc in documents if doc.get("supplier_name")))
            }
            
        except Exception as e:
            logger.warning("Failed to generate search insights", error=str(e))
            return {
                "summary": "Unable to generate insights at this time.",
                "total_contracts": len(documents),
                "total_value": 0,
                "suppliers_count": 0
            }
    
    async def _hybrid_clause_search(
        self,
        clause_types: List[str],
        clause_content: Optional[str] = None,
        clause_conditions: Optional[Dict[str, Any]] = None,
        risk_factors: Optional[List[str]] = None,
        raw_query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Hybrid search combining Elasticsearch with RAG for clause-based queries
        
        This method implements a two-phase search:
        1. Fast Elasticsearch search for initial contract filtering
        2. RAG-based analysis for complex clause content understanding
        """
        start_time = time.time()
        
        try:
            # Phase 1: Try clause-specific Elasticsearch search first
            es_filters = self._build_clause_search_filters(
                clause_types, clause_content, filters
            )
            
            try:
                # Try the clause-specific search first
                # Always include the user's raw natural language query for semantic matching
                _es_query = clause_content or raw_query or ""
                es_results = await self.elasticsearch_service.search_contracts(
                    query=_es_query,
                    filters=es_filters,
                    page=page,
                    page_size=page_size,
                    sort_by="relevance"
                )
                
                if es_results.documents:
                    logger.info("Elasticsearch clause search successful", results_count=len(es_results.documents))
                    search_strategy = "elasticsearch_clause_search"
                else:
                    logger.info("Elasticsearch clause search returned no results, falling back to RAG")
                    search_strategy = "rag_fallback"
                    
            except Exception as es_error:
                logger.warning("Elasticsearch clause search failed, falling back to RAG", error=str(es_error))
                es_results = type('MockResults', (), {
                    'documents': [],
                    'total_count': 0
                })()
                search_strategy = "rag_fallback"
            
            # Phase 2: RAG-based clause analysis (always run for comprehensive results)
            if es_results.documents:
                # Analyze the documents found by Elasticsearch
                clause_analysis = await self._analyze_clauses_with_rag(
                    documents=es_results.documents,
                    clause_types=clause_types,
                    clause_conditions=clause_conditions,
                    risk_factors=risk_factors
                )
            else:
                # No Elasticsearch results - use RAG to search through all available documents
                logger.info("Using RAG to search through available documents")
                clause_analysis = await self._rag_search_through_documents(
                    clause_types=clause_types,
                    clause_conditions=clause_conditions,
                    risk_factors=risk_factors,
                    filters=filters,
                    raw_query=raw_query
                )
                
                # Extract documents from RAG results
                if clause_analysis.get('matching_documents'):
                    es_results.documents = clause_analysis['matching_documents']
                    es_results.total_count = len(clause_analysis['matching_documents'])
                else:
                    es_results.documents = []
                    es_results.total_count = 0
            
            search_time = (time.time() - start_time) * 1000
            
            return {
                "documents": es_results.documents,
                "total_count": es_results.total_count,
                "search_time_ms": search_time,
                "clause_analysis": clause_analysis,
                "risk_assessment": await self._assess_clause_risks(
                    clause_analysis, risk_factors
                ),
                "search_strategy": search_strategy,
                "performance_met": search_time < 2000  # 2s threshold for complex queries
            }
            
        except Exception as e:
            search_time = (time.time() - start_time) * 1000
            logger.error("Hybrid clause search failed", error=str(e))
            return {
                "documents": [],
                "total_count": 0,
                "search_time_ms": search_time,
                "clause_analysis": {},
                "risk_assessment": {},
                "error": str(e)
            }
    
    def _build_clause_search_filters(
        self,
        clause_types: List[str],
        clause_content: Optional[str] = None,
        base_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build Elasticsearch filters for clause-based search"""
        filters = base_filters or {}
        
        # Add clause type filters
        if clause_types:
            filters["clause_types"] = clause_types
        
        # Add semantic content filters
        if clause_content:
            filters["semantic_content"] = clause_content
        
        return filters
    
    async def _analyze_clauses_with_rag(
        self,
        documents: List[Dict[str, Any]],
        clause_types: List[str],
        clause_conditions: Optional[Dict[str, Any]] = None,
        risk_factors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Use RAG (Retrieval-Augmented Generation) to analyze clauses in documents
        
        This method combines document content with AI analysis to understand
        complex clause structures and conditions
        """
        try:
            # Prepare context for OpenAI analysis
            context = self._prepare_clause_analysis_context(
                documents, clause_types, clause_conditions, risk_factors
            )
            
            # Use OpenAI for clause analysis
            analysis_prompt = self._build_clause_analysis_prompt(
                clause_types, clause_conditions, risk_factors
            )
            
            response = await self._call_openai(
                messages=[
                    {"role": "system", "content": analysis_prompt},
                    {"role": "user", "content": f"Analyze these contracts for the specified clauses: {context}"}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse the analysis response
            return self._parse_clause_analysis(response)
            
        except Exception as e:
            logger.error("RAG clause analysis failed", error=str(e))
            return {
                "clause_findings": [],
                "risk_indicators": [],
                "compliance_gaps": [],
                "recommendations": []
            }
    
    def _prepare_clause_analysis_context(
        self,
        documents: List[Dict[str, Any]],
        clause_types: List[str],
        clause_conditions: Optional[Dict[str, Any]] = None,
        risk_factors: Optional[List[str]] = None
    ) -> str:
        """Prepare context for clause analysis"""
        context_parts = [
            f"Analyzing {len(documents)} contracts for {', '.join(clause_types)} clauses."
        ]
        
        if clause_conditions:
            context_parts.append(f"Specific conditions: {clause_conditions}")
        
        if risk_factors:
            context_parts.append(f"Risk factors to consider: {', '.join(risk_factors)}")
        
        # Add document summaries
        doc_summaries = []
        for doc in documents[:5]:  # Limit to top 5 for context
            summary = f"- {doc.get('supplier_name', 'Unknown')}: {doc.get('contract_amount', 0)} USD"
            if doc.get('extracted_text'):
                summary += f" (Text length: {len(doc['extracted_text'])} chars)"
            doc_summaries.append(summary)
        
        context_parts.append("Document summaries:\n" + "\n".join(doc_summaries))
        
        return "\n".join(context_parts)
    
    async def _rag_search_through_documents(
        self,
        clause_types: List[str],
        clause_conditions: Optional[Dict[str, Any]] = None,
        risk_factors: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        raw_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use RAG to search through all available documents when Elasticsearch fails
        
        This method implements intelligent document search using AI analysis
        """
        try:
            logger.info("Starting RAG-based document search", clause_types=clause_types)
            
            # Get all available documents from the database
            from app.core.database import get_db
            from app.models.document import Document
            
            db = next(get_db())
            documents = db.query(Document).filter(
                Document.organization_id == filters.get('organization_id', 1)  # Default org
            ).limit(100).all()  # Limit to prevent memory issues
            
            logger.info(f"Found {len(documents)} documents for RAG analysis")
            
            if not documents:
                return {
                    "clause_findings": [],
                    "risk_indicators": [],
                    "compliance_gaps": [],
                    "recommendations": [],
                    "matching_documents": []
                }
            
            # Prepare context for RAG analysis
            context = self._prepare_rag_search_context(
                documents, clause_types, clause_conditions, risk_factors, raw_query
            )
            
            # Build RAG search prompt
            rag_prompt = self._build_rag_search_prompt(
                clause_types, clause_conditions, risk_factors, raw_query
            )
            
            logger.info("RAG prompt prepared", prompt_length=len(rag_prompt), context_length=len(context))
            
            # Use OpenAI for RAG search
            response = await self._call_openai(
                messages=[
                    {"role": "system", "content": rag_prompt},
                    {"role": "user", "content": f"Search through these documents for the specified clauses: {context}"}
                ],
                temperature=0.1,
                max_tokens=2000  # Increased for more detailed analysis
            )
            
            logger.info("OpenAI RAG response received", response_length=len(response), response_preview=response[:200])
            
            # Parse RAG results
            rag_results = self._parse_rag_search_results(response, documents)

            # Deterministic fallback: if no matching documents were returned by RAG,
            # perform a simple boolean keyword scan using the user's natural language query.
            if (not rag_results.get("matching_documents")) and raw_query:
                required_terms = self._extract_required_terms_from_query(raw_query)
                if required_terms:
                    matching_docs = []
                    for doc in documents:
                        text = (doc.extracted_text or "").lower()
                        if all(any(term in text for term in term_group) for term_group in required_terms):
                            matching_docs.append({
                                'document_id': doc.id,
                                'filename': doc.filename,
                                'supplier_name': doc.extracted_metadata.get('supplier_name') if doc.extracted_metadata else None,
                                'contract_amount': doc.extracted_metadata.get('contract_amount') if doc.extracted_metadata else None,
                                'extracted_text': doc.extracted_text,
                                'relevance_score': 0.9
                            })
                    rag_results["matching_documents"] = matching_docs
            
            return rag_results
            
        except Exception as e:
            logger.error("RAG document search failed", error=str(e))
            return {
                "clause_findings": [],
                "risk_indicators": [],
                "compliance_gaps": [],
                "recommendations": [],
                "matching_documents": []
            }

    def _extract_required_terms_from_query(self, raw_query: str) -> List[List[str]]:
        """Extract groups of synonymous required terms with AND semantics from the natural language query.

        Returns a list of term groups. Each inner list represents a synonym set (OR),
        and all groups must be satisfied (AND across groups).
        This is a lightweight heuristic to ensure robust baseline matching without model reliance.
        """
        q = raw_query.lower()
        groups: List[List[str]] = []

        # Common legal/commercial concepts and synonyms
        concepts = {
            'iso_9001': ["iso 9001", "iso-9001", "iso9001", "quality management", "quality management system"],
            'force_majeure': ["force majeure", "act of god", "unforeseen circumstances"],
            'warranty': ["warranty", "warranty period", "guarantee", "guaranty"],
            'semiconductor': ["semiconductor", "semiconductors", "chips", "chip", "integrated circuit"],
        }

        # Build groups if the query mentions them
        if any(token in q for token in ["iso 9001", "iso-9001", "iso9001", "quality management"]):
            groups.append(concepts['iso_9001'])
        if any(token in q for token in ["force majeure", "act of god", "unforeseen circumstances"]):
            groups.append(concepts['force_majeure'])
        if any(token in q for token in ["warranty", "guarantee", "warranty period", "guaranty"]):
            groups.append(concepts['warranty'])
        if any(token in q for token in ["semiconductor", "chips", "chip", "integrated circuit"]):
            groups.append(concepts['semiconductor'])

        # If the query uses "both" or "and", we keep AND logic across groups.
        # If none of the known concepts are detected, return empty to skip.
        return groups
    
    def _prepare_rag_search_context(
        self,
        documents: List["Document"],
        clause_types: List[str],
        clause_conditions: Optional[Dict[str, Any]] = None,
        risk_factors: Optional[List[str]] = None,
        raw_query: Optional[str] = None
    ) -> str:
        """Prepare context for RAG search through documents"""
        context_parts = [
            f"ANALYZE THESE {len(documents)} CONTRACT DOCUMENTS",
            f"USER NATURAL LANGUAGE QUERY: {raw_query or 'N/A'}",
            f"SEARCH QUERY: Find documents with {', '.join(clause_types)} clauses"
        ]
        
        if clause_conditions:
            context_parts.append(f"SPECIFIC REQUIREMENTS: {clause_conditions}")
        
        if risk_factors:
            context_parts.append(f"RISK FACTORS: {', '.join(risk_factors)}")
        
        # Add specific search guidance based on clause types
        search_guidance = []
        for clause_type in clause_types:
            if "iso" in clause_type.lower() or "certification" in clause_type.lower():
                search_guidance.append(f"Look for ISO standards, quality management systems, certifications, compliance requirements")
            if "warranty" in clause_type.lower():
                search_guidance.append(f"Look for warranty periods, guarantees, quality assurances, time-based commitments")
            if "quality" in clause_type.lower():
                search_guidance.append(f"Look for quality standards, quality control, quality management, quality requirements")
        
        if search_guidance:
            context_parts.append(f"SEARCH GUIDANCE: {'; '.join(search_guidance)}")
        
        context_parts.append("")
        
        # Add document content for analysis with clear document identification
        doc_contents = []
        total_tokens_estimate = 0
        max_tokens_per_doc = 4000  # Allow more content per document
        max_total_tokens = 120000   # Leave room for prompt and response
        
        for i, doc in enumerate(documents):
            if doc.extracted_text and total_tokens_estimate < max_total_tokens:
                # Clean up the text but preserve structure
                text = doc.extracted_text
                
                # Remove excessive whitespace but keep line breaks for readability
                text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
                
                # Estimate tokens (roughly 4 characters per token)
                estimated_tokens = len(text) // 4
                
                if estimated_tokens > max_tokens_per_doc:
                    # If document is too long, try to find the most relevant sections
                    relevant_sections = self._extract_relevant_sections(
                        text, clause_types, clause_conditions, max_tokens_per_doc
                    )
                    text = relevant_sections
                    estimated_tokens = len(text) // 4
                
                if total_tokens_estimate + estimated_tokens < max_total_tokens:
                    doc_contents.append(f"DOCUMENT {doc.id} ({doc.filename}):\n{text}")
                    total_tokens_estimate += estimated_tokens
                else:
                    # Stop adding documents if we're approaching token limit
                    break
        
        context_parts.append(f"DOCUMENTS TO ANALYZE ({len(doc_contents)} documents):\n" + "\n---\n".join(doc_contents))
        
        context_parts.append(
            "\nINSTRUCTIONS:"
        )
        context_parts.append(
            "1. Read and analyze each document above thoroughly"
        )
        context_parts.append(
            "2. Look for ANY content that matches the search query"
        )
        context_parts.append(
            "3. Don't just look for exact phrases - think broadly and intelligently"
        )
        context_parts.append(
            "4. If you find relevant information, include the document in your results"
        )
        context_parts.append(
            "5. Return ONLY the JSON response with your findings"
        )
        
        return "\n".join(context_parts)
    
    def _extract_relevant_sections(
        self,
        text: str,
        clause_types: List[str],
        clause_conditions: Optional[Dict[str, Any]] = None,
        max_tokens: int = 4000
    ) -> str:
        """Extract the most relevant sections of a document based on the search query"""
        try:
            # Split text into sections (by lines or paragraphs)
            lines = text.split('\n')
            relevant_lines = []
            current_section = []
            
            # Keywords to look for that might indicate relevant sections
            relevant_keywords = []
            for clause_type in clause_types:
                relevant_keywords.extend([
                    clause_type.lower(),
                    clause_type.replace(' ', '').lower(),
                    clause_type.replace(' ', '_').lower()
                ])
            
            if clause_conditions:
                # Add condition-related keywords
                condition_text = str(clause_conditions).lower()
                relevant_keywords.extend([
                    'termination', 'fee', 'penalty', 'cost', 'month', 'value',
                    'early', 'contract', 'agreement', 'clause', 'section',
                    'iso', '9001', 'certification', 'certified', 'quality', 'quality management',
                    'warranty', 'guarantee', 'period', 'months', 'years'
                ])
            
            # Find sections that contain relevant keywords
            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in relevant_keywords):
                    # Include this line and surrounding context
                    relevant_lines.append(line)
                    # Also include a few lines before and after for context
                    if len(relevant_lines) < max_tokens // 4:  # Rough token estimation
                        continue
                    else:
                        break
            
            if relevant_lines:
                # If we found relevant sections, return them
                return '\n'.join(relevant_lines)
            else:
                # If no relevant sections found, return the beginning of the document
                return text[:max_tokens]
                
        except Exception as e:
            # Fallback: return the beginning of the document
            return text[:max_tokens]
    
    def _build_rag_search_prompt(
        self,
        clause_types: List[str],
        clause_conditions: Optional[Dict[str, Any]] = None,
        risk_factors: Optional[List[str]] = None,
        raw_query: Optional[str] = None
    ) -> str:
        """Build the prompt for RAG document search"""
        prompt_parts = [
            "You are an expert contract analyst with deep understanding of legal documents, business contracts, and risk assessment.",
            "",
            "TASK: Analyze the provided contract documents to find ANY content that matches the user's natural language query.",
            "",
            "YOUR APPROACH:",
            "1. **Understand the user's intent** - What are they really looking for?",
            "2. **Think broadly and creatively** - Don't just look for exact phrases",
            "3. **Search thoroughly** - Examine every section, clause, and detail",
            "4. **Look for related concepts** - Synonyms, variations, and related terms",
            "5. **Consider context** - How does this information relate to the query?",
            "6. **Apply boolean logic** - Treat 'and' as ALL conditions must be present in the same document; treat 'or' as ANY; honor 'not'/'without' as exclusions",
            "7. **Respect numeric constraints** - Interpret quantities, durations, and thresholds (e.g., '24 months', 'over 3 months', 'greater than 20%') with unit awareness and synonyms ('24 months' ≈ '2 years')",
            "",
            f"USER QUERY: {raw_query or ('Find documents with ' + ', '.join(clause_types) + ' clauses')}"
        ]
        
        if clause_conditions:
            prompt_parts.append(f"SPECIFIC REQUIREMENTS: {clause_conditions}")
        
        if risk_factors:
            prompt_parts.append(f"RISK FACTORS TO CONSIDER: {', '.join(risk_factors)}")
        
        prompt_parts.extend([
            "",
            "SEARCH STRATEGY:",
            "1. **Read each document completely** - Don't skip sections",
            "2. **Look for explicit mentions** - Direct references to the requested information",
            "3. **Look for implicit mentions** - Related concepts, synonyms, or variations",
            "4. **Look for contextual clues** - Information that answers the user's question even if phrased differently",
            "5. **Consider business logic** - What would make sense in a business context?",
            "6. **Look in all sections** - Don't limit yourself to obvious sections",
            "",
            "EXAMPLES OF INTELLIGENT SEARCHING:",
            "If user asks for 'early termination fees over 3 months of order value':",
            "- Look for: 'Early Termination Fee', 'Termination Fee', 'Early Termination'",
            "- Look for: 'Buyer Termination: X months', 'Supplier Termination: X months'",
            "- Look for: Any mention of termination costs, penalties, or fees",
            "- Look for: Time-based penalties (months, quarters, etc.)",
            "- Look for: Value-based calculations (order value, monthly value, etc.)",
            "- Look in: Termination sections, penalty sections, cost sections",
            "",
            "If user asks for 'ISO 9001 certification and 24-month warranties':",
            "- Look for: 'ISO 9001', 'ISO 9000', 'quality management system', 'quality standards'",
            "- Look for: 'certification', 'certified', 'compliance', 'quality assurance'",
            "- Look for: 'warranty', 'warranty period', 'guarantee', 'quality guarantee'",
            "- Look for: Time periods like '24 months', '2 years', '730 days'",
            "- Look for: Quality-related terms like 'quality control', 'quality management'",
            "- Look in: Quality sections, warranty sections, compliance sections, general terms",
            "",
            "If user asks for 'force majeure clauses that don't cover pandemics':",
            "- Look for: 'Force Majeure', 'Act of God', 'unforeseen circumstances'",
            "- Look for: Specific exclusions like 'pandemics', 'epidemics', 'disease outbreaks'",
            "- Look for: Coverage lists and what's included/excluded",
            "- Look in: Force majeure sections, general terms, exclusions"
            "",
            "RESPONSE FORMAT - Return ONLY valid JSON:",
            "{",
            '  "matching_documents": [',
            '    {',
            '      "document_id": "EXACT_DOCUMENT_ID_FROM_THE_LIST",',
            '      "filename": "filename_from_document",',
            '      "relevance_score": 0.95,',
            '      "clause_findings": [',
            '        {',
            '          "clause_type": "what_you_found",',
            '          "found": true,',
            '          "details": "specific details about what you found",',
            '          "risk_level": "high/medium/low"',
            '        }',
            '      ]',
            '    }',
            '  ],',
            '  "clause_findings": [',
            '    {',
            '      "clause_type": "summary_of_findings",',
            '      "summary": "What you found and where",',
            '      "risk_indicators": ["specific risks or concerns"],',
            '      "compliance_gaps": ["compliance issues found"]',
            '    }',
            '  ],',
            '  "risk_indicators": ["List of identified risks"],',
            '  "compliance_gaps": ["List of compliance issues"],',
            '  "recommendations": ["List of recommendations"]',
            "}",
            "",
            "CRITICAL INSTRUCTIONS:",
            "1. **Be thorough and intelligent** - Use your expertise to find relevant information",
            "2. **Don't give up easily** - If you see something that might be relevant, investigate further",
            "3. **Think like a business analyst** - What would be important to know?",
            "4. **Return ONLY valid JSON** - No explanations or other text",
            "5. **Include ALL relevant documents** - If a document has relevant information, include it",
            "6. **Be specific about what you found** - Include details in your findings",
            "7. **Use high relevance scores** for clearly relevant documents (0.8-1.0)",
            "8. **Don't be overly strict** - If information is related to the query, include it"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_rag_search_results(
        self,
        response: str,
        documents: List["Document"]
    ) -> Dict[str, Any]:
        """Parse RAG search results from OpenAI response"""
        try:
            logger.info("Parsing RAG search results", response_length=len(response))
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                logger.info("RAG JSON parsed successfully", result_keys=list(result.keys()))
                
                # Convert document IDs to actual document objects
                matching_docs = []
                if result.get('matching_documents'):
                    logger.info(f"Found {len(result['matching_documents'])} matching documents in RAG response")
                    for doc_info in result['matching_documents']:
                        doc_id = doc_info.get('document_id')
                        logger.info(f"Processing document_id from RAG: {doc_id}")
                        if doc_id:
                            # Find the actual document
                            for doc in documents:
                                if str(doc.id) == str(doc_id):
                                    logger.info(f"Found matching document: {doc.id} - {doc.filename}")
                                    # Convert to dict format for consistency
                                    doc_dict = {
                                        'document_id': doc.id,
                                        'filename': doc.filename,
                                        'supplier_name': doc.extracted_metadata.get('supplier_name') if doc.extracted_metadata else None,
                                        'contract_amount': doc.extracted_metadata.get('contract_amount') if doc.extracted_metadata else None,
                                        'extracted_text': doc.extracted_text,
                                        'relevance_score': doc_info.get('relevance_score', 0.8)
                                    }
                                    matching_docs.append(doc_dict)
                                    break
                            else:
                                logger.warning(f"Document ID {doc_id} from RAG not found in documents list")
                        else:
                            logger.warning("RAG result missing document_id")
                else:
                    logger.warning("No matching_documents found in RAG response")
                
                logger.info(f"Final matching documents count: {len(matching_docs)}")
                
                return {
                    "clause_findings": result.get('clause_findings', []),
                    "risk_indicators": result.get('risk_indicators', []),
                    "compliance_gaps": result.get('compliance_gaps', []),
                    "recommendations": result.get('recommendations', []),
                    "matching_documents": matching_docs
                }
            else:
                logger.warning("No JSON found in RAG response")
                return {
                    "clause_findings": [],
                    "risk_indicators": [],
                    "compliance_gaps": [],
                    "recommendations": [],
                    "matching_documents": []
                }
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse RAG search results", response=response, error=str(e))
            return {
                "clause_findings": [],
                "risk_indicators": [],
                "compliance_gaps": [],
                "recommendations": [],
                "matching_documents": []
            }
    
    def _build_clause_analysis_prompt(
        self,
        clause_types: List[str],
        clause_conditions: Optional[Dict[str, Any]] = None,
        risk_factors: Optional[List[str]] = None
    ) -> str:
        """Build the prompt for clause analysis"""
        prompt_parts = [
            "You are a contract analysis expert. Analyze the provided contracts for the specified clauses.",
            f"Clause types to analyze: {', '.join(clause_types)}"
        ]
        
        if clause_conditions:
            prompt_parts.append(f"Specific conditions to check: {clause_conditions}")
        
        if risk_factors:
            prompt_parts.append(f"Risk factors to identify: {', '.join(risk_factors)}")
        
        prompt_parts.extend([
            "",
            "Provide your analysis in this JSON format:",
            "{",
            '  "clause_findings": [',
            '    {',
            '      "clause_type": "force_majeure",',
            '      "found": true,',
            '      "coverage": "pandemics, natural disasters",',
            '      "exclusions": ["pandemics"],',
            '      "risk_level": "high",',
            '      "contract_id": "contract_id_here"',
            '    }',
            '  ],',
            '  "risk_indicators": [',
            '    "force_majeure clause excludes pandemic coverage",',
            '    "penalty clause exceeds 20% threshold"',
            '  ],',
            '  "compliance_gaps": [',
            '    "Missing pandemic coverage in force majeure"',
            '  ],',
            '  "recommendations": [',
            '    "Update force majeure clauses to include pandemic coverage"',
            '  ]',
            "}"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_clause_analysis(self, response: str) -> Dict[str, Any]:
        """Parse OpenAI response for clause analysis"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "clause_findings": [],
                    "risk_indicators": [],
                    "compliance_gaps": [],
                    "recommendations": []
                }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse clause analysis", response=response, error=str(e))
            return {
                "clause_findings": [],
                "risk_indicators": [],
                "compliance_gaps": [],
                "recommendations": []
            }
    
    async def _assess_clause_risks(
        self,
        clause_analysis: Dict[str, Any],
        risk_factors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Assess risks based on clause analysis"""
        try:
            risk_assessment = {
                "overall_risk_level": "low",
                "risk_factors": [],
                "high_risk_clauses": [],
                "mitigation_recommendations": []
            }
            
            if not clause_analysis:
                return risk_assessment
            
            # Analyze clause findings for risks
            findings = clause_analysis.get("clause_findings", [])
            risk_indicators = clause_analysis.get("risk_indicators", [])
            
            # Count high-risk findings
            high_risk_count = sum(
                1 for finding in findings 
                if finding.get("risk_level") == "high"
            )
            
            # Determine overall risk level
            if high_risk_count > 3:
                risk_assessment["overall_risk_level"] = "critical"
            elif high_risk_count > 1:
                risk_assessment["overall_risk_level"] = "high"
            elif high_risk_count == 1:
                risk_assessment["overall_risk_level"] = "medium"
            
            # Add specific risk factors
            risk_assessment["risk_factors"] = risk_indicators
            risk_assessment["high_risk_clauses"] = [
                finding for finding in findings 
                if finding.get("risk_level") in ["high", "critical"]
            ]
            
            # Generate mitigation recommendations
            if risk_assessment["overall_risk_level"] != "low":
                risk_assessment["mitigation_recommendations"] = [
                    "Review and update high-risk clauses",
                    "Consider adding missing coverage for identified gaps",
                    "Consult legal team for high-risk contract modifications"
                ]
            
            return risk_assessment
            
        except Exception as e:
            logger.error("Risk assessment failed", error=str(e))
            return {
                "overall_risk_level": "unknown",
                "risk_factors": [],
                "high_risk_clauses": [],
                "mitigation_recommendations": []
            }
    
    async def _comprehensive_risk_analysis(
        self,
        risk_types: List[str],
        clause_analysis: Optional[Dict[str, Any]] = None,
        supplier_risk: Optional[Dict[str, Any]] = None,
        regulatory_changes: Optional[List[str]] = None,
        time_period: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive risk analysis"""
        try:
            # This would integrate with external risk assessment services
            # For now, return a structured analysis framework
            return {
                "risk_assessment": {
                    "overall_risk_score": 0.65,
                    "risk_breakdown": {
                        "financial_risk": 0.7,
                        "compliance_risk": 0.6,
                        "operational_risk": 0.5
                    }
                },
                "clause_analysis": clause_analysis or {},
                "regulatory_impact": {
                    "changes_identified": regulatory_changes or [],
                    "impact_assessment": "Medium impact on existing contracts"
                },
                "recommendations": [
                    "Update force majeure clauses for pandemic coverage",
                    "Review export control clauses for new restrictions",
                    "Assess penalty clause thresholds for financial risk"
                ]
            }
        except Exception as e:
            logger.error("Comprehensive risk analysis failed", error=str(e))
            return {
                "risk_assessment": {},
                "clause_analysis": {},
                "recommendations": [],
                "error": str(e)
            }
    
    async def _clause_comparison_analysis(
        self,
        clause_type: str,
        comparison_criteria: List[str],
        contract_ids: Optional[List[str]] = None,
        supplier_groups: Optional[List[str]] = None,
        benchmark_standards: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Perform clause comparison analysis"""
        try:
            # This would implement detailed clause comparison logic
            # For now, return a structured comparison framework
            return {
                "comparison_results": {
                    "clause_type": clause_type,
                    "criteria_analyzed": comparison_criteria,
                    "variations_found": 3,
                    "best_practices": ["Standardized duration limits", "Clear coverage definitions"]
                },
                "benchmark_analysis": {
                    "industry_standards": benchmark_standards or [],
                    "internal_baselines": "Based on top-performing contracts"
                },
                "recommendations": [
                    "Standardize clause language across contracts",
                    "Adopt best practices from high-performing agreements"
                ]
            }
        except Exception as e:
            logger.error("Clause comparison analysis failed", error=str(e))
            return {
                "comparison_results": {},
                "benchmark_analysis": {},
                "recommendations": [],
                "error": str(e)
            }
    
    def validate_intent_confidence(self, intent: QueryIntent) -> bool:
        """
        Validate if the intent confidence meets the required threshold (>90%).
        
        Args:
            intent: QueryIntent object to validate
            
        Returns:
            True if confidence is above threshold, False otherwise
        """
        return intent.confidence >= 0.9
    
    def _construct_query_from_filters(self, filters: Optional[Dict[str, Any]]) -> str:
        """
        Construct a natural language query from search filters for RAG fallback
        """
        if not filters:
            return ""
        
        query_parts = []
        
        if filters.get("supplier"):
            query_parts.append(f"contracts with {filters['supplier']}")
        
        if filters.get("tags"):
            tags = filters["tags"]
            if isinstance(tags, list):
                if len(tags) == 1:
                    query_parts.append(f"that have {tags[0]}")
                else:
                    tag_list = ", ".join(tags[:-1]) + f" and {tags[-1]}"
                    query_parts.append(f"that have {tag_list}")
        
        if filters.get("contract_type"):
            query_parts.append(f"of type {filters['contract_type']}")
        
        if filters.get("amount_min") or filters.get("amount_max"):
            if filters.get("amount_min") and filters.get("amount_max"):
                query_parts.append(f"with amounts between ${filters['amount_min']} and ${filters['amount_max']}")
            elif filters.get("amount_min"):
                query_parts.append(f"with amounts over ${filters['amount_min']}")
            elif filters.get("amount_max"):
                query_parts.append(f"with amounts under ${filters['amount_max']}")
        
        constructed_query = " ".join(query_parts)
        logger.info(f"Constructed query from filters: '{constructed_query}'")
        return constructed_query
    
    async def _rag_semantic_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page_size: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        RAG-powered semantic search fallback when Elasticsearch returns 0 results.
        Uses OpenAI to analyze actual document content semantically.
        """
        try:
            from app.core.database import get_db_context
            from app.models.document import Document
            import time
            
            start_time = time.time()
            
            logger.info(
                "Starting RAG semantic search",
                query=query,
                filters=filters,
                page_size=page_size
            )
            
            # Get documents from database
            with get_db_context() as db:
                db_query = db.query(Document).filter(
                    Document.status == "PROCESSED",
                    Document.extracted_text.isnot(None)
                )
                
                # Apply organization filter if available
                if filters and filters.get("organization_id"):
                    db_query = db_query.filter(Document.organization_id == filters["organization_id"])
                
                # Limit to reasonable number for RAG analysis
                documents = db_query.limit(100).all()
                
                if not documents:
                    logger.warning("No processed documents found for RAG search")
                    return None
                
                logger.info(f"Found {len(documents)} documents for RAG analysis")
                
                # Prepare documents for AI analysis
                document_contexts = []
                for doc in documents:
                    doc_context = {
                        "document_id": doc.id,
                        "filename": doc.filename,
                        "original_filename": doc.original_filename,
                        "extracted_text": doc.extracted_text[:5000],  # Limit text length
                        "extracted_metadata": doc.extracted_metadata or {}
                    }
                    document_contexts.append(doc_context)
                
                # Use OpenAI for semantic analysis
                rag_prompt = f"""
You are a contract discovery AI. Analyze the provided documents and find those that match this query: "{query}"

Search for documents that semantically match the query, not just exact keyword matches. Consider:
- Supplier types and industries (e.g., "semiconductor suppliers" matches "Global Electronics Manufacturing")
- Certifications and standards (e.g., "ISO 9001 certification" matches "ISO 9001:2015 certified")  
- Contract clauses and terms (e.g., "force majeure clauses" matches "Force Majeure" sections)
- Related concepts and synonyms

For each matching document, provide:
1. document_id
2. relevance_score (0.0 to 1.0)
3. match_reasons (why it matches the query)
4. key_excerpts (relevant text snippets)

Return ONLY a JSON array of matching documents, ordered by relevance_score (highest first).
Limit to top {page_size} most relevant results.

Documents to analyze:
{json.dumps(document_contexts[:20], indent=2)}  # Limit for token efficiency
"""
                
                # Call OpenAI
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a contract discovery AI that performs semantic document search."},
                        {"role": "user", "content": rag_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=4000
                )
                
                # Parse AI response
                ai_response = response.choices[0].message.content.strip()
                
                # Try to extract JSON from the response
                try:
                    # Look for JSON array in the response
                    import re
                    json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
                    if json_match:
                        ai_results = json.loads(json_match.group())
                    else:
                        # Fallback: try to parse the entire response as JSON
                        ai_results = json.loads(ai_response)
                    
                    if not isinstance(ai_results, list):
                        logger.warning("AI response is not a list, wrapping in array")
                        ai_results = [ai_results] if ai_results else []
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse AI response as JSON: {e}")
                    logger.debug(f"AI response: {ai_response}")
                    return None
                
                # Convert AI results to standard format
                rag_documents = []
                for ai_doc in ai_results:
                    if isinstance(ai_doc, dict) and ai_doc.get("document_id"):
                        # Find the original document
                        doc_id = str(ai_doc["document_id"])
                        original_doc = next(
                            (doc for doc in documents if str(doc.id) == doc_id), 
                            None
                        )
                        
                        if original_doc:
                            rag_doc = {
                                "id": original_doc.id,
                                "filename": original_doc.filename,
                                "original_filename": original_doc.original_filename,
                                "supplier_name": ai_doc.get("supplier_name", "Unknown"),
                                "contract_amount": getattr(original_doc.extracted_metadata, 'get', lambda x, d: d)('contract_amount', 0) if original_doc.extracted_metadata else 0,
                                "contract_date": getattr(original_doc.extracted_metadata, 'get', lambda x, d: d)('contract_date', None) if original_doc.extracted_metadata else None,
                                "relevance_score": ai_doc.get("relevance_score", 0.8),
                                "match_reasons": ai_doc.get("match_reasons", []),
                                "key_excerpts": ai_doc.get("key_excerpts", []),
                                "search_highlights": ai_doc.get("key_excerpts", [])[:3]  # Limit highlights
                            }
                            rag_documents.append(rag_doc)
                
                search_time = (time.time() - start_time) * 1000
                
                logger.info(
                    "RAG semantic search completed",
                    results_found=len(rag_documents),
                    search_time_ms=search_time
                )
                
                return {
                    "documents": rag_documents,
                    "total_count": len(rag_documents),
                    "search_time_ms": search_time,
                    "query": query,
                    "filters_applied": filters or {},
                    "performance_met": search_time < 5000,  # 5 second limit for RAG
                    "search_method": "RAG_SEMANTIC_SEARCH"
                }
                
        except Exception as e:
            logger.error("RAG semantic search failed", error=str(e))
            import traceback
            logger.debug("RAG search traceback", traceback=traceback.format_exc())
            return None


class IntentClassificationResult:
    """Result of intent classification"""
    
    def __init__(self, intent: IntentType, confidence: float):
        self.intent = intent
        self.confidence = confidence

