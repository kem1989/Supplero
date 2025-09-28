"""
Intent classification logic for AI Assistant.
"""

import structlog
import httpx
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings

logger = structlog.get_logger(__name__)


class IntentType(str, Enum):
    """Simplified intent types for natural language to SQL conversion - v2.0"""
    
    # Primary data retrieval intent
    SQL_QUERY = "SQL_QUERY"  # Standard data retrieval queries
    
    # Analytical queries with aggregations and calculations
    SQL_ANALYTICS = "SQL_ANALYTICS"  # Analytics, reporting, aggregations, statistics
    
    # Comparative analysis between entities
    COMPARISON_QUERY = "COMPARISON_QUERY"  # Side-by-side comparisons, benchmarking
    
    # Explanatory content based on data analysis
    GENERATE_EXPLANATION = "GENERATE_EXPLANATION"  # Contextual explanations, reasoning
    
    # Strategic insights and recommendations
    GENERATE_INSIGHTS = "GENERATE_INSIGHTS"  # Business intelligence, recommendations
    
    UNKNOWN = "UNKNOWN"


@dataclass
class IntentClassificationResult:
    """Result of intent classification"""
    intent: IntentType
    confidence: float
    reasoning: str
    context_parameters: Optional[Dict[str, Any]] = None


@dataclass
class MultiPartQueryComponent:
    """Represents a component of a multi-part query"""
    component_type: str  # "retrieval" or "explanation"
    intent: IntentType
    confidence: float
    reasoning: str
    query_text: str
    context_parameters: Optional[Dict[str, Any]] = None


@dataclass
class MultiPartQueryResult:
    """Result of multi-part query decomposition"""
    is_multi_part: bool
    components: List[MultiPartQueryComponent]
    primary_intent: IntentType
    overall_confidence: float
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
                            reasoning=classification.get("reasoning", "No reasoning provided"),
                            context_parameters=classification.get("context_parameters")
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
    
    async def detect_multi_part_query(self, query: str) -> MultiPartQueryResult:
        """
        Detect if a query is multi-part and decompose it into components.
        
        Args:
            query: The natural language query to analyze
            
        Returns:
            MultiPartQueryResult with decomposition information
        """
        try:
            system_prompt = self._build_multi_part_detection_prompt()
            
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
                            {"role": "user", "content": f"Analyze this query for multi-part components: {query}"}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Parse the JSON response
                    import json
                    try:
                        analysis = json.loads(content)
                        
                        if analysis.get("is_multi_part", False):
                            components = []
                            for comp_data in analysis.get("components", []):
                                try:
                                    intent = IntentType(comp_data.get("intent", "UNKNOWN"))
                                except ValueError:
                                    intent = IntentType.UNKNOWN
                                
                                component = MultiPartQueryComponent(
                                    component_type=comp_data.get("component_type", "unknown"),
                                    intent=intent,
                                    confidence=comp_data.get("confidence", 0.0),
                                    reasoning=comp_data.get("reasoning", ""),
                                    query_text=comp_data.get("query_text", ""),
                                    context_parameters=comp_data.get("context_parameters")
                                )
                                components.append(component)
                            
                            # Determine primary intent (usually the retrieval component)
                            primary_intent = IntentType.UNKNOWN
                            for component in components:
                                if component.component_type == "retrieval":
                                    primary_intent = component.intent
                                    break
                            if primary_intent == IntentType.UNKNOWN and components:
                                primary_intent = components[0].intent
                            
                            return MultiPartQueryResult(
                                is_multi_part=True,
                                components=components,
                                primary_intent=primary_intent,
                                overall_confidence=analysis.get("overall_confidence", 0.0),
                                reasoning=analysis.get("reasoning", "")
                            )
                        else:
                            # Single intent query
                            try:
                                primary_intent = IntentType(analysis.get("primary_intent", "UNKNOWN"))
                            except ValueError:
                                primary_intent = IntentType.UNKNOWN
                            
                            return MultiPartQueryResult(
                                is_multi_part=False,
                                components=[],
                                primary_intent=primary_intent,
                                overall_confidence=analysis.get("confidence", 0.0),
                                reasoning=analysis.get("reasoning", "")
                            )
                            
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse multi-part analysis JSON", content=content)
                        return MultiPartQueryResult(
                            is_multi_part=False,
                            components=[],
                            primary_intent=IntentType.UNKNOWN,
                            overall_confidence=0.0,
                            reasoning="Failed to parse analysis response"
                        )
                else:
                    logger.error("OpenAI API error for multi-part detection", status_code=response.status_code, response=response.text)
                    return MultiPartQueryResult(
                        is_multi_part=False,
                        components=[],
                        primary_intent=IntentType.UNKNOWN,
                        overall_confidence=0.0,
                        reasoning="OpenAI API error"
                    )
                    
        except Exception as e:
            logger.error("Multi-part query detection failed", error=str(e), exc_info=True)
            return MultiPartQueryResult(
                is_multi_part=False,
                components=[],
                primary_intent=IntentType.UNKNOWN,
                overall_confidence=0.0,
                reasoning=f"Detection error: {str(e)}"
            )
    
    def _build_tools_description(self) -> Dict[str, Dict[str, str]]:
        """Build the simplified tools description for SQL-based intent classification v2.0"""
        return {
            "SQL_QUERY": {
                "name": "SQL_QUERY",
                "description": "Standard data retrieval queries - covers simple to moderately complex SELECT operations"
            },
            "SQL_ANALYTICS": {
                "name": "SQL_ANALYTICS",
                "description": "Analytical queries with aggregations, calculations, and reporting - mathematical operations, grouping, trends, statistical analysis"
            },
            "COMPARISON_QUERY": {
                "name": "COMPARISON_QUERY",
                "description": "Comparative analysis between entities - side-by-side comparisons, benchmarking, difference analysis"
            },
            "GENERATE_EXPLANATION": {
                "name": "GENERATE_EXPLANATION",
                "description": "Explanatory content based on data analysis - contextual explanations, reasoning, educational responses about data"
            },
            "GENERATE_INSIGHTS": {
                "name": "GENERATE_INSIGHTS",
                "description": "Strategic insights, recommendations, and actionable intelligence - business intelligence, trend interpretation, strategic recommendations"
            }
        }
    
    def _build_intent_classification_prompt(self) -> str:
        """Build the simplified system prompt for SQL-based intent classification v2.0"""
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.tools.values()
        ])
        
        return f"""You are an AI assistant that classifies natural language queries into specific intents for a contract and supplier management system that uses SQL generation.

Available intents:
{tools_description}

Your task is to classify the user's query into one of these intents with a confidence score (0.0 to 1.0).

**Primary Decision Flow:**
1. **Asking for explanations or reasoning?** → `GENERATE_EXPLANATION`
2. **Asking for insights, recommendations, or strategy?** → `GENERATE_INSIGHTS`
3. **Explicitly comparing multiple entities?** → `COMPARISON_QUERY`
4. **Involves calculations, aggregations, or statistics?** → `SQL_ANALYTICS`
5. **Standard data retrieval request?** → `SQL_QUERY`

**Intent Selection Examples:**

| Query Pattern | Intent | Context |
|---------------|--------|---------|
| "Find all suppliers" | SQL_QUERY | domain=suppliers |
| "Count contracts by status" | SQL_ANALYTICS | metrics=count |
| "Compare supplier risk scores" | COMPARISON_QUERY | entities=suppliers |
| "Why is this contract risky?" | GENERATE_EXPLANATION | type=reasoning |
| "Give portfolio insights" | GENERATE_INSIGHTS | type=strategic |

**Detailed Classification Rules:**

**SQL_QUERY** (~55% of queries):
- Primary intent for most data requests
- Covers simple to moderately complex SELECT operations
- Basic searches, filters, lookups, standard business queries
- Examples: "Find all suppliers in China", "Show me active contracts with Huawei", "Get users with admin role"

**SQL_ANALYTICS** (~25% of queries):
- Queries involving mathematical operations, grouping, trends, statistical analysis
- Aggregations, statistics, trend analysis, performance metrics, dashboards
- Examples: "What's the average risk score by country?", "Show me contract count trends over time", "Get supplier risk distribution by industry"

**COMPARISON_QUERY** (~10% of queries):
- Side-by-side comparisons, benchmarking, difference analysis
- Supplier benchmarking, contract comparisons, risk analysis, performance comparisons
- Examples: "Compare risk scores between Chinese and European suppliers", "Show differences in contract terms by supplier"

**GENERATE_EXPLANATION** (~7% of queries):
- Contextual explanations, reasoning, educational responses about data
- Risk assessment explanations, methodology clarifications, business context
- Examples: "Explain why this supplier has a high risk score", "Tell me about risk factors in telecommunications industry"

**GENERATE_INSIGHTS** (~3% of queries):
- Business intelligence, trend interpretation, strategic recommendations
- Strategic recommendations, business insights, risk mitigation, portfolio optimization
- Examples: "Provide insights on supplier portfolio optimization", "What trends should we watch in contract risk?"

**Context Parameters:**
Extract relevant context parameters to provide additional specificity:

**Domain Context:**
- `suppliers`: Supplier-focused queries
- `contracts`: Contract-focused queries  
- `organizations`: Organization management
- `users`: User management
- `risk`: Risk assessment and analysis
- `compliance`: Compliance and regulatory

**Query Modifiers:**
- `time_scope`: today, this_week, this_month, this_year, custom_range
- `risk_level`: low, medium, high, critical
- `status`: active, inactive, expired, pending
- `filters`: geographic, industry, size, temporal

Respond in this exact JSON format:
{{
    "intent": "INTENT_NAME",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this intent was chosen",
    "context_parameters": {{
        "domain": "suppliers|contracts|organizations|users|risk|compliance",
        "time_scope": "today|this_week|this_month|this_year|custom_range",
        "risk_level": "low|medium|high|critical",
        "status": "active|inactive|expired|pending",
        "filters": ["geographic", "industry", "size", "temporal"]
    }}
}}"""
    
    def _build_multi_part_detection_prompt(self) -> str:
        """Build the system prompt for multi-part query detection v2.0"""
        
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.tools.values()
        ])
        
        return f"""You are an AI assistant that analyzes natural language queries to detect multi-part requests that combine data retrieval with explanation or insight generation.

Available intents for classification:
{tools_description}

Your task is to determine if a query has multiple parts and decompose it into components.

**Multi-Part Query Patterns:**
1. **Retrieval + Explanation**: "Find high-risk suppliers in China, then explain why Chinese suppliers have higher risk"
2. **Retrieval + Insights**: "Find suppliers in China, and tell me about semiconductor suppliers in China"
3. **Search + Analysis**: "Show me risky suppliers, then analyze their risk patterns"
4. **Data + Context**: "Get expiring contracts, then explain renewal best practices"

**Component Types:**
- **retrieval**: Queries that ask for specific data, contracts, suppliers, or search results (SQL_QUERY, SQL_ANALYTICS, COMPARISON_QUERY)
- **explanation**: Queries that ask for explanations, reasons, or context about retrieved data (GENERATE_EXPLANATION)
- **insights**: Queries that ask for analysis, trends, or recommendations (GENERATE_INSIGHTS)

**Detection Rules:**
1. Look for connecting words: "then", "and", "also", "plus", "furthermore", "additionally"
2. Look for explanation requests: "explain why", "tell me about", "give reasons", "what are the benefits"
3. Look for insight requests: "analyze", "trends", "recommendations", "insights", "summary"

**Examples:**

Query: "Find high-risk suppliers in China, then explain why Chinese suppliers have higher risk"
Response:
{{
    "is_multi_part": true,
    "components": [
        {{
            "component_type": "retrieval",
            "intent": "SQL_QUERY",
            "confidence": 0.95,
            "reasoning": "User wants to find suppliers with specific criteria",
            "query_text": "Find high-risk suppliers in China"
        }},
        {{
            "component_type": "explanation",
            "intent": "GENERATE_EXPLANATION",
            "confidence": 0.90,
            "reasoning": "User wants explanation about risk factors",
            "query_text": "explain why Chinese suppliers have higher risk"
        }}
    ],
    "primary_intent": "SQL_QUERY",
    "overall_confidence": 0.92,
    "reasoning": "Query combines data retrieval with explanation request"
}}

Query: "Find me suppliers in China"
Response:
{{
    "is_multi_part": false,
    "primary_intent": "SQL_QUERY",
    "confidence": 0.95,
    "reasoning": "Single intent query asking for supplier search"
}}

Respond in this exact JSON format:
{{
    "is_multi_part": boolean,
    "components": [
        {{
            "component_type": "retrieval|explanation|insights",
            "intent": "INTENT_NAME",
            "confidence": 0.95,
            "reasoning": "Brief explanation",
            "query_text": "Extracted query text for this component"
        }}
    ],
    "primary_intent": "INTENT_NAME",
    "overall_confidence": 0.92,
    "reasoning": "Overall analysis reasoning"
}}"""
