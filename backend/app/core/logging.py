"""
Structured logging configuration for the Supplero application.
Enhanced for comprehensive observability and audit baseline.
"""

import sys
import uuid
import time
import structlog
from typing import Any, Dict, Optional
from contextvars import ContextVar
from app.core.config import settings

# Context variables for request correlation
REQUEST_ID: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
USER_ID: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
CORRELATION_ID: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
SPAN_ID: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
PARENT_SPAN_ID: ContextVar[Optional[str]] = ContextVar("parent_span_id", default=None)


def setup_logging():
    """Configure structured logging for the application."""
    
    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        # Add context variables to all log entries
        add_context_variables,
        structlog.processors.JSONRenderer()
    ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    import logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper())
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)
    
    # Create logger instance
    logger = structlog.get_logger()
    logger.info("Logging configured successfully", log_level=settings.LOG_LEVEL)


def add_context_variables(logger, method_name, event_dict):
    """Add context variables to all log entries."""
    # Add request correlation IDs if available
    if REQUEST_ID.get():
        event_dict["request_id"] = REQUEST_ID.get()
    if USER_ID.get():
        event_dict["user_id"] = USER_ID.get()
    if CORRELATION_ID.get():
        event_dict["correlation_id"] = CORRELATION_ID.get()
    if SPAN_ID.get():
        event_dict["span_id"] = SPAN_ID.get()
    if PARENT_SPAN_ID.get():
        event_dict["parent_span_id"] = PARENT_SPAN_ID.get()
    
    # Add service information
    event_dict["service"] = "supplero-api"
    event_dict["environment"] = settings.ENVIRONMENT
    
    return event_dict


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def generate_trace_id() -> str:
    """Generate a unique trace ID for request correlation."""
    return f"trace_{uuid.uuid4().hex[:16]}"


def generate_span_id() -> str:
    """Generate a unique span ID for distributed tracing."""
    return f"span_{uuid.uuid4().hex[:8]}"


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for complex request chains."""
    return f"corr_{uuid.uuid4().hex[:12]}"


def set_request_context(
    request_id: str, 
    user_id: str = None, 
    correlation_id: str = None,
    span_id: str = None,
    parent_span_id: str = None
):
    """Set request context variables for logging."""
    REQUEST_ID.set(request_id)
    if user_id:
        USER_ID.set(user_id)
    if correlation_id:
        CORRELATION_ID.set(correlation_id)
    if span_id:
        SPAN_ID.set(span_id)
    if parent_span_id:
        PARENT_SPAN_ID.set(parent_span_id)


def clear_request_context():
    """Clear request context variables."""
    REQUEST_ID.set(None)
    USER_ID.set(None)
    CORRELATION_ID.set(None)
    SPAN_ID.set(None)
    PARENT_SPAN_ID.set(None)


def get_current_trace_context() -> Dict[str, Optional[str]]:
    """Get current trace context for propagation."""
    return {
        "request_id": REQUEST_ID.get(),
        "correlation_id": CORRELATION_ID.get(),
        "span_id": SPAN_ID.get(),
        "parent_span_id": PARENT_SPAN_ID.get(),
        "user_id": USER_ID.get()
    }


def log_request_context(request_id: str, user_id: str = None, **kwargs) -> Dict[str, Any]:
    """Create a context dictionary for request logging."""
    context = {
        "request_id": request_id,
        "timestamp": time.time(),
        "service": "supplero-api",
        "environment": settings.ENVIRONMENT,
    }
    
    if user_id:
        context["user_id"] = user_id
    
    context.update(kwargs)
    return context


def log_ai_request(
    request_id: str,
    model: str,
    prompt_length: int,
    user_id: str = None,
    **kwargs
) -> Dict[str, Any]:
    """Create a context dictionary for AI request logging."""
    return log_request_context(
        request_id=request_id,
        user_id=user_id,
        ai_model=model,
        prompt_length=prompt_length,
        **kwargs
    )


def log_ai_response(
    request_id: str,
    model: str,
    response_length: int,
    processing_time: float,
    user_id: str = None,
    **kwargs
) -> Dict[str, Any]:
    """Create a context dictionary for AI response logging."""
    return log_request_context(
        request_id=request_id,
        user_id=user_id,
        ai_model=model,
        response_length=response_length,
        processing_time=processing_time,
        **kwargs
    )


def log_database_operation(
    operation: str,
    table: str,
    record_id: str = None,
    user_id: str = None,
    **kwargs
) -> Dict[str, Any]:
    """Create a context dictionary for database operation logging."""
    context = {
        "operation": operation,
        "table": table,
        "timestamp": time.time(),
        "service": "supplero-api",
        "environment": settings.ENVIRONMENT,
    }
    
    if record_id:
        context["record_id"] = record_id
    if user_id:
        context["user_id"] = user_id
    
    context.update(kwargs)
    return context


def log_integration_call(
    integration_name: str,
    endpoint: str,
    status_code: int,
    response_time: float,
    user_id: str = None,
    **kwargs
) -> Dict[str, Any]:
    """Create a context dictionary for external integration logging."""
    context = {
        "integration": integration_name,
        "endpoint": endpoint,
        "status_code": status_code,
        "response_time": response_time,
        "timestamp": time.time(),
        "service": "supplero-api",
        "environment": settings.ENVIRONMENT,
    }
    
    if user_id:
        context["user_id"] = user_id
    
    context.update(kwargs)
    return context


def log_security_event(
    event_type: str,
    severity: str,
    user_id: str = None,
    ip_address: str = None,
    **kwargs
) -> Dict[str, Any]:
    """Create a context dictionary for security event logging."""
    context = {
        "event_type": event_type,
        "severity": severity,
        "timestamp": time.time(),
        "service": "supplero-api",
        "environment": settings.ENVIRONMENT,
    }
    
    if user_id:
        context["user_id"] = user_id
    if ip_address:
        context["ip_address"] = ip_address
    
    context.update(kwargs)
    return context


def log_trace_event(
    event_type: str,
    trace_id: str,
    span_id: str = None,
    parent_span_id: str = None,
    **kwargs
) -> Dict[str, Any]:
    """Create a context dictionary for trace event logging."""
    context = {
        "event_type": event_type,
        "trace_id": trace_id,
        "timestamp": time.time(),
        "service": "supplero-api",
        "environment": settings.ENVIRONMENT,
    }
    
    if span_id:
        context["span_id"] = span_id
    if parent_span_id:
        context["parent_span_id"] = parent_span_id
    
    context.update(kwargs)
    return context 