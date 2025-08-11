# Structured Logging Implementation

## Overview

This document describes the comprehensive structured logging implementation for the Supplero AI-Powered Procurement Platform, which forms the foundation of the **Observability & Audit Baseline** as outlined in the project scope.

## 🎯 **Features Implemented**

### 1. **Structured Logging with `structlog`**
- **JSON-formatted logs** for easy parsing and analysis
- **Consistent log structure** across all services
- **Automatic context injection** for request correlation
- **Configurable log levels** via environment variables

### 2. **Request Correlation & Trace IDs**
- **Unique trace ID generation** for every request
- **Request context propagation** across all log entries
- **User context extraction** from JWT tokens
- **Automatic context cleanup** after request completion

### 3. **Comprehensive Service Logging**
- **Database operations** with performance metrics
- **Redis operations** with response time tracking
- **External API calls** with status codes and timing
- **Security events** with detailed context
- **Health checks** with comprehensive status reporting

### 4. **Performance Monitoring**
- **Request timing** from start to completion
- **Database query execution** time tracking
- **External service response** time monitoring
- **Resource utilization** logging

## 🚀 **Quick Start**

### Basic Usage

```python
from app.core.logging import get_logger

# Get a logger instance
logger = get_logger(__name__)

# Basic logging
logger.info("User action completed", user_id=123, action="login")
logger.warning("High memory usage detected", memory_usage="85%")
logger.error("Database connection failed", error=str(e), exc_info=True)
```

### Request Context Usage

```python
from app.core.logging import set_request_context, clear_request_context

# Set request context (automatically done in middleware)
set_request_context(request_id="trace_abc123", user_id="user_456")

# All subsequent logs will include request_id and user_id
logger.info("Processing user request")

# Clear context when done
clear_request_context()
```

### Specialized Logging Functions

```python
from app.core.logging import (
    log_database_operation,
    log_integration_call,
    log_security_event
)

# Database operations
log_database_operation(
    operation="INSERT",
    table="users",
    record_id="user_789",
    user_id="admin_123"
)

# External API calls
log_integration_call(
    integration_name="OpenAI API",
    endpoint="/v1/chat/completions",
    status_code=200,
    response_time=1.25
)

# Security events
log_security_event(
    event_type="login_attempt",
    severity="warning",
    user_id="user_123",
    ip_address="192.168.1.100"
)
```

## 📊 **Log Structure**

### Standard Log Fields

Every log entry includes these standard fields:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "info",
  "logger": "app.api.v1.auth",
  "event": "User authenticated successfully",
  "service": "supplero-api",
  "environment": "development"
}
```

### Request Context Fields

When request context is set, additional fields are automatically included:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "info",
  "logger": "app.api.v1.auth",
  "event": "User authenticated successfully",
  "request_id": "trace_abc123def456",
  "user_id": "user_789",
  "service": "supplero-api",
  "environment": "development"
}
```

### Specialized Log Fields

#### Database Operations
```json
{
  "operation": "INSERT",
  "table": "users",
  "record_id": "user_123",
  "user_id": "admin_456",
  "execution_time": 0.045,
  "rows_affected": 1
}
```

#### External API Calls
```json
{
  "integration": "OpenAI API",
  "endpoint": "/v1/chat/completions",
  "status_code": 200,
  "response_time": 1.25,
  "tokens_used": 150,
  "cost": 0.003
}
```

#### Security Events
```json
{
  "event_type": "login_attempt",
  "severity": "warning",
  "user_id": "user_123",
  "ip_address": "192.168.1.100",
  "success": false,
  "failure_reason": "invalid_credentials"
}
```

## 🔧 **Configuration**

### Environment Variables

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log format (json, text)
LOG_FORMAT=json

# Environment (development, staging, production)
ENVIRONMENT=development
```

### Log Level Configuration

```python
# In app/core/logging.py
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("fastapi").setLevel(logging.INFO)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("elasticsearch").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.INFO)
```

## 🧪 **Testing**

### Run the Test Script

```bash
cd backend
python test_logging.py
```

This will test all logging features and show example output.

### Manual Testing

```bash
# Start the application
make dev

# Make a request to see logs
curl -H "X-Trace-ID: test_123" http://localhost:8000/health

# Check logs in the console
```

## 📈 **Monitoring & Analysis**

### Log Aggregation

The structured JSON logs can be easily aggregated using tools like:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Fluentd** for log forwarding
- **Prometheus** for metrics collection
- **Grafana** for visualization

### Key Metrics to Monitor

1. **Request Performance**
   - Average response time
   - 95th percentile response time
   - Error rates by endpoint

2. **Database Performance**
   - Query execution times
   - Connection pool utilization
   - Transaction success rates

3. **External Service Health**
   - API response times
   - Error rates
   - Availability

4. **Security Events**
   - Authentication attempts
   - Authorization failures
   - Suspicious activities

## 🔒 **Security & Privacy**

### Data Redaction

- **Sensitive fields** are automatically redacted
- **User credentials** are never logged
- **Personal data** is anonymized where possible

### Access Control

- **Audit logs** are protected by role-based access
- **Log retention** policies are configurable
- **Log encryption** at rest and in transit

## 🚨 **Troubleshooting**

### Common Issues

1. **Logs not appearing**
   - Check `LOG_LEVEL` environment variable
   - Verify logging configuration in `setup_logging()`

2. **Missing context fields**
   - Ensure `set_request_context()` is called
   - Check middleware configuration

3. **Performance impact**
   - Use appropriate log levels for production
   - Consider async logging for high-volume operations

### Debug Mode

Enable debug logging to see detailed information:

```bash
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development
```

## 🔄 **Next Steps**

This structured logging implementation provides the foundation for:

1. **Advanced Monitoring** - Prometheus metrics integration
2. **Distributed Tracing** - OpenTelemetry integration
3. **Log Analytics** - ELK stack integration
4. **Alerting** - Automated anomaly detection
5. **Compliance Reporting** - SOC2 audit trail generation

## 📚 **References**

- [structlog Documentation](https://www.structlog.org/)
- [FastAPI Logging](https://fastapi.tiangolo.com/tutorial/logging/)
- [SQLAlchemy Events](https://docs.sqlalchemy.org/en/14/core/events.html)
- [Redis Python Client](https://redis-py.readthedocs.io/) 