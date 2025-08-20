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
        
        elif intent in [IntentType.SEARCH_SUPPLIERS, IntentType.ANALYZE_SUPPLIER_RISK, IntentType.COMPARE_SUPPLIERS]:
            return base_prompt + """
For supplier-related queries, extract these parameters:
- supplier_name: Name of the supplier (string)
- supplier_ids: List of supplier IDs (array of numbers)
- industry: Industry sector (string)
- country: Country or location (string)
- risk_level: Risk level like "LOW", "MEDIUM", "HIGH" (string)
- min_risk_score: Minimum risk score (number 0-100)
- max_risk_score: Maximum risk score (number 0-100)
- watchlisted_only: Filter for watchlisted suppliers only (boolean)
- risk_types: Types of risk to analyze (array of strings)
- time_period: Time period for analysis in days (number)
- include_news: Include news analysis (boolean)
- include_financial: Include financial analysis (boolean)
- benchmark_industry: Include industry benchmarks (boolean)
- comparison_criteria: Criteria for comparison (array of strings)
- include_history: Include historical data (boolean)

Return only the parameters that are explicitly mentioned in the query.
"""
        
        elif intent == IntentType.SUPPLIER_INSIGHTS:
            return base_prompt + """
For supplier insights queries, extract these parameters:
- insight_type: Type of insights like "portfolio_overview", "risk_trends", "performance_analysis" (string)
- supplier_ids: Specific suppliers to analyze (array of numbers)
- time_period: Analysis time period in days (number)
- industry_focus: Focus on specific industry (string)
- risk_threshold: Risk threshold for analysis (number)
- include_predictions: Include predictive analysis (boolean)
- include_recommendations: Include recommendations (boolean)

Return only the parameters that are explicitly mentioned in the query.
"""
        
        elif intent in [IntentType.SUPPLIERS_WITH_RISKY_CONTRACTS, IntentType.SUPPLIERS_WITH_EXPIRING_CONTRACTS]:
            return base_prompt + """
For cross-system queries, extract these parameters:
- contract_risk_level: Risk level for contracts (string)
- supplier_risk_level: Risk level for suppliers (string)
- supplier_industries: Filter by industries (array of strings)
- supplier_countries: Filter by countries (array of strings)
- contract_value_min: Minimum contract value (number)
- contract_expiring_days: Days until contract expiration (number)
- page: Page number for results (number)
- page_size: Number of results per page (number)

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
