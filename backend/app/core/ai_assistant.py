"""
AI Assistant service for natural language query processing and intent recognition.
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import openai
from openai import OpenAI
import structlog

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class IntentType(str, Enum):
    """Supported intent types for natural language queries"""
    SEARCH_CONTRACTS = "SEARCH_CONTRACTS"
    GET_DETAILS = "GET_DETAILS"
    EXPORT = "EXPORT"
    UNKNOWN = "UNKNOWN"


class ToolType(str, Enum):
    """Available tools for the AI assistant"""
    SEARCH_CONTRACTS = "SEARCH_CONTRACTS"
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
        
    def _initialize_tools(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the available tools registry"""
        return {
            ToolType.SEARCH_CONTRACTS: {
                "name": "SEARCH_CONTRACTS",
                "description": "Search for contracts based on various criteria like supplier, amount, date, document type",
                "parameters": {
                    "supplier": "string - Supplier name or company",
                    "amount_min": "number - Minimum contract amount",
                    "amount_max": "number - Maximum contract amount", 
                    "date_from": "string - Start date (YYYY-MM-DD)",
                    "date_to": "string - End date (YYYY-MM-DD)",
                    "document_type": "string - Type of document (contract, invoice, etc.)",
                    "tags": "array - List of tags to filter by"
                },
                "examples": [
                    "Find contracts with supplier ABC Corp",
                    "Show contracts over $100,000 from last year",
                    "Get contracts with tag 'high-risk'"
                ]
            },
            ToolType.GET_DETAILS: {
                "name": "GET_DETAILS", 
                "description": "Get detailed information about a specific contract or document",
                "parameters": {
                    "document_id": "string - Document ID to retrieve details for",
                    "include_metadata": "boolean - Whether to include extracted metadata",
                    "include_text": "boolean - Whether to include extracted text content"
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

Respond in this exact JSON format:
{{
    "intent": "INTENT_NAME",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this intent was chosen"
}}

Examples:
- "Find contracts with supplier ABC Corp" → SEARCH_CONTRACTS
- "Show me details for contract ABC-123" → GET_DETAILS  
- "Export all contracts to CSV" → EXPORT
- "What's the weather like?" → UNKNOWN

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
    
    def validate_intent_confidence(self, intent: QueryIntent) -> bool:
        """
        Validate if the intent confidence meets the required threshold (>90%).
        
        Args:
            intent: QueryIntent object to validate
            
        Returns:
            True if confidence is above threshold, False otherwise
        """
        return intent.confidence >= 0.9


class IntentClassificationResult:
    """Result of intent classification"""
    
    def __init__(self, intent: IntentType, confidence: float):
        self.intent = intent
        self.confidence = confidence
