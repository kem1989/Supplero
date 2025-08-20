"""
Base handler utilities and common functionality for AI Assistant execution handlers.
"""

import structlog
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User

logger = structlog.get_logger(__name__)


class BaseHandler:
    """Base class for AI Assistant execution handlers with common utilities."""
    
    @staticmethod
    def create_error_response(
        message: str,
        parameters: Dict[str, Any],
        error: str,
        additional_fields: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a standardized error response."""
        response = {
            "message": message,
            "parameters_used": parameters,
            "error": error,
            "performance_met": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if additional_fields:
            response.update(additional_fields)
            
        return response
    
    @staticmethod
    def create_success_response(
        message: str,
        parameters: Dict[str, Any],
        data: Dict[str, Any],
        performance_met: bool = True
    ) -> Dict[str, Any]:
        """Create a standardized success response."""
        return {
            "message": message,
            "parameters_used": parameters,
            "performance_met": performance_met,
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }
    
    @staticmethod
    def log_execution_start(
        handler_name: str,
        parameters: Dict[str, Any],
        user_id: int,
        organization_id: int
    ):
        """Log the start of handler execution."""
        logger.info(
            f"Executing {handler_name}",
            handler=handler_name,
            user_id=user_id,
            organization_id=organization_id,
            parameters=parameters
        )
    
    @staticmethod
    def log_execution_error(
        handler_name: str,
        error: Exception,
        parameters: Dict[str, Any]
    ):
        """Log handler execution errors."""
        logger.error(
            f"Failed to execute {handler_name}",
            handler=handler_name,
            error=str(error),
            parameters=parameters,
            exc_info=True
        )
    
    @staticmethod
    def validate_required_parameters(
        parameters: Dict[str, Any],
        required_params: List[str]
    ) -> List[str]:
        """Validate that required parameters are present."""
        missing_params = []
        for param in required_params:
            if param not in parameters or parameters[param] is None:
                missing_params.append(param)
        return missing_params
    
    @staticmethod
    def sanitize_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parameters for logging and processing."""
        # Remove sensitive information if any
        sanitized = parameters.copy()
        
        # Add any sanitization logic here
        # For example, removing passwords, tokens, etc.
        
        return sanitized
