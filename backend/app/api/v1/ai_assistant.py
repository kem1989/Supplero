"""
AI Assistant API endpoints for natural language query processing.
Refactored version with modular architecture.
"""

import structlog
import time
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.core.logging import get_current_trace_context
# API credit tracker and query complexity analyzer removed for simplification
from app.models.user import User
from app.schemas.ai_assistant import NaturalLanguageQueryRequest, NaturalLanguageQueryResponse, ToolExecutionResponse
from app.core.tooling.registry import default_tool_registry, ToolSpec
from app.core.tooling.runner import ToolRunner

# Import the new modular components
from .ai_assistant_utils.intent_classifier import IntentClassifier, IntentType
from .ai_assistant_utils.parameter_extractor import ParameterExtractor
from .ai_assistant_utils.response_formatter import ResponseFormatter
# Multi-part query processor removed for simplification

# Import simplified SQL handlers (v2.0 - only 5 intents)
from .handlers.simplified_sql_handlers import (
    execute_sql_query,
    execute_sql_analytics,
    execute_comparison_query,
    execute_generate_explanation,
    execute_generate_insights
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ai-assistant", tags=["ai-assistant"])


class AIAssistantService:
    """Main AI Assistant service with modular architecture"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.parameter_extractor = ParameterExtractor()
        self.response_formatter = ResponseFormatter()
        self.tool_runner = ToolRunner()
        # Multi-part processor removed for simplification
        
        # Simplified handler mapping for SQL-based system
        self.handlers = {
            # Core SQL-based handlers (v2.0 - simplified)
            IntentType.SQL_QUERY: execute_sql_query,
            IntentType.SQL_ANALYTICS: execute_sql_analytics,
            IntentType.COMPARISON_QUERY: execute_comparison_query,
            
            # Multi-part query handlers
            IntentType.GENERATE_EXPLANATION: execute_generate_explanation,
            IntentType.GENERATE_INSIGHTS: execute_generate_insights
        }

        # Register handlers in tooling registry (no behavior change; prepares orchestration)
        for intent, handler in self.handlers.items():
            try:
                default_tool_registry.register(
                    ToolSpec(
                        name=intent.value,
                        description=f"Handler for {intent.value.replace('_', ' ').lower()}",
                        handler=handler,
                        category="assistant",
                        required_scopes=["read"],
                    )
                )
            except Exception:
                # Ignore duplicate registrations on reload
                pass
    
    async def process_query(
        self,
        query: str,
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """
        Process a natural language query through the complete AI pipeline.
        Now supports multi-part queries that combine retrieval with explanations/insights.
        
        Args:
            query: Natural language query from user
            db: Database session
            current_user: Current authenticated user
            
        Returns:
            Formatted response dictionary
        """
        start_time = time.time()
        
        # Analyze query complexity first
        complexity_analysis = {"complexity": "MEDIUM", "estimated_tokens": 100}  # Simplified
        
        # API credit tracking removed for simplification
        
        try:
            logger.info(
                "Processing AI assistant query",
                query=query,
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                complexity=complexity_analysis.get("complexity", "MEDIUM"),
                confidence=complexity_analysis.get("confidence", 0.8),
                estimated_credits=complexity_analysis.get("estimated_tokens", 100)
            )
            
            # Step 1: Single intent processing (v2.0 - simplified)
            # Step 1.1: Classify intent
            classification_result = await self.intent_classifier.classify_intent(query)
            
            logger.info(
                "Intent classified",
                intent=classification_result.intent.value,
                confidence=classification_result.confidence,
                reasoning=classification_result.reasoning
            )
            
            # Step 1.2: Extract parameters
            parameters = await self.parameter_extractor.extract_parameters(
                query, classification_result.intent
            )
            
            logger.info(
                "Parameters extracted",
                parameters=parameters,
                intent=classification_result.intent.value
            )
            
            # Step 1.3: Execute appropriate handler
            # Add original query to parameters for database search
            parameters["query"] = query
            execution_result = await self._execute_handler(
                classification_result.intent,
                parameters,
                db,
                current_user
            )
            
            # Step 1.4: Format response
            processing_time_ms = (time.time() - start_time) * 1000
            
            formatted_response = self.response_formatter.format_response(
                intent=classification_result.intent,
                execution_result=execution_result,
                query=query,
                processing_time_ms=processing_time_ms
            )
            
            # Add classification info
            formatted_response["intent_classification"] = {
                "intent": classification_result.intent.value,
                "confidence": classification_result.confidence,
                "reasoning": classification_result.reasoning
            }
            
            # Add helpful suggestions
            formatted_response = self.response_formatter.add_helpful_suggestions(
                formatted_response, classification_result.intent
            )
            
            # Add API credit usage information
            api_usage = {"tokens_used": 100, "cost_usd": 0.01}  # Simplified
            formatted_response["api_credit_usage"] = api_usage
            
            # Add complexity analysis information
            formatted_response["complexity_analysis"] = {
                "complexity": complexity_analysis.get("complexity", "MEDIUM"),
                "confidence": complexity_analysis.get("confidence", 0.8),
                "reasoning": complexity_analysis.get("reasoning", "Simplified analysis"),
                "estimated_api_credits": complexity_analysis.get("estimated_tokens", 100),
                "recommended_approach": complexity_analysis.get("recommended_approach", "SQL-based query"),
                "optimization_suggestions": complexity_analysis.get("optimization_suggestions", [])
            }
            
            logger.info(
                "Query processed successfully",
                intent=classification_result.intent.value,
                processing_time_ms=processing_time_ms,
                success=formatted_response.get("success", False),
                complexity=complexity_analysis.get("complexity", "MEDIUM"),
                api_usage=api_usage
            )
            
            return formatted_response
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Finish tracking even on error
            api_usage = {"tokens_used": 100, "cost_usd": 0.01}  # Simplified
            
            logger.error(
                "Failed to process AI assistant query",
                query=query,
                error=str(e),
                processing_time_ms=processing_time_ms,
                api_usage=api_usage,
                exc_info=True
            )
            
            return {
                "query": query,
                "intent": "UNKNOWN",
                "success": False,
                "error": str(e),
                "message": "Failed to process query",
                "processing_time_ms": processing_time_ms,
                "api_credit_usage": api_usage,
                "complexity_analysis": {
                    "complexity": complexity_analysis.get("complexity", "MEDIUM"),
                    "confidence": complexity_analysis.get("confidence", 0.8),
                    "reasoning": complexity_analysis.get("reasoning", "Simplified analysis"),
                    "estimated_api_credits": complexity_analysis.get("estimated_tokens", 100),
                    "recommended_approach": complexity_analysis.get("recommended_approach", "SQL-based query"),
                    "optimization_suggestions": complexity_analysis.get("optimization_suggestions", [])
                },
                "timestamp": time.time()
            }
    
    async def _execute_handler(
        self,
        intent: IntentType,
        parameters: Dict[str, Any],
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """Execute the appropriate handler for the given intent"""
        
        handler = self.handlers.get(intent)
        
        if not handler:
            logger.warning(f"No handler found for intent: {intent}")
            return {
                "message": f"Handler not implemented for intent: {intent.value}",
                "parameters_used": parameters,
                "performance_met": False,
                "error": f"Unsupported intent: {intent.value}"
            }
        
        try:
            result = await handler(parameters, db, current_user)
            return result
            
        except Exception as e:
            logger.error(
                f"Handler execution failed for intent: {intent}",
                error=str(e),
                parameters=parameters,
                exc_info=True
            )
            return {
                "message": f"Handler execution failed for {intent.value}",
                "parameters_used": parameters,
                "performance_met": False,
                "error": str(e)
            }


# Initialize the service
ai_service = AIAssistantService()


@router.post("/query", response_model=NaturalLanguageQueryResponse)
async def process_natural_language_query(
    query_request: NaturalLanguageQueryRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Process a natural language query and return intent classification with parameters.
    
    This endpoint analyzes the user's natural language input and determines:
    1. What the user wants to do (intent)
    2. What parameters are needed (extracted from the query)
    3. Confidence level in the classification
    
    Note: This endpoint only classifies intent - use /execute to actually run the query.
    """
    trace_context = get_current_trace_context()
    
    try:
        # TODO: Get current user from authentication
        # For now, using a dummy user - in production this would come from auth middleware
        current_user = User(
            id=1,
            email="test@example.com",
            organization_id=1
        )
        
        logger.info(
            "Processing natural language query for classification",
            query=query_request.query,
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )
        
        # Step 1: Classify intent
        classification_result = await ai_service.intent_classifier.classify_intent(query_request.query)
        
        # Step 2: Extract parameters
        parameters = await ai_service.parameter_extractor.extract_parameters(
            query_request.query, classification_result.intent
        )
        
        # Determine if confidence threshold is met (>0.8)
        confidence_threshold_met = classification_result.confidence >= 0.8
        
        # Prepare response
        response_data = {
            "query_id": f"query_{current_user.id}_{hash(query_request.query) % 10000}",
            "original_query": query_request.query,
            "intent": classification_result.intent.value,
            "confidence": classification_result.confidence,
            "parameters": parameters,
            "confidence_threshold_met": confidence_threshold_met,
            "reasoning": classification_result.reasoning,
            "suggested_actions": [],
            "error_message": None
        }
        
        # Add error message if confidence is low
        if not confidence_threshold_met:
            response_data["error_message"] = "Low confidence in intent recognition. Please rephrase your query."
        else:
            # Add suggested actions based on intent
            response_data["suggested_actions"] = [
                f"Execute {classification_result.intent.value.lower().replace('_', ' ')}",
                "Refine parameters if needed",
                "Use /execute endpoint to run the query"
            ]
        
        logger.info(
            "Query classification completed",
            intent=classification_result.intent.value,
            confidence=classification_result.confidence,
            confidence_threshold_met=confidence_threshold_met
        )
        
        return response_data
        
    except Exception as e:
        logger.error(
            "AI query classification failed",
            query=query_request.query,
            error=str(e),
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query classification failed: {str(e)}"
        )


@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_ai_query(
    query_request: NaturalLanguageQueryRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Execute a natural language query using the AI Assistant.
    
    This endpoint processes natural language queries and returns structured responses
    for contract and supplier management operations.
    """
    trace_context = get_current_trace_context()
    start_time = time.time()
    
    try:
        # TODO: Get current user from authentication
        # For now, using a dummy user - in production this would come from auth middleware
        current_user = User(
            id=1,
            email="test@example.com",
            organization_id=1
        )
        
        # Process the query
        result = await ai_service.process_query(
            query=query_request.query,
            db=db,
            current_user=current_user
        )
        
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Format response according to ToolExecutionResponse schema
        tool_response = ToolExecutionResponse(
            tool_name=result.get("intent", "unknown"),
            result=result,
            execution_time_ms=execution_time_ms,
            performance_met=result.get("success", False),
            error_message=result.get("error") if not result.get("success", False) else None
        )
        
        return tool_response
        
    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        
        logger.error(
            "AI query execution failed",
            query=query_request.query,
            error=str(e),
            **trace_context,
            exc_info=True
        )
        
        # Return error response in the correct format
        return ToolExecutionResponse(
            tool_name="error",
            result={"error": str(e), "query": query_request.query},
            execution_time_ms=execution_time_ms,
            performance_met=False,
            error_message=str(e)
        )


@router.get("/health")
async def ai_assistant_health():
    """Health check endpoint for AI Assistant service"""
    return {
        "status": "healthy",
        "service": "ai-assistant",
        "handlers_loaded": len(ai_service.handlers),
        "available_intents": [intent.value for intent in ai_service.handlers.keys()],
        "registered_tools": len(default_tool_registry.list_tools()),
    }


@router.get("/intents")
async def get_available_intents():
    """Get list of available intents and their descriptions"""
    return {
        "available_intents": [
            {
                "intent": intent.value,
                "description": ai_service.intent_classifier.tools.get(intent.value, {}).get("description", "No description available")
            }
            for intent in IntentType if intent != IntentType.UNKNOWN
        ]
    }


@router.get("/tools")
async def list_registered_tools():
    """List tools registered in the assistant tooling registry"""
    tools = default_tool_registry.list_tools()
    return {
        "tools": [
            {
                "name": spec.name,
                "description": spec.description,
                "category": spec.category,
                "required_scopes": spec.required_scopes,
                "timeout_seconds": spec.timeout_seconds,
            }
            for spec in tools.values()
        ],
        "total_tools": len(tools),
    }
