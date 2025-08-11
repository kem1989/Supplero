"""
Redis client configuration and session management for the Supplero application.
Enhanced with structured logging for observability.
"""

import redis
from typing import Optional, Any, Dict
import time
from contextlib import contextmanager

from app.core.config import settings
from app.core.logging import get_logger, log_integration_call

# Logger
logger = get_logger(__name__)

# Redis client
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30
)


def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    return redis_client


def check_redis_health() -> bool:
    """Check if Redis is healthy."""
    try:
        start_time = time.time()
        result = redis_client.ping()
        response_time = time.time() - start_time
        
        if result:
            logger.debug("Redis health check successful", response_time=response_time)
            return True
        else:
            logger.warning("Redis health check failed - ping returned False")
            return False
            
    except Exception as e:
        logger.error("Redis health check failed", error=str(e), exc_info=True)
        return False


def log_redis_operation(operation: str, key: str, success: bool, response_time: float = None, **kwargs):
    """Log Redis operations for audit trail."""
    log_data = {
        "operation": operation,
        "key": key,
        "success": success,
        "response_time": response_time,
        "timestamp": time.time(),
        "service": "supplero-api",
        "environment": settings.ENVIRONMENT,
    }
    
    log_data.update(kwargs)
    
    if success:
        logger.debug("Redis operation", **log_data)
    else:
        logger.warning("Redis operation failed", **log_data)


class RedisClient:
    """Redis client wrapper with logging capabilities."""
    
    def __init__(self):
        self.client = redis_client
    
    def get(self, key: str) -> Optional[str]:
        """Get value from Redis with logging."""
        start_time = time.time()
        try:
            value = self.client.get(key)
            response_time = time.time() - start_time
            
            log_redis_operation(
                operation="GET",
                key=key,
                success=True,
                response_time=response_time,
                value_length=len(value) if value else 0
            )
            
            return value
            
        except Exception as e:
            response_time = time.time() - start_time
            log_redis_operation(
                operation="GET",
                key=key,
                success=False,
                response_time=response_time,
                error=str(e)
            )
            raise
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with logging."""
        start_time = time.time()
        try:
            result = self.client.set(key, value, ex=ex)
            response_time = time.time() - start_time
            
            log_redis_operation(
                operation="SET",
                key=key,
                success=result,
                response_time=response_time,
                value_length=len(value),
                expiration=ex
            )
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            log_redis_operation(
                operation="SET",
                key=key,
                success=False,
                response_time=response_time,
                error=str(e)
            )
            raise
    
    def delete(self, key: str) -> int:
        """Delete key from Redis with logging."""
        start_time = time.time()
        try:
            result = self.client.delete(key)
            response_time = time.time() - start_time
            
            log_redis_operation(
                operation="DELETE",
                key=key,
                success=result > 0,
                response_time=response_time,
                deleted_count=result
            )
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            log_redis_operation(
                operation="DELETE",
                key=key,
                success=False,
                response_time=response_time,
                error=str(e)
            )
            raise
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis with logging."""
        start_time = time.time()
        try:
            result = self.client.exists(key)
            response_time = time.time() - start_time
            
            log_redis_operation(
                operation="EXISTS",
                key=key,
                success=True,
                response_time=response_time,
                exists=bool(result)
            )
            
            return bool(result)
            
        except Exception as e:
            response_time = time.time() - start_time
            log_redis_operation(
                operation="EXISTS",
                key=key,
                success=False,
                response_time=response_time,
                error=str(e)
            )
            raise
    
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key in Redis with logging."""
        start_time = time.time()
        try:
            result = self.client.expire(key, seconds)
            response_time = time.time() - start_time
            
            log_redis_operation(
                operation="EXPIRE",
                key=key,
                success=result,
                response_time=response_time,
                expiration_seconds=seconds
            )
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            log_redis_operation(
                operation="EXPIRE",
                key=key,
                success=False,
                response_time=response_time,
                error=str(e)
            )
            raise
    
    def ping(self) -> bool:
        """Ping Redis with logging."""
        start_time = time.time()
        try:
            result = self.client.ping()
            response_time = time.time() - start_time
            
            log_redis_operation(
                operation="PING",
                key="N/A",
                success=result,
                response_time=response_time
            )
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            log_redis_operation(
                operation="PING",
                key="N/A",
                success=False,
                response_time=response_time,
                error=str(e)
            )
            raise


# Health check function
async def check_redis_health_async() -> Dict[str, Any]:
    """Async Redis health check for health endpoints."""
    start_time = time.time()
    try:
        is_healthy = check_redis_health()
        response_time = time.time() - start_time
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "response_time": response_time,
            "service": "redis"
        }
        
    except Exception as e:
        response_time = time.time() - start_time
        logger.error("Redis health check failed", error=str(e), response_time=response_time)
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time": response_time,
            "service": "redis"
        }


# Cleanup function
def close_redis_connections():
    """Close Redis connections."""
    try:
        redis_client.close()
        logger.info("Redis connections closed")
    except Exception as e:
        logger.error("Failed to close Redis connections", error=str(e)) 