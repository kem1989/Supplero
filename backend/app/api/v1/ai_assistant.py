"""
AI Assistant API endpoints for natural language query processing.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.ai_assistant import AIAssistantService, QueryIntent, IntentType
from app.core.logging import get_logger
from app.models.user import User

logger = get_logger(__name__)

router = APIRouter(prefix="/ai-assistant", tags=["ai-assistant"])


# Request/Response models
class NaturalLanguageQueryRequest(BaseModel):
    """Request model for natural language queries"""
    query: str = "Find contracts with supplier ABC Corp"
    user_context: Optional[Dict[str, Any]] = None


class NaturalLanguageQueryResponse(BaseModel):
    """Response model for natural language query processing"""
    query_id: str
    original_query: str
    intent: str
    confidence: float
    parameters: Dict[str, Any]
    confidence_threshold_met: bool
    suggested_actions: list
    error_message: Optional[str] = None


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution"""
    query_id: str
    original_query: str
    intent: str
    confidence: float
    tool_executed: str
    execution_result: Dict[str, Any]
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None


class AvailableToolsResponse(BaseModel):
    """Response model for available tools"""
    tools: Dict[str, Dict[str, Any]]
    total_tools: int
    user_role: str
    organization_id: int


@router.post("/query", response_model=NaturalLanguageQueryResponse)
async def process_natural_language_query(
    request: NaturalLanguageQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process a natural language query and return intent classification with parameters.
    
    This endpoint analyzes the user's natural language input and determines:
    1. What the user wants to do (intent)
    2. What parameters are needed (extracted from the query)
    3. Confidence level in the classification
    """
    try:
        logger.info(
            "Processing natural language query",
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            query=request.query
        )
        
        # Initialize AI assistant service
        ai_service = AIAssistantService()
        
        # Process the query
        query_intent = await ai_service.process_query(
            query=request.query,
            user_context={
                "user_id": current_user.id,
                "organization_id": current_user.organization_id,
                "role": current_user.role
            }
        )
        
        # Validate confidence threshold (>90%)
        confidence_met = ai_service.validate_intent_confidence(query_intent)
        
        # Prepare response
        response = NaturalLanguageQueryResponse(
            query_id=f"query_{current_user.id}_{hash(request.query) % 10000}",
            original_query=request.query,
            intent=query_intent.intent.value,
            confidence=query_intent.confidence,
            parameters=query_intent.parameters,
            confidence_threshold_met=confidence_met,
            suggested_actions=[],
            error_message=None
        )
        
        # Add suggested actions based on intent
        if confidence_met:
            response.suggested_actions = _get_suggested_actions(query_intent.intent)
        else:
            response.error_message = "Low confidence in intent recognition. Please rephrase your query."
        
        logger.info(
            "Query processed successfully",
            query_id=response.query_id,
            intent=response.intent,
            confidence=response.confidence,
            confidence_threshold_met=confidence_met
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to process natural language query",
            user_id=current_user.id,
            query=request.query,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool_for_intent(
    request: NaturalLanguageQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute the appropriate tool based on the identified intent.
    
    This endpoint:
    1. Processes the natural language query
    2. Identifies the intent and parameters
    3. Executes the corresponding tool
    4. Returns the results
    """
    try:
        logger.info(
            "Executing tool for natural language query",
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            query=request.query
        )
        
        # Initialize AI assistant service
        ai_service = AIAssistantService()
        
        # Process the query to get intent and parameters
        query_intent = await ai_service.process_query(
            query=request.query,
            user_context={
                "user_id": current_user.id,
                "organization_id": current_user.organization_id,
                "role": current_user.role
            }
        )
        
        # Validate confidence threshold
        if not ai_service.validate_intent_confidence(query_intent):
            raise HTTPException(
                status_code=400,
                detail=f"Low confidence in intent recognition ({query_intent.confidence:.2f}). Please rephrase your query."
            )
        
        # Execute the appropriate tool based on intent
        execution_result = await _execute_tool_for_intent(
            query_intent=query_intent,
            db=db,
            current_user=current_user
        )
        
        logger.info(
            "Tool executed successfully",
            intent=query_intent.intent.value,
            tool_executed=execution_result.get("tool_name"),
            execution_time_ms=execution_result.get("execution_time_ms")
        )
        
        return ToolExecutionResponse(
            query_id=f"exec_{current_user.id}_{hash(request.query) % 10000}",
            original_query=request.query,
            intent=query_intent.intent.value,
            confidence=query_intent.confidence,
            tool_executed=execution_result.get("tool_name"),
            execution_result=execution_result.get("result"),
            execution_time_ms=execution_result.get("execution_time_ms"),
            success=True,
            error_message=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to execute tool for query",
            user_id=current_user.id,
            query=request.query,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute tool: {str(e)}"
        )


@router.get("/tools", response_model=AvailableToolsResponse)
async def get_available_tools(
    current_user: User = Depends(get_current_user)
):
    """
    Get information about available tools and their capabilities.
    
    This endpoint provides:
    1. List of available tools
    2. Tool descriptions and parameters
    3. Example queries for each tool
    """
    try:
        ai_service = AIAssistantService()
        tools = ai_service.get_available_tools()
        
        return AvailableToolsResponse(
            tools=tools,
            total_tools=len(tools),
            user_role=current_user.role,
            organization_id=current_user.organization_id
        )
        
    except Exception as e:
        logger.error(
            "Failed to get available tools",
            user_id=current_user.id,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available tools: {str(e)}"
        )


@router.post("/search-contracts")
async def search_contracts(
    request: NaturalLanguageQueryRequest,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("relevance", regex="^(relevance|date|amount)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dedicated endpoint for contract search with natural language queries.
    
    This endpoint:
    1. Processes natural language queries for contract search
    2. Uses the Elasticsearch service for fast (<500ms) search
    3. Returns AI-generated insights along with search results
    """
    try:
        logger.info(
            "Processing contract search request",
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            query=request.query,
            page=page,
            page_size=page_size
        )
        
        # Initialize AI assistant service
        ai_service = AIAssistantService()
        
        # Process the query to extract intent and parameters
        query_intent = await ai_service.process_query(
            query=request.query,
            user_context={
                "user_id": current_user.id,
                "organization_id": current_user.organization_id,
                "role": current_user.role
            }
        )
        
        # Validate that this is a search intent
        if query_intent.intent != IntentType.SEARCH_CONTRACTS:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Query is not a contract search request",
                    "detected_intent": query_intent.intent.value,
                    "suggested_action": "Use a search-related query like 'Find contracts with supplier ABC Corp'"
                }
            )
        
        # Extract search parameters
        filters = {
            "supplier": query_intent.parameters.get("supplier"),
            "amount_min": query_intent.parameters.get("amount_min"),
            "amount_max": query_intent.parameters.get("amount_max"),
            "date_from": query_intent.parameters.get("date_from"),
            "date_to": query_intent.parameters.get("date_to"),
            "contract_type": query_intent.parameters.get("contract_type"),
            "tags": query_intent.parameters.get("tags"),
            "organization_id": current_user.organization_id
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Execute search
        search_result = await ai_service.search_contracts(
            query=request.query,
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by
        )
        
        # Add query processing metadata
        search_result["query_processing"] = {
            "intent": query_intent.intent.value,
            "confidence": query_intent.confidence,
            "extracted_parameters": query_intent.parameters,
            "confidence_threshold_met": query_intent.confidence >= 0.9
        }
        
        logger.info(
            "Contract search completed successfully",
            user_id=current_user.id,
            query=request.query,
            results_count=search_result.get("total_count", 0),
            search_time_ms=search_result.get("search_time_ms", 0),
            performance_met=search_result.get("performance_met", False)
        )
        
        return search_result
        
    except Exception as e:
        logger.error(
            "Contract search failed",
            user_id=current_user.id,
            query=request.query,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Contract search failed: {str(e)}"
        )


async def _execute_tool_for_intent(
    query_intent: QueryIntent,
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """
    Execute the appropriate tool based on the identified intent.
    
    Args:
        query_intent: The processed query intent
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dictionary containing execution results
    """
    import time
    start_time = time.time()
    
    try:
        if query_intent.intent == IntentType.SEARCH_CONTRACTS:
            result = await _execute_search_contracts(
                parameters=query_intent.parameters,
                db=db,
                current_user=current_user
            )
            tool_name = "SEARCH_CONTRACTS"
            
        elif query_intent.intent == IntentType.GET_DETAILS:
            result = await _execute_get_details(
                parameters=query_intent.parameters,
                db=db,
                current_user=current_user
            )
            tool_name = "GET_DETAILS"
            
        elif query_intent.intent == IntentType.EXPORT:
            result = await _execute_export(
                parameters=query_intent.parameters,
                db=db,
                current_user=current_user
            )
            tool_name = "EXPORT"
            
        else:
            raise ValueError(f"Unknown intent: {query_intent.intent}")
        
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return {
            "tool_name": tool_name,
            "result": result,
            "execution_time_ms": round(execution_time, 2)
        }
        
    except Exception as e:
        logger.error(
            "Tool execution failed",
            intent=query_intent.intent.value,
            parameters=query_intent.parameters,
            error=str(e)
        )
        raise


async def _execute_search_contracts(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute contract search based on extracted parameters"""
    try:
        # Initialize AI assistant service
        ai_service = AIAssistantService()
        
        # Extract search parameters
        query = parameters.get("query", "")
        filters = {
            "supplier": parameters.get("supplier"),
            "amount_min": parameters.get("amount_min"),
            "amount_max": parameters.get("amount_max"),
            "date_from": parameters.get("date_from"),
            "date_to": parameters.get("date_to"),
            "contract_type": parameters.get("contract_type"),
            "tags": parameters.get("tags"),
            "organization_id": current_user.organization_id
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Execute search using AI assistant service
        search_result = await ai_service.search_contracts(
            query=query,
            filters=filters,
            page=1,
            page_size=20,
            sort_by="relevance"
        )
        
        return {
            "message": "Contract search executed successfully",
            "parameters_used": parameters,
            "search_results": search_result,
            "search_criteria": filters,
            "performance_met": search_result.get("performance_met", False)
        }
        
    except Exception as e:
        logger.error("Contract search execution failed", error=str(e))
        return {
            "message": "Contract search failed",
            "parameters_used": parameters,
            "error": str(e),
            "search_results": {
                "documents": [],
                "total_count": 0,
                "search_time_ms": 0
            },
            "performance_met": False
        }


async def _execute_get_details(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute document details retrieval based on extracted parameters"""
    # TODO: Implement actual document details retrieval
    # For now, return mock data
    return {
        "message": "Document details retrieved",
        "parameters_used": parameters,
        "document_info": {
            "id": parameters.get("document_id", "unknown"),
            "status": "processed"
        }
    }


async def _execute_export(
    parameters: Dict[str, Any],
    db: Session,
    current_user: User
) -> Dict[str, Any]:
    """Execute data export based on extracted parameters"""
    # TODO: Implement actual export logic
    # For now, return mock data
    return {
        "message": "Export executed",
        "parameters_used": parameters,
        "export_format": parameters.get("format", "csv"),
        "export_status": "completed"
    }


def _get_suggested_actions(intent: IntentType) -> list:
    """Get suggested actions based on the identified intent"""
    if intent == IntentType.SEARCH_CONTRACTS:
        return [
            "Execute search with extracted parameters",
            "Modify search criteria if needed",
            "View search results"
        ]
    elif intent == IntentType.GET_DETAILS:
        return [
            "View document details",
            "Download document if available",
            "View extracted metadata"
        ]
    elif intent == IntentType.EXPORT:
        return [
            "Download exported file",
            "View export summary",
            "Schedule recurring export"
        ]
    else:
        return ["Please rephrase your query"]
