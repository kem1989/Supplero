"""
Intent classification logic for AI Assistant.
"""

import structlog
import httpx
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings

logger = structlog.get_logger(__name__)


class IntentType(str, Enum):
    """Available intent types for natural language queries"""
    # Contract-related intents
    SEARCH_CONTRACTS = "SEARCH_CONTRACTS"
    SEARCH_CLAUSES = "SEARCH_CLAUSES"
    ANALYZE_RISK = "ANALYZE_RISK"
    COMPARE_CLAUSES = "COMPARE_CLAUSES"
    GET_DETAILS = "GET_DETAILS"
    EXPORT = "EXPORT"
    
    # Supplier-related intents
    SEARCH_SUPPLIERS = "SEARCH_SUPPLIERS"
    ANALYZE_SUPPLIER_RISK = "ANALYZE_SUPPLIER_RISK"
    COMPARE_SUPPLIERS = "COMPARE_SUPPLIERS"
    SUPPLIER_INSIGHTS = "SUPPLIER_INSIGHTS"
    
    # Cross-system intents
    SUPPLIERS_WITH_RISKY_CONTRACTS = "SUPPLIERS_WITH_RISKY_CONTRACTS"
    SUPPLIERS_WITH_EXPIRING_CONTRACTS = "SUPPLIERS_WITH_EXPIRING_CONTRACTS"
    SUPPLIERS_BY_CONTRACT_CLAUSES = "SUPPLIERS_BY_CONTRACT_CLAUSES"
    CONTRACTS_BY_SUPPLIER_RISK = "CONTRACTS_BY_SUPPLIER_RISK"
    UNIFIED_RISK_SEARCH = "UNIFIED_RISK_SEARCH"
    
    # Enhanced intelligence intents
    PORTFOLIO_RISK_ANALYSIS = "PORTFOLIO_RISK_ANALYSIS"
    GEOGRAPHIC_RISK_CLUSTERING = "GEOGRAPHIC_RISK_CLUSTERING"
    INDUSTRY_RISK_CLUSTERING = "INDUSTRY_RISK_CLUSTERING"
    CONTRACT_IMPACT_ASSESSMENT = "CONTRACT_IMPACT_ASSESSMENT"
    SUPPLIER_TREND_ANALYSIS = "SUPPLIER_TREND_ANALYSIS"
    PREDICTIVE_RISK_MODELING = "PREDICTIVE_RISK_MODELING"
    INTELLIGENT_RECOMMENDATIONS = "INTELLIGENT_RECOMMENDATIONS"
    
    UNKNOWN = "UNKNOWN"


@dataclass
class IntentClassificationResult:
    """Result of intent classification"""
    intent: IntentType
    confidence: float
    reasoning: str


class IntentClassifier:
    """Handles intent classification for natural language queries"""
    
    def __init__(self):
        self.tools = self._build_tools_description()
    
    async def classify_intent(self, query: str) -> IntentClassificationResult:
        """
        Classify the intent of a natural language query using OpenAI.
        
        Args:
            query: The natural language query to classify
            
        Returns:
            IntentClassificationResult with intent, confidence, and reasoning
        """
        try:
            system_prompt = self._build_intent_classification_prompt()
            
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
                            {"role": "user", "content": f"Classify this query: {query}"}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 200
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Parse the JSON response
                    import json
                    try:
                        classification = json.loads(content)
                        intent_str = classification.get("intent", "UNKNOWN")
                        
                        # Convert string to IntentType enum
                        try:
                            intent = IntentType(intent_str)
                        except ValueError:
                            intent = IntentType.UNKNOWN
                        
                        return IntentClassificationResult(
                            intent=intent,
                            confidence=classification.get("confidence", 0.0),
                            reasoning=classification.get("reasoning", "No reasoning provided")
                        )
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse classification JSON", content=content)
                        return IntentClassificationResult(
                            intent=IntentType.UNKNOWN,
                            confidence=0.0,
                            reasoning="Failed to parse classification response"
                        )
                else:
                    logger.error("OpenAI API error", status_code=response.status_code, response=response.text)
                    return IntentClassificationResult(
                        intent=IntentType.UNKNOWN,
                        confidence=0.0,
                        reasoning="OpenAI API error"
                    )
                    
        except Exception as e:
            logger.error("Intent classification failed", error=str(e), exc_info=True)
            return IntentClassificationResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                reasoning=f"Classification error: {str(e)}"
            )
    
    def _build_tools_description(self) -> Dict[str, Dict[str, str]]:
        """Build the tools description for intent classification"""
        return {
            "SEARCH_CONTRACTS": {
                "name": "SEARCH_CONTRACTS",
                "description": "Search for contracts by supplier, value, date, or tags"
            },
            "SEARCH_CLAUSES": {
                "name": "SEARCH_CLAUSES", 
                "description": "Search for specific clauses or terms within contracts"
            },
            "ANALYZE_RISK": {
                "name": "ANALYZE_RISK",
                "description": "Analyze contract risk factors and compliance issues"
            },
            "COMPARE_CLAUSES": {
                "name": "COMPARE_CLAUSES",
                "description": "Compare clauses across multiple contracts"
            },
            "GET_DETAILS": {
                "name": "GET_DETAILS",
                "description": "Get detailed information about a specific contract"
            },
            "EXPORT": {
                "name": "EXPORT",
                "description": "Export contract data in various formats"
            },
            "SEARCH_SUPPLIERS": {
                "name": "SEARCH_SUPPLIERS",
                "description": "Search for suppliers by name, industry, location, or risk level"
            },
            "ANALYZE_SUPPLIER_RISK": {
                "name": "ANALYZE_SUPPLIER_RISK",
                "description": "Analyze supplier risk factors and assessment history"
            },
            "COMPARE_SUPPLIERS": {
                "name": "COMPARE_SUPPLIERS",
                "description": "Compare multiple suppliers across various criteria"
            },
            "SUPPLIER_INSIGHTS": {
                "name": "SUPPLIER_INSIGHTS",
                "description": "Generate insights, trends, and recommendations about suppliers"
            },
            "SUPPLIERS_WITH_RISKY_CONTRACTS": {
                "name": "SUPPLIERS_WITH_RISKY_CONTRACTS",
                "description": "Find suppliers that have risky contracts"
            },
            "SUPPLIERS_WITH_EXPIRING_CONTRACTS": {
                "name": "SUPPLIERS_WITH_EXPIRING_CONTRACTS",
                "description": "Find suppliers with contracts expiring soon"
            },
            "SUPPLIERS_BY_CONTRACT_CLAUSES": {
                "name": "SUPPLIERS_BY_CONTRACT_CLAUSES",
                "description": "Find suppliers based on specific contract clause types"
            },
            "CONTRACTS_BY_SUPPLIER_RISK": {
                "name": "CONTRACTS_BY_SUPPLIER_RISK",
                "description": "Find contracts based on supplier risk levels"
            },
            "UNIFIED_RISK_SEARCH": {
                "name": "UNIFIED_RISK_SEARCH",
                "description": "Comprehensive risk analysis across suppliers and contracts"
            }
        }
    
    def _build_intent_classification_prompt(self) -> str:
        """Build the system prompt for intent classification"""
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.tools.values()
        ])
        
        return f"""You are an AI assistant that classifies natural language queries into specific intents for a contract and supplier management system.

Available intents:
{tools_description}

Your task is to classify the user's query into one of these intents with a confidence score (0.0 to 1.0).

Key Classification Rules:

**Contract-Related Intents:**
1. **SEARCH_CLAUSES**: Use when query asks about specific clause content, coverage, or conditions
2. **ANALYZE_RISK**: Use when query asks about risk analysis, outdated clauses, or legal disputes
3. **COMPARE_CLAUSES**: Use when query asks to compare clauses across contracts or suppliers
4. **SEARCH_CONTRACTS**: Use for basic contract searches (supplier, amount, date, tags)

**Supplier-Related Intents:**
5. **SEARCH_SUPPLIERS**: Use when query asks to find or search for suppliers
6. **ANALYZE_SUPPLIER_RISK**: Use when query asks for supplier risk analysis or assessment
7. **COMPARE_SUPPLIERS**: Use when query asks to compare multiple suppliers
8. **SUPPLIER_INSIGHTS**: Use when query asks for insights, trends, or recommendations about suppliers

**Cross-System Intents:**
9. **SUPPLIERS_WITH_RISKY_CONTRACTS**: Use when query asks for suppliers that have risky contracts
10. **SUPPLIERS_WITH_EXPIRING_CONTRACTS**: Use when query asks for suppliers with expiring contracts
11. **SUPPLIERS_BY_CONTRACT_CLAUSES**: Use when query asks for suppliers based on specific contract clause types
12. **CONTRACTS_BY_SUPPLIER_RISK**: Use when query asks for contracts based on supplier risk levels
13. **UNIFIED_RISK_SEARCH**: Use when query asks for comprehensive risk analysis across suppliers and contracts

Respond in this exact JSON format:
{{
    "intent": "INTENT_NAME",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this intent was chosen"
}}"""
