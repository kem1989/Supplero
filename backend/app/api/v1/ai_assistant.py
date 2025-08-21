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
from app.models.user import User
from app.schemas.ai_assistant import NaturalLanguageQueryRequest, NaturalLanguageQueryResponse, ToolExecutionResponse

# Import the new modular components
from .ai_assistant_utils.intent_classifier import IntentClassifier, IntentType
from .ai_assistant_utils.parameter_extractor import ParameterExtractor
from .ai_assistant_utils.response_formatter import ResponseFormatter

# Import handlers
from .handlers.contract_handlers import (
    execute_search_contracts,
    execute_get_details,
    execute_export,
    execute_search_clauses,
    execute_analyze_risk,
    execute_compare_clauses
)
from .handlers.supplier_handlers import (
    execute_search_suppliers,
    execute_analyze_supplier_risk,
    execute_compare_suppliers,
    execute_supplier_insights
)
from .handlers.cross_system_handlers import (
    execute_suppliers_with_risky_contracts,
    execute_suppliers_with_expiring_contracts,
    execute_suppliers_by_contract_clauses,
    execute_contracts_by_supplier_risk,
    execute_unified_risk_search,
    execute_suppliers_by_contract_value,
    execute_suppliers_with_contract_criteria,
    execute_supplier_contract_portfolio,
    execute_suppliers_by_semantic_contracts
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/ai-assistant", tags=["ai-assistant"])


class AIAssistantService:
    """Main AI Assistant service with modular architecture"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.parameter_extractor = ParameterExtractor()
        self.response_formatter = ResponseFormatter()
        
        # Handler mapping
        self.handlers = {
            IntentType.SEARCH_CONTRACTS: execute_search_contracts,
            IntentType.GET_DETAILS: execute_get_details,
            IntentType.EXPORT: execute_export,
            IntentType.SEARCH_CLAUSES: execute_search_clauses,
            IntentType.ANALYZE_RISK: execute_analyze_risk,
            IntentType.COMPARE_CLAUSES: execute_compare_clauses,
            
            IntentType.SEARCH_SUPPLIERS: execute_search_suppliers,
            IntentType.ANALYZE_SUPPLIER_RISK: execute_analyze_supplier_risk,
            IntentType.COMPARE_SUPPLIERS: execute_compare_suppliers,
            IntentType.SUPPLIER_INSIGHTS: execute_supplier_insights,
            
            IntentType.SUPPLIERS_WITH_RISKY_CONTRACTS: execute_suppliers_with_risky_contracts,
            IntentType.SUPPLIERS_WITH_EXPIRING_CONTRACTS: execute_suppliers_with_expiring_contracts,
            IntentType.SUPPLIERS_BY_CONTRACT_CLAUSES: execute_suppliers_by_contract_clauses,
            IntentType.CONTRACTS_BY_SUPPLIER_RISK: execute_contracts_by_supplier_risk,
            IntentType.UNIFIED_RISK_SEARCH: execute_unified_risk_search,
            IntentType.SUPPLIERS_BY_SEMANTIC_CONTRACTS: execute_suppliers_by_semantic_contracts,
            
            # NEW: Enhanced supplier-contract relationship handlers
            IntentType.SUPPLIERS_BY_CONTRACT_VALUE: execute_suppliers_by_contract_value,
            IntentType.SUPPLIERS_WITH_CONTRACT_CRITERIA: execute_suppliers_with_contract_criteria,
            IntentType.CONTRACTS_BY_SUPPLIER_CRITERIA: execute_suppliers_with_contract_criteria,  # Reuse handler
            IntentType.SUPPLIER_CONTRACT_PORTFOLIO: execute_supplier_contract_portfolio
        }
    
    async def process_query(
        self,
        query: str,
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """
        Process a natural language query through the complete AI pipeline.
        
        Args:
            query: Natural language query from user
            db: Database session
            current_user: Current authenticated user
            
        Returns:
            Formatted response dictionary
        """
        start_time = time.time()
        
        try:
            logger.info(
                "Processing AI assistant query",
                query=query,
                user_id=current_user.id,
                organization_id=current_user.organization_id
            )
            
            # Step 1: Classify intent
            classification_result = await self.intent_classifier.classify_intent(query)
            
            logger.info(
                "Intent classified",
                intent=classification_result.intent.value,
                confidence=classification_result.confidence,
                reasoning=classification_result.reasoning
            )
            
            # Step 2: Extract parameters
            parameters = await self.parameter_extractor.extract_parameters(
                query, classification_result.intent
            )
            
            logger.info(
                "Parameters extracted",
                parameters=parameters,
                intent=classification_result.intent.value
            )
            
            # Step 3: Execute appropriate handler
            # Add original query to parameters for RAG semantic search
            parameters["query"] = query
            execution_result = await self._execute_handler(
                classification_result.intent,
                parameters,
                db,
                current_user
            )
            
            # Step 4: Format response
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
            
            logger.info(
                "Query processed successfully",
                intent=classification_result.intent.value,
                processing_time_ms=processing_time_ms,
                success=formatted_response.get("success", False)
            )
            
            return formatted_response
            
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            
            logger.error(
                "Failed to process AI assistant query",
                query=query,
                error=str(e),
                processing_time_ms=processing_time_ms,
                exc_info=True
            )
            
            return {
                "query": query,
                "intent": "UNKNOWN",
                "success": False,
                "error": str(e),
                "message": "Failed to process query",
                "processing_time_ms": processing_time_ms,
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
        "available_intents": [intent.value for intent in ai_service.handlers.keys()]
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
