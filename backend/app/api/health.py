"""
Health check endpoints for the Supplero application.
Enhanced with structured logging for observability.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import httpx
from typing import Dict, Any
import time

from app.core.database import get_db, check_db_health
# Redis client removed for simplification
from app.core.config import settings
from app.core.logging import get_logger, get_current_trace_context

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health")
async def health_check(request: Request) -> Dict[str, Any]:
    """Health check endpoint for the application."""
    # Get current trace context
    trace_context = get_current_trace_context()
    
    logger.debug("Basic health check requested", **trace_context)
    return {
        "status": "healthy",
        "service": "supplero-backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "trace_id": trace_context.get("request_id"),
        "correlation_id": trace_context.get("correlation_id")
    }


@router.get("/health/detailed")
async def detailed_health_check(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Detailed health check including database and external service status."""
    start_time = time.time()
    
    # Get current trace context
    trace_context = get_current_trace_context()
    
    health_status = {
        "status": "healthy",
        "service": "supplero-backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
        "trace_id": trace_context.get("request_id"),
        "correlation_id": trace_context.get("correlation_id"),
        "span_id": trace_context.get("span_id"),
        "checks": {
            "database": "unknown",
            "redis": "unknown",
            "elasticsearch": "unknown"
        }
    }
    
    # Check database connection
    try:
        db_check_start = time.time()
        db.execute("SELECT 1")
        db_check_time = time.time() - db_check_start
        
        health_status["checks"]["database"] = "healthy"
        logger.debug(
            "Database health check successful", 
            response_time=db_check_time,
            **trace_context
        )
        
    except Exception as e:
        db_check_time = time.time() - db_check_start
        logger.error(
            "Database health check failed",
            error=str(e),
            response_time=db_check_time,
            **trace_context,
            exc_info=True
        )
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Redis connection
    try:
        redis_check_start = time.time()
        redis_status = {"status": "disabled", "message": "Redis removed for simplification"}
        redis_check_time = time.time() - redis_check_start
        
        health_status["checks"]["redis"] = redis_status["status"]
        if redis_status["status"] == "unhealthy":
            health_status["status"] = "degraded"
            
        logger.debug(
            "Redis health check completed", 
            status=redis_status["status"], 
            response_time=redis_check_time,
            **trace_context
        )
        
    except Exception as e:
        redis_check_time = time.time() - redis_check_start
        logger.error(
            "Redis health check failed",
            error=str(e),
            response_time=redis_check_time,
            **trace_context,
            exc_info=True
        )
        health_status["checks"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Elasticsearch connection
    try:
        es_check_start = time.time()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.ELASTICSEARCH_URL}/_cluster/health",
                timeout=5.0
            )
            es_check_time = time.time() - es_check_start
            
            if response.status_code == 200:
                health_status["checks"]["elasticsearch"] = "healthy"
                logger.debug(
                    "Elasticsearch health check successful", 
                    response_time=es_check_time,
                    status_code=response.status_code,
                    **trace_context
                )
            else:
                health_status["checks"]["elasticsearch"] = "unhealthy"
                health_status["status"] = "degraded"
                logger.warning(
                    "Elasticsearch health check failed", 
                    response_time=es_check_time,
                    status_code=response.status_code,
                    **trace_context
                )
                                
    except Exception as e:
        es_check_time = time.time() - es_check_start
        logger.error(
            "Elasticsearch health check failed",
            error=str(e),
            response_time=es_check_time,
            **trace_context,
            exc_info=True
        )
        health_status["checks"]["elasticsearch"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Determine overall status
    if any(check == "unhealthy" for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"
    
    total_time = time.time() - start_time
    health_status["total_check_time"] = total_time
    
    logger.info(
        "Detailed health check completed",
        overall_status=health_status["status"],
        total_time=total_time,
        database_status=health_status["checks"]["database"],
        redis_status=health_status["checks"]["redis"],
        elasticsearch_status=health_status["checks"]["elasticsearch"],
        **trace_context
    )
    
    return health_status


@router.get("/health/ready")
async def readiness_check(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Readiness check for Kubernetes liveness/readiness probes."""
    start_time = time.time()
    
    # Get current trace context
    trace_context = get_current_trace_context()
    
    try:
        # Check database
        db.execute("SELECT 1")
        
        # Check Redis
        redis_status = {"status": "disabled", "message": "Redis removed for simplification"}
        if redis_status["status"] != "healthy":
            raise Exception(f"Redis not ready: {redis_status['status']}")
        
        # Check Elasticsearch
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.ELASTICSEARCH_URL}/_cluster/health",
                timeout=5.0
            )
            if response.status_code != 200:
                raise Exception(f"Elasticsearch not ready: {response.status_code}")
        
        total_time = time.time() - start_time
        logger.info(
            "Readiness check successful", 
            response_time=total_time,
            **trace_context
        )
        
        return {
            "status": "ready",
            "response_time": total_time,
            "timestamp": time.time(),
            "trace_id": trace_context.get("request_id"),
            "correlation_id": trace_context.get("correlation_id")
        }
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(
            "Readiness check failed",
            error=str(e),
            response_time=total_time,
            **trace_context,
            exc_info=True
        )
        raise HTTPException(
            status_code=503, 
            detail={
                "status": "not_ready",
                "error": str(e),
                "response_time": total_time,
                "timestamp": time.time(),
                "trace_id": trace_context.get("request_id"),
                "correlation_id": trace_context.get("correlation_id")
            }
        )


@router.get("/health/live")
async def liveness_check(request: Request) -> Dict[str, Any]:
    """Liveness check for Kubernetes liveness probe."""
    # Get current trace context
    trace_context = get_current_trace_context()
    
    logger.debug("Liveness check requested", **trace_context)
    return {
        "status": "alive",
        "timestamp": time.time(),
        "service": "supplero-backend",
        "trace_id": trace_context.get("request_id"),
        "correlation_id": trace_context.get("correlation_id")
    } 