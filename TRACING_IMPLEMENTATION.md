# Trace ID and Request Correlation Implementation

## Overview

This document describes the comprehensive implementation of trace IDs and request correlation for the Supplero platform, which is part of the **Observability & Audit Baseline** (Phase 1).

## ✅ Implementation Status

- [x] **Backend Trace ID Generation** - Unique trace IDs for every request
- [x] **Correlation ID Support** - Complex request chain correlation
- [x] **Span ID Generation** - Distributed tracing span management
- [x] **Frontend Trace Propagation** - Client-side trace ID management
- [x] **Structured Logging Integration** - All logs include trace context
- [x] **Response Header Propagation** - Trace IDs returned in all responses
- [x] **Error Handling** - Trace IDs included in error responses
- [x] **Development Tools** - Debug components for trace visualization

## Architecture

### Backend Implementation

#### 1. Core Logging System (`backend/app/core/logging.py`)

```python
# Context variables for request correlation
REQUEST_ID: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
USER_ID: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
CORRELATION_ID: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
SPAN_ID: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
PARENT_SPAN_ID: ContextVar[Optional[str]] = ContextVar("parent_span_id", default=None)
```

**Key Functions:**
- `generate_trace_id()` - Creates unique trace IDs
- `generate_correlation_id()` - Creates correlation IDs for request chains
- `generate_span_id()` - Creates span IDs for distributed tracing
- `set_request_context()` - Sets all context variables
- `get_current_trace_context()` - Retrieves current trace context

#### 2. Middleware Integration (`backend/app/main.py`)

The main FastAPI application includes comprehensive middleware that:

- **Extracts existing trace IDs** from request headers (`X-Trace-ID`, `X-Correlation-ID`, `X-Parent-Span-ID`)
- **Generates new IDs** when none exist
- **Sets request context** for structured logging
- **Logs trace events** (start, complete, failed)
- **Adds trace headers** to all responses

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Extract or generate trace IDs
    trace_id = request.headers.get("X-Trace-ID") or generate_trace_id()
    correlation_id = request.headers.get("X-Correlation-ID") or generate_correlation_id()
    parent_span_id = request.headers.get("X-Parent-Span-ID")
    span_id = generate_span_id()
    
    # Set request context and log events
    # ... implementation details
```

#### 3. API Endpoint Integration

All API endpoints now include trace context in their logging:

```python
@router.get("/health")
async def health_check(request: Request) -> Dict[str, Any]:
    # Get current trace context
    trace_context = get_current_trace_context()
    
    logger.debug("Basic health check requested", **trace_context)
    return {
        "status": "healthy",
        "trace_id": trace_context.get("request_id"),
        "correlation_id": trace_context.get("correlation_id")
    }
```

### Frontend Implementation

#### 1. Tracing Utilities (`frontend/app/lib/tracing.ts`)

**Core Functions:**
- `generateFrontendTraceId()` - Creates frontend-specific trace IDs
- `getSessionTraceId()` - Manages session-based trace IDs
- `createTraceHeaders()` - Generates headers for API requests
- `extractTraceInfo()` - Extracts trace info from responses

**Session Management:**
- Trace IDs are stored in `sessionStorage`
- Persist across page refreshes within the same session
- New trace IDs generated for new sessions

#### 2. React Hooks (`frontend/app/hooks/useTracing.ts`)

**Available Hooks:**
- `useTracing()` - Basic tracing functionality
- `useComponentTracing()` - Component lifecycle tracing
- `useOperationTracing()` - Operation-level tracing with timing

**Example Usage:**
```tsx
const tracing = useComponentTracing('MyComponent');

useEffect(() => {
  tracing.logTraceEvent('Component Mounted', { component: 'MyComponent' });
}, []);
```

#### 3. API Integration (`frontend/app/lib/auth.ts`)

Axios interceptors automatically add trace headers to all requests:

```typescript
// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add trace headers
    config = addTraceHeadersToRequest(config);
    return config;
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // Handle trace information from response
    response = handleTraceResponse(response);
    return response;
  }
);
```

#### 4. Debug Components (`frontend/app/components/debug/TraceInfo.tsx`)

Development-only components for visualizing trace information:

- `TraceInfo` - Full trace information display
- `TraceInfoCompact` - Compact header/footer display
- `InlineTraceId` - Inline trace ID display

## Trace ID Format

### Backend Trace IDs
- **Format:** `trace_{uuid_hex[:16]}`
- **Example:** `trace_3df65709709a4334`
- **Length:** 21 characters

### Frontend Trace IDs
- **Format:** `frontend_{timestamp}_{random_string}`
- **Example:** `frontend_1754906318431_abc123def`
- **Length:** Variable

### Correlation IDs
- **Format:** `corr_{uuid_hex[:12]}`
- **Example:** `corr_48da96409ad9`
- **Length:** 17 characters

### Span IDs
- **Format:** `span_{uuid_hex[:8]}`
- **Example:** `span_c7c3c7c6`
- **Length:** 13 characters

## HTTP Headers

### Request Headers
- `X-Trace-ID` - Existing trace ID (optional)
- `X-Correlation-ID` - Existing correlation ID (optional)
- `X-Parent-Span-ID` - Parent span ID for distributed tracing (optional)
- `X-Client-Type` - Client type (frontend, mobile, etc.)
- `X-Client-Version` - Client version

### Response Headers
- `X-Trace-ID` - Trace ID for the request
- `X-Correlation-ID` - Correlation ID for the request
- `X-Span-ID` - Span ID for the request

## Logging Integration

### Structured Logging
All log entries automatically include trace context:

```json
{
  "event": "Request started",
  "method": "GET",
  "url": "http://localhost:8000/health",
  "trace_id": "trace_3df65709709a4334",
  "correlation_id": "corr_48da96409ad9",
  "span_id": "span_c7c3c7c6",
  "parent_span_id": null,
  "user_id": "user_123",
  "service": "supplero-api",
  "environment": "development",
  "timestamp": "2025-08-11T09:58:19.493532Z"
}
```

### Trace Events
Special trace events are logged for observability:

- `request_start` - Request processing begins
- `request_complete` - Request processing completes successfully
- `request_failed` - Request processing fails
- `Component Mounted` - React component lifecycle
- `Operation Started/Completed/Failed` - Business operation tracing

## Usage Examples

### Backend API Development

```python
from app.core.logging import get_current_trace_context

@router.get("/example")
async def example_endpoint(request: Request):
    trace_context = get_current_trace_context()
    
    logger.info("Processing example request", **trace_context)
    
    # Your business logic here
    
    return {"message": "success", "trace_id": trace_context["request_id"]}
```

### Frontend Component Development

```tsx
import { useComponentTracing } from '../hooks/useTracing';

export const MyComponent = () => {
  const tracing = useComponentTracing('MyComponent');
  
  const handleClick = async () => {
    const result = await tracing.traceOperation('Button Click', async () => {
      // Your async operation here
      return await api.someEndpoint();
    });
  };
  
  return <button onClick={handleClick}>Click Me</button>;
};
```

### Custom Trace Headers

```typescript
// Send request with custom trace context
const response = await fetch('/api/endpoint', {
  headers: {
    'X-Trace-ID': 'custom_trace_123',
    'X-Correlation-ID': 'custom_corr_456',
    'X-Parent-Span-ID': 'parent_span_789'
  }
});
```

## Testing

### Automated Testing
Run the test script to verify implementation:

```bash
python3 test_tracing.py
```

### Manual Testing
1. **Backend:** Check response headers for trace IDs
2. **Frontend:** Open browser dev tools and check console for trace logs
3. **Logs:** Monitor backend logs for structured trace information

## Monitoring and Observability

### What You Can Track
- **Request Flow:** Follow requests through the system using trace IDs
- **Performance:** Measure request processing times with span IDs
- **Error Correlation:** Correlate errors with specific requests
- **User Actions:** Track user interactions across the frontend
- **API Dependencies:** Monitor calls between services

### Log Analysis
Search logs by trace ID to reconstruct request flows:

```bash
# Find all logs for a specific trace
docker-compose logs backend | grep "trace_3df65709709a4334"

# Find all logs for a specific user
docker-compose logs backend | grep "user_123"
```

## Future Enhancements

### Phase 2 Considerations
- **Distributed Tracing:** Integration with Jaeger or Zipkin
- **Metrics Collection:** Prometheus metrics with trace labels
- **Alerting:** Trace-based alerting for performance issues
- **Visualization:** Trace flow diagrams and request maps

### Advanced Features
- **Sampling:** Configurable trace sampling rates
- **Retention:** Trace data retention policies
- **Export:** Trace data export for external analysis
- **Integration:** Third-party APM tool integration

## Configuration

### Environment Variables
```bash
# Logging level
LOG_LEVEL=INFO

# Environment
ENVIRONMENT=development
```

### Development vs Production
- **Development:** Full trace logging, debug components visible
- **Production:** Essential trace logging, debug components hidden
- **Staging:** Configurable trace levels for testing

## Troubleshooting

### Common Issues

1. **Missing Trace IDs**
   - Check if middleware is properly configured
   - Verify logging setup in main.py

2. **Frontend Not Sending Headers**
   - Check if axios interceptors are configured
   - Verify tracing utilities are imported

3. **Logs Missing Context**
   - Ensure `get_current_trace_context()` is called
   - Check if context variables are properly set

### Debug Steps
1. Check backend logs for trace events
2. Verify response headers contain trace IDs
3. Check frontend console for trace logs
4. Use debug components to visualize trace state

## Conclusion

The trace ID and request correlation implementation provides a solid foundation for observability and debugging across the Supplero platform. It enables:

- **End-to-end request tracking** from frontend to backend
- **Structured logging** with full context
- **Performance monitoring** and debugging
- **User experience tracking** and optimization
- **Operational visibility** into system behavior

This implementation satisfies the Phase 1 requirement for "Trace IDs and request correlation for every request" and sets the stage for more advanced observability features in future phases. 