"""
Multi-part query processing logic for AI Assistant.
Handles decomposition and execution of multi-part natural language queries.
"""

import structlog
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from app.core.config import settings
from .intent_classifier import IntentClassifier, MultiPartQueryResult, MultiPartQueryComponent, IntentType
from .parameter_extractor import ParameterExtractor

logger = structlog.get_logger(__name__)


@dataclass
class QueryExecutionResult:
    """Result of executing a single query component"""
    component_type: str
    intent: IntentType
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class MultiPartExecutionResult:
    """Result of executing a multi-part query"""
    is_multi_part: bool
    retrieval_results: List[QueryExecutionResult]
    explanation_results: List[QueryExecutionResult]
    insights_results: List[QueryExecutionResult]
    overall_success: bool
    total_execution_time_ms: float
    unified_response: Dict[str, Any]


class MultiPartQueryProcessor:
    """Handles processing of multi-part natural language queries"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.parameter_extractor = ParameterExtractor()
    
    async def process_multi_part_query(
        self,
        query: str,
        db,
        current_user,
        ai_service
    ) -> MultiPartExecutionResult:
        """
        Process a multi-part query by detecting, decomposing, and executing components.
        
        Args:
            query: The natural language query
            db: Database session
            current_user: Current authenticated user
            ai_service: AI service instance for executing handlers
            
        Returns:
            MultiPartExecutionResult with unified response
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                "Processing multi-part query",
                query=query,
                user_id=current_user.id,
                organization_id=current_user.organization_id
            )
            
            # Step 1: Detect if query is multi-part
            multi_part_result = await self.intent_classifier.detect_multi_part_query(query)
            
            if not multi_part_result.is_multi_part:
                # Handle as single intent query
                return await self._handle_single_intent_query(
                    query, multi_part_result, db, current_user, ai_service, start_time
                )
            
            # Step 2: Execute components in parallel
            execution_tasks = []
            for component in multi_part_result.components:
                task = self._execute_component(
                    component, query, db, current_user, ai_service
                )
                execution_tasks.append(task)
            
            # Wait for all components to complete
            component_results = await asyncio.gather(*execution_tasks, return_exceptions=True)
            
            # Step 3: Categorize results
            retrieval_results = []
            explanation_results = []
            insights_results = []
            
            for i, result in enumerate(component_results):
                if isinstance(result, Exception):
                    logger.error(
                        "Component execution failed",
                        component_index=i,
                        error=str(result)
                    )
                    # Create error result
                    error_result = QueryExecutionResult(
                        component_type=multi_part_result.components[i].component_type,
                        intent=multi_part_result.components[i].intent,
                        success=False,
                        data={},
                        error=str(result)
                    )
                    
                    if multi_part_result.components[i].component_type == "retrieval":
                        retrieval_results.append(error_result)
                    elif multi_part_result.components[i].component_type == "explanation":
                        explanation_results.append(error_result)
                    elif multi_part_result.components[i].component_type == "insights":
                        insights_results.append(error_result)
                else:
                    if result.component_type == "retrieval":
                        retrieval_results.append(result)
                    elif result.component_type == "explanation":
                        explanation_results.append(result)
                    elif result.component_type == "insights":
                        insights_results.append(result)
            
            # Step 4: Generate unified response
            total_execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            unified_response = await self._generate_unified_response(
                query,
                multi_part_result,
                retrieval_results,
                explanation_results,
                insights_results,
                total_execution_time_ms
            )
            
            overall_success = all(
                result.success for result in retrieval_results + explanation_results + insights_results
            )
            
            logger.info(
                "Multi-part query processed successfully",
                is_multi_part=True,
                components_count=len(multi_part_result.components),
                overall_success=overall_success,
                execution_time_ms=total_execution_time_ms
            )
            
            return MultiPartExecutionResult(
                is_multi_part=True,
                retrieval_results=retrieval_results,
                explanation_results=explanation_results,
                insights_results=insights_results,
                overall_success=overall_success,
                total_execution_time_ms=total_execution_time_ms,
                unified_response=unified_response
            )
            
        except Exception as e:
            total_execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.error(
                "Multi-part query processing failed",
                query=query,
                error=str(e),
                execution_time_ms=total_execution_time_ms,
                exc_info=True
            )
            
            return MultiPartExecutionResult(
                is_multi_part=False,
                retrieval_results=[],
                explanation_results=[],
                insights_results=[],
                overall_success=False,
                total_execution_time_ms=total_execution_time_ms,
                unified_response={
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "message": "Failed to process multi-part query"
                }
            )
    
    async def _handle_single_intent_query(
        self,
        query: str,
        multi_part_result: MultiPartQueryResult,
        db,
        current_user,
        ai_service,
        start_time: datetime
    ) -> MultiPartExecutionResult:
        """Handle single intent queries using existing AI service"""
        
        try:
            # Use the intent classification and handler execution directly to avoid recursion
            intent = multi_part_result.primary_intent
            
            # Extract parameters
            parameters = await self.parameter_extractor.extract_parameters(query, intent)
            parameters["query"] = query
            
            # Execute the handler directly
            handler = ai_service.handlers.get(intent)
            if handler:
                execution_result = await handler(parameters, db, current_user)
                
                # Format the response
                processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                formatted_response = ai_service.response_formatter.format_response(
                    intent=intent,
                    execution_result=execution_result,
                    query=query,
                    processing_time_ms=processing_time_ms
                )
                
                formatted_response["intent_classification"] = {
                    "intent": intent.value,
                    "confidence": multi_part_result.overall_confidence,
                    "reasoning": multi_part_result.reasoning
                }
                
                return MultiPartExecutionResult(
                    is_multi_part=False,
                    retrieval_results=[],
                    explanation_results=[],
                    insights_results=[],
                    overall_success=execution_result.get("performance_met", False),
                    total_execution_time_ms=processing_time_ms,
                    unified_response=formatted_response
                )
            else:
                # No handler found
                total_execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                return MultiPartExecutionResult(
                    is_multi_part=False,
                    retrieval_results=[],
                    explanation_results=[],
                    insights_results=[],
                    overall_success=False,
                    total_execution_time_ms=total_execution_time_ms,
                    unified_response={
                        "query": query,
                        "success": False,
                        "error": f"No handler found for intent: {intent.value}",
                        "message": "Handler not implemented"
                    }
                )
            
        except Exception as e:
            total_execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.error(
                "Single intent query processing failed",
                query=query,
                error=str(e),
                exc_info=True
            )
            
            return MultiPartExecutionResult(
                is_multi_part=False,
                retrieval_results=[],
                explanation_results=[],
                insights_results=[],
                overall_success=False,
                total_execution_time_ms=total_execution_time_ms,
                unified_response={
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "message": "Failed to process single intent query"
                }
            )
    
    async def _execute_component(
        self,
        component: MultiPartQueryComponent,
        original_query: str,
        db,
        current_user,
        ai_service
    ) -> QueryExecutionResult:
        """Execute a single query component"""
        
        component_start_time = datetime.utcnow()
        
        try:
            logger.info(
                "Executing query component",
                component_type=component.component_type,
                intent=component.intent.value,
                query_text=component.query_text
            )
            
            if component.component_type == "retrieval":
                # Execute retrieval directly to avoid recursion
                parameters = await self.parameter_extractor.extract_parameters(component.query_text, component.intent)
                parameters["query"] = component.query_text
                
                handler = ai_service.handlers.get(component.intent)
                if handler:
                    execution_result = await handler(parameters, db, current_user)
                    
                    execution_time_ms = (datetime.utcnow() - component_start_time).total_seconds() * 1000
                    
                    return QueryExecutionResult(
                        component_type="retrieval",
                        intent=component.intent,
                        success=execution_result.get("performance_met", False),
                        data=execution_result,
                        execution_time_ms=execution_time_ms
                    )
                else:
                    execution_time_ms = (datetime.utcnow() - component_start_time).total_seconds() * 1000
                    
                    return QueryExecutionResult(
                        component_type="retrieval",
                        intent=component.intent,
                        success=False,
                        data={},
                        error=f"No handler found for intent: {component.intent.value}",
                        execution_time_ms=execution_time_ms
                    )
            
            elif component.component_type in ["explanation", "insights"]:
                # Generate explanation or insights using LLM
                generated_content = await self._generate_explanation_or_insights(
                    component, original_query, ai_service
                )
                
                execution_time_ms = (datetime.utcnow() - component_start_time).total_seconds() * 1000
                
                return QueryExecutionResult(
                    component_type=component.component_type,
                    intent=component.intent,
                    success=True,
                    data=generated_content,
                    execution_time_ms=execution_time_ms
                )
            
            else:
                execution_time_ms = (datetime.utcnow() - component_start_time).total_seconds() * 1000
                
                return QueryExecutionResult(
                    component_type=component.component_type,
                    intent=component.intent,
                    success=False,
                    data={},
                    error=f"Unknown component type: {component.component_type}",
                    execution_time_ms=execution_time_ms
                )
                
        except Exception as e:
            execution_time_ms = (datetime.utcnow() - component_start_time).total_seconds() * 1000
            
            logger.error(
                "Component execution failed",
                component_type=component.component_type,
                intent=component.intent.value,
                error=str(e),
                exc_info=True
            )
            
            return QueryExecutionResult(
                component_type=component.component_type,
                intent=component.intent,
                success=False,
                data={},
                error=str(e),
                execution_time_ms=execution_time_ms
            )
    
    async def _generate_explanation_or_insights(
        self,
        component: MultiPartQueryComponent,
        original_query: str,
        ai_service
    ) -> Dict[str, Any]:
        """Generate explanation or insights using LLM"""
        
        try:
            # Build context-aware prompt for explanation/insights
            system_prompt = self._build_explanation_prompt(component.component_type)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
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
                            {"role": "user", "content": f"Query: {original_query}\nComponent: {component.query_text}"}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 800
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    return {
                        "type": component.component_type,
                        "content": content,
                        "intent": component.intent.value,
                        "confidence": component.confidence,
                        "reasoning": component.reasoning
                    }
                else:
                    logger.error(
                        "OpenAI API error for explanation generation",
                        status_code=response.status_code,
                        response=response.text
                    )
                    return {
                        "type": component.component_type,
                        "content": "Unable to generate explanation due to API error.",
                        "intent": component.intent.value,
                        "confidence": 0.0,
                        "error": "OpenAI API error"
                    }
                    
        except Exception as e:
            logger.error(
                "Explanation generation failed",
                component_type=component.component_type,
                error=str(e),
                exc_info=True
            )
            return {
                "type": component.component_type,
                "content": f"Unable to generate explanation: {str(e)}",
                "intent": component.intent.value,
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _build_explanation_prompt(self, component_type: str) -> str:
        """Build system prompt for explanation/insights generation"""
        
        if component_type == "explanation":
            return """You are an AI assistant that provides detailed explanations about procurement, contracts, and supplier management topics.

Your task is to provide clear, informative explanations that help users understand:
- Why certain practices exist in procurement and contract management
- The benefits and rationale behind specific contract clauses
- Industry standards and best practices
- Legal and business reasoning behind common contract terms

Guidelines:
1. Be specific and factual
2. Use business and legal context when relevant
3. Provide practical insights
4. Keep explanations clear and concise
5. Focus on actionable information

Provide a comprehensive explanation that addresses the user's question."""
        
        elif component_type == "insights":
            return """You are an AI assistant that provides strategic insights about procurement, suppliers, and contract management.

Your task is to provide valuable insights that help users understand:
- Industry trends and patterns
- Risk factors and mitigation strategies
- Best practices for supplier management
- Market dynamics and competitive landscape
- Strategic recommendations

Guidelines:
1. Provide actionable insights
2. Include relevant industry context
3. Highlight key trends and patterns
4. Suggest practical recommendations
5. Consider risk and opportunity factors

Provide strategic insights that help with decision-making."""
        
        else:
            return """You are an AI assistant that provides helpful information about procurement and supplier management topics.

Provide clear, informative responses that help users understand the topic at hand."""
    
    async def _generate_unified_response(
        self,
        original_query: str,
        multi_part_result: MultiPartQueryResult,
        retrieval_results: List[QueryExecutionResult],
        explanation_results: List[QueryExecutionResult],
        insights_results: List[QueryExecutionResult],
        total_execution_time_ms: float
    ) -> Dict[str, Any]:
        """Generate a unified response combining all components"""
        
        # Extract retrieval data
        retrieval_data = []
        for result in retrieval_results:
            if result.success and result.data:
                # Extract clickable results from retrieval data
                if "contracts" in result.data:
                    for contract in result.data["contracts"]:
                        retrieval_data.append({
                            "type": "contract",
                            "id": contract.get("id"),
                            "name": contract.get("contract_name", "Unnamed Contract"),
                            "supplier": contract.get("supplier_name"),
                            "value": contract.get("contract_value"),
                            "link": f"/documents?documentId={contract.get('id')}",
                            "description": f"Contract with {contract.get('supplier_name', 'Unknown Supplier')}"
                        })
                
                elif "suppliers" in result.data:
                    for supplier in result.data["suppliers"]:
                        retrieval_data.append({
                            "type": "supplier",
                            "id": supplier.get("id"),
                            "name": supplier.get("name"),
                            "industry": supplier.get("industry"),
                            "location": supplier.get("location"),
                            "risk_score": supplier.get("risk_score"),
                            "link": f"/suppliers?ids={supplier.get('id')}",
                            "description": f"{supplier.get('industry', 'Unknown')} supplier in {supplier.get('location', 'Unknown')}"
                        })
        
        # Extract explanations and insights
        explanations = []
        for result in explanation_results:
            if result.success and result.data:
                explanations.append({
                    "title": f"Explanation: {result.data.get('intent', 'Unknown')}",
                    "content": result.data.get("content", ""),
                    "confidence": result.data.get("confidence", 0.0)
                })
        
        insights = []
        for result in insights_results:
            if result.success and result.data:
                insights.append({
                    "title": f"Insights: {result.data.get('intent', 'Unknown')}",
                    "content": result.data.get("content", ""),
                    "confidence": result.data.get("confidence", 0.0)
                })
        
        # Build unified response
        unified_response = {
            "query": original_query,
            "is_multi_part": True,
            "success": len(retrieval_results) > 0 or len(explanations) > 0 or len(insights) > 0,
            "timestamp": datetime.utcnow().isoformat(),
            "execution_time_ms": round(total_execution_time_ms, 2),
            "intent_classification": {
                "primary_intent": multi_part_result.primary_intent.value,
                "overall_confidence": multi_part_result.overall_confidence,
                "reasoning": multi_part_result.reasoning
            },
            "results": {
                "retrieval": {
                    "type": "search_results",
                    "title": "🔍 Search Results",
                    "data": retrieval_data,
                    "count": len(retrieval_data),
                    "has_results": len(retrieval_data) > 0
                },
                "explanations": {
                    "type": "explanations",
                    "title": "💡 Explanations",
                    "data": explanations,
                    "count": len(explanations),
                    "has_results": len(explanations) > 0
                },
                "insights": {
                    "type": "insights",
                    "title": "📊 Insights",
                    "data": insights,
                    "count": len(insights),
                    "has_results": len(insights) > 0
                }
            },
            "summary": {
                "total_components": len(multi_part_result.components),
                "retrieval_success": len([r for r in retrieval_results if r.success]) > 0,
                "explanation_success": len([r for r in explanation_results if r.success]) > 0,
                "insights_success": len([r for r in insights_results if r.success]) > 0
            }
        }
        
        return unified_response
