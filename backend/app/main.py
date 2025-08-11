"""
Main FastAPI application entry point for Supplero AI-Powered Procurement Platform.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import (
    setup_logging, get_logger, generate_trace_id, generate_span_id, 
    generate_correlation_id, set_request_context, clear_request_context,
    log_trace_event
)
from app.core.auth import extract_user_from_token
from app.api.v1.api import api_router
from app.core.database import init_db

# Setup structured logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Supplero API server")
    await init_db()
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Supplero API server")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Supplero AI-Powered Procurement Platform",
        description="Enterprise-grade AI platform for intelligent procurement and supplier risk management",
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
        lifespan=lifespan
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Extract or generate trace IDs for request correlation
        trace_id = request.headers.get("X-Trace-ID") or generate_trace_id()
        correlation_id = request.headers.get("X-Correlation-ID") or generate_correlation_id()
        parent_span_id = request.headers.get("X-Parent-Span-ID")
        span_id = generate_span_id()
        
        # Extract user ID from JWT token if available
        user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            user_id = extract_user_from_token(token)
        
        # Set request context for structured logging
        set_request_context(
            request_id=trace_id, 
            user_id=user_id, 
            correlation_id=correlation_id,
            span_id=span_id,
            parent_span_id=parent_span_id
        )
        
        # Log trace event start
        log_trace_event(
            event_type="request_start",
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id
        )
        
        # Log request start
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            content_length=request.headers.get("content-length"),
            content_type=request.headers.get("content-type"),
            trace_id=trace_id,
            correlation_id=correlation_id,
            span_id=span_id,
            parent_span_id=parent_span_id
        )
        
        try:
            response = await call_next(request)
            
            # Log successful response
            process_time = time.time() - start_time
            logger.info(
                "Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=process_time,
                response_size=response.headers.get("content-length"),
                trace_id=trace_id,
                correlation_id=correlation_id,
                span_id=span_id
            )
            
            # Log trace event completion
            log_trace_event(
                event_type="request_complete",
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                status_code=response.status_code,
                process_time=process_time
            )
            
        except Exception as exc:
            # Log error response
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                method=request.method,
                url=str(request.url),
                error=str(exc),
                process_time=process_time,
                trace_id=trace_id,
                correlation_id=correlation_id,
                span_id=span_id,
                exc_info=True
            )
            
            # Log trace event failure
            log_trace_event(
                event_type="request_failed",
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                error=str(exc),
                process_time=process_time
            )
            raise
        finally:
            # Clear request context
            clear_request_context()
        
        # Add trace correlation headers to response
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Span-ID"] = span_id
        
        return response
    
    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # Get trace context from headers
        trace_id = request.headers.get("X-Trace-ID", "unknown")
        correlation_id = request.headers.get("X-Correlation-ID", "unknown")
        span_id = request.headers.get("X-Span-ID", "unknown")
        
        logger.error(
            "Unhandled exception",
            method=request.method,
            url=str(request.url),
            error=str(exc),
            trace_id=trace_id,
            correlation_id=correlation_id,
            span_id=span_id,
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "trace_id": trace_id,
                "correlation_id": correlation_id,
                "span_id": span_id
            }
        )
    
    # Include API routes
    app.include_router(api_router, prefix=settings.API_PREFIX)
    
    # Include health check routes
    from app.api.health import router as health_router
    app.include_router(health_router, tags=["health"])
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to Supplero AI-Powered Procurement Platform",
            "version": "1.0.0",
            "docs": "/docs" if settings.ENVIRONMENT == "development" else None
        }
    
    return app


# Create the application instance
app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 