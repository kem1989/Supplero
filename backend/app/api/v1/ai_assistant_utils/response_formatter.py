"""
Response formatting utilities for AI Assistant.
Simplified for SQL-based natural language query processing.
"""

import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime

from .intent_classifier import IntentType

logger = structlog.get_logger(__name__)


class ResponseFormatter:
    """Handles formatting of AI Assistant responses for different intents"""
    
    @staticmethod
    def format_response(
        intent: IntentType,
        execution_result: Dict[str, Any],
        query: str,
        processing_time_ms: float
    ) -> Dict[str, Any]:
        """
        Format the final response based on intent and execution result.
        
        Args:
            intent: The classified intent
            execution_result: Result from the execution handler
            query: Original user query
            processing_time_ms: Time taken to process the query
            
        Returns:
            Formatted response dictionary
        """
        
        base_response = {
            "query": query,
            "intent": intent.value,
            "processing_time_ms": round(processing_time_ms, 2),
            "timestamp": datetime.utcnow().isoformat(),
            "success": execution_result.get("performance_met", False)
        }
        
        # Add execution result data
        base_response.update(execution_result)
        
        # Simplified formatting - return base response for all SQL-based intents
        return base_response
    
    @staticmethod
    def add_helpful_suggestions(
        response: Dict[str, Any],
        intent: IntentType
    ) -> Dict[str, Any]:
        """Add helpful suggestions for follow-up queries"""
        
        suggestions = []
        
        if intent == IntentType.SQL_QUERY:
            suggestions = [
                "Analyze risk for these suppliers",
                "Compare top suppliers",
                "Get insights on supplier portfolio"
            ]
        
        elif intent == IntentType.SQL_ANALYTICS:
            suggestions = [
                "Get trend analysis",
                "Compare time periods",
                "Generate detailed reports"
            ]
        
        elif intent == IntentType.COMPARISON_QUERY:
            suggestions = [
                "Compare more suppliers",
                "Analyze differences",
                "Get benchmarking insights"
            ]
        
        else:
            suggestions = [
                "Ask for more specific information",
                "Refine your search criteria",
                "Try a different query approach"
            ]
        
        if suggestions:
            response["helpful_suggestions"] = suggestions
        
        return response