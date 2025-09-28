"""
Parameter extraction logic for AI Assistant queries.
"""

import structlog
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

from app.core.config import settings
from .intent_classifier import IntentType

logger = structlog.get_logger(__name__)


class ParameterExtractor:
    """Handles parameter extraction from natural language queries"""
    
    async def extract_parameters(
        self,
        query: str,
        intent: IntentType
    ) -> Dict[str, Any]:
        """
        Extract parameters from a natural language query based on the intent.
        
        Args:
            query: The natural language query
            intent: The classified intent
            
        Returns:
            Dictionary of extracted parameters
        """
        try:
            system_prompt = self._build_parameter_extraction_prompt(intent)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.OPENAI_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Extract parameters from: {query}"}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 300
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    try:
                        parameters = json.loads(content)
                        # Post-process and validate parameters
                        return self._validate_and_clean_parameters(parameters, intent)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse parameter JSON", content=content)
                        return {}
                else:
                    logger.error("OpenAI API error for parameter extraction", 
                               status_code=response.status_code, response=response.text)
                    return {}
                    
        except Exception as e:
            logger.error("Parameter extraction failed", error=str(e), exc_info=True)
            return {}
    
    def _build_parameter_extraction_prompt(self, intent: IntentType) -> str:
        """Build the system prompt for parameter extraction based on intent"""
        
        base_prompt = """You are an AI assistant that extracts parameters from natural language queries for a contract and supplier management system.

Your task is to extract relevant parameters from the user's query and return them as a JSON object.

"""
        
        if intent in [IntentType.SEARCH_CONTRACTS, IntentType.GET_DETAILS, IntentType.EXPORT]:
            return base_prompt + """
For contract-related queries, extract these parameters when mentioned:
- supplier_name: Name of the supplier (string)
- contract_value_min: Minimum contract value (number)
- contract_value_max: Maximum contract value (number)
- date_from: Start date for filtering (ISO format string)
- date_to: End date for filtering (ISO format string)
- tags: List of tags to filter by (array of strings)
- contract_id: Specific contract ID (number)
- contract_ids: List of contract IDs (array of numbers)
- export_format: Export format like "json", "csv", "excel" (string)

Return only the parameters that are explicitly mentioned in the query.
"""
        
        elif intent in [IntentType.SEARCH_CLAUSES, IntentType.ANALYZE_RISK, IntentType.COMPARE_CLAUSES]:
            return base_prompt + """
For clause and risk analysis queries, extract these parameters:
- clause_types: Types of clauses mentioned (array of strings)
- search_terms: Specific terms to search for (array of strings)
- supplier_filter: Filter by supplier name (string)
- contract_ids: Specific contracts to analyze (array of numbers)
- risk_factors: Risk factors to analyze (array of strings)

Return only the parameters that are explicitly mentioned in the query.
"""
        
        elif intent in [IntentType.SEARCH_SUPPLIERS, IntentType.ANALYZE_SUPPLIER_RISK, IntentType.COMPARE_SUPPLIERS, IntentType.SUPPLIER_INSIGHTS]:
            return base_prompt + """
For supplier-related queries, extract these parameters when mentioned:
- supplier_name: Name of the supplier (string)
- supplier_names: List of supplier names (array of strings)
- industry: Industry sector (string)
- industries: List of industries (array of strings)
- country: Country (string)
- countries: List of countries (array of strings)
- risk_level: Risk level like "low", "medium", "high", "critical" (string)
- min_risk_score: Minimum risk score threshold (number, e.g., "above 50" -> 50)
- max_risk_score: Maximum risk score threshold (number, e.g., "below 80" -> 80)
- company_size: Company size like "small", "medium", "large" (string)
- is_watchlisted: Whether supplier is watchlisted (boolean)
- has_contracts: Whether supplier has contracts (boolean)
- contract_count_min: Minimum number of contracts (number)
- contract_count_max: Maximum number of contracts (number)

IMPORTANT: For risk score queries like "above 50", "below 80", "between 60 and 90":
- Extract "above X" as min_risk_score: X
- Extract "below X" as max_risk_score: X  
- Extract "between X and Y" as min_risk_score: X, max_risk_score: Y

Return only the parameters that are explicitly mentioned in the query.
"""
        
        elif intent in [IntentType.SUPPLIERS_WITH_RISKY_CONTRACTS, IntentType.SUPPLIERS_WITH_EXPIRING_CONTRACTS, IntentType.SUPPLIERS_BY_CONTRACT_CLAUSES, IntentType.CONTRACTS_BY_SUPPLIER_RISK, IntentType.UNIFIED_RISK_SEARCH, IntentType.SUPPLIERS_BY_SEMANTIC_CONTRACTS]:
            return base_prompt + """
For cross-system supplier-contract queries, extract these parameters when mentioned:
- contract_risk_level: Contract risk level like "low", "medium", "high", "critical" (string)
- supplier_risk_level: Supplier risk level like "low", "medium", "high", "critical" (string)
- supplier_industries: List of supplier industries (array of strings)
- supplier_countries: List of supplier countries (array of strings)
- contract_value_min: Minimum contract value (number)
- contract_value_max: Maximum contract value (number)
- contract_expiring_days: Days until contract expires (number)
- clause_types: List of clause types like "force_majeure", "termination" (array of strings)
- termination_days_min: Minimum termination notice days threshold (number)
- liability_cap_max_amount: Maximum liability cap amount in dollars (number)
- payment_terms_days_min: Minimum payment terms days (number, e.g., Net 30 -> 30)
- page: Page number for pagination (number)
- page_size: Number of results per page (number)

Return only the parameters that are explicitly mentioned in the query.
"""
        
        # NEW: Enhanced supplier-contract relationship parameter extraction
        elif intent in [IntentType.SUPPLIERS_BY_CONTRACT_VALUE, IntentType.SUPPLIERS_WITH_CONTRACT_CRITERIA, IntentType.CONTRACTS_BY_SUPPLIER_CRITERIA, IntentType.SUPPLIER_CONTRACT_PORTFOLIO]:
            return base_prompt + """
For enhanced supplier-contract relationship queries, extract these parameters when mentioned:
- contract_value_min: Minimum contract value in dollars (number)
- contract_value_max: Maximum contract value in dollars (number)
- contract_value_range: Contract value range like "over $5 million" (string)
- supplier_industry: Supplier industry sector (string)
- supplier_country: Supplier country (string)
- supplier_risk_level: Supplier risk level like "low", "medium", "high", "critical" (string)
- supplier_company_size: Company size like "small", "medium", "large" (string)
- contract_status: Contract status like "active", "expired", "pending" (string)
- contract_start_date: Contract start date (string)
- contract_end_date: Contract end date (string)
- contract_type: Type of contract like "service", "product", "partnership" (string)
- payment_terms: Payment terms like "net 30", "net 60" (string)
- contract_region: Geographic region for contracts (string)
- supplier_name: Specific supplier name (string)
- supplier_names: List of supplier names (array of strings)
- has_contracts: Whether suppliers have contracts (boolean)
- contract_count_min: Minimum number of contracts per supplier (number)
- contract_count_max: Maximum number of contracts per supplier (number)
- total_contract_value_min: Minimum total contract value across all contracts (number)
- total_contract_value_max: Maximum total contract value across all contracts (number)

IMPORTANT: For contract value queries like "over $5 million", "under $1 million", "between $2M and $10M":
- Extract "over X" as contract_value_min: X
- Extract "under X" as contract_value_max: X
- Extract "between X and Y" as contract_value_min: X, contract_value_max: Y

Return only the parameters that are explicitly mentioned in the query.
"""
        
        else:
            return base_prompt + """
Extract any relevant parameters mentioned in the query. Common parameters include:
- Names, IDs, dates, numbers, boolean flags, lists of items
- Time periods, thresholds, filters, criteria

Return only the parameters that are explicitly mentioned in the query as a JSON object.
"""
    
    def _validate_and_clean_parameters(
        self,
        parameters: Dict[str, Any],
        intent: IntentType
    ) -> Dict[str, Any]:
        """Validate and clean extracted parameters"""
        
        cleaned = {}
        
        for key, value in parameters.items():
            # Skip empty or null values
            if value is None or value == "" or value == []:
                continue
            
            # Clean string values
            if isinstance(value, str):
                cleaned[key] = value.strip()
            
            # Clean numeric values
            elif isinstance(value, (int, float)):
                if key.endswith('_score') or key.endswith('_threshold'):
                    # Risk scores should be 0-100
                    cleaned[key] = max(0, min(100, value))
                else:
                    cleaned[key] = value
            
            # Clean boolean values
            elif isinstance(value, bool):
                cleaned[key] = value
            
            # Clean list values
            elif isinstance(value, list):
                clean_list = [item.strip() if isinstance(item, str) else item for item in value if item]
                if clean_list:
                    cleaned[key] = clean_list
            
            else:
                cleaned[key] = value
        
        # Add default values for certain parameters
        if intent == IntentType.SUPPLIER_INSIGHTS:
            cleaned.setdefault('time_period', 90)
            cleaned.setdefault('include_predictions', True)
            cleaned.setdefault('include_recommendations', True)
        
        elif intent in [IntentType.SUPPLIERS_WITH_EXPIRING_CONTRACTS]:
            cleaned.setdefault('contract_expiring_days', 90)
        
        # Set pagination defaults
        if 'page' not in cleaned:
            cleaned['page'] = 1
        if 'page_size' not in cleaned:
            cleaned['page_size'] = 20
        
        return cleaned
