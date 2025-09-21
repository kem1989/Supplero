/**
 * Frontend tracing utilities for request correlation and distributed tracing
 */

// Generate a unique trace ID for the frontend session
export const generateFrontendTraceId = (): string => {
  return `frontend_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Generate a correlation ID for complex request chains
export const generateCorrelationId = (): string => {
  return `corr_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Get or create a session trace ID
export const getSessionTraceId = (): string => {
  if (typeof window === 'undefined') return 'server-side';
  
  let sessionTraceId = sessionStorage.getItem('supplero_trace_id');
  if (!sessionTraceId) {
    sessionTraceId = generateFrontendTraceId();
    sessionStorage.setItem('supplero_trace_id', sessionTraceId);
  }
  return sessionTraceId;
};

// Get or create a session correlation ID
export const getSessionCorrelationId = (): string => {
  if (typeof window === 'undefined') return 'server-side';
  
  let sessionCorrelationId = sessionStorage.getItem('supplero_correlation_id');
  if (!sessionCorrelationId) {
    sessionCorrelationId = generateCorrelationId();
    sessionStorage.setItem('supplero_correlation_id', sessionCorrelationId);
  }
  return sessionCorrelationId;
};

// Create headers with trace information
export const createTraceHeaders = (): Record<string, string> => {
  const traceId = getSessionTraceId();
  const correlationId = getSessionCorrelationId();
  
  return {
    'X-Trace-ID': traceId,
    'X-Correlation-ID': correlationId,
    'X-Client-Type': 'frontend',
    'X-Client-Version': '1.0.0'
  };
};

// Extract trace information from response headers
export const extractTraceInfo = (response: Response): Record<string, string> => {
  const traceInfo: Record<string, string> = {};
  
  // Extract trace headers from response
  const traceId = response.headers.get('X-Trace-ID');
  const correlationId = response.headers.get('X-Correlation-ID');
  const spanId = response.headers.get('X-Span-ID');
  
  if (traceId) traceInfo.traceId = traceId;
  if (correlationId) traceInfo.correlationId = correlationId;
  if (spanId) traceInfo.spanId = spanId;
  
  return traceInfo;
};

// Log trace information to console (for development)
export const logTraceInfo = (operation: string, traceInfo: Record<string, string>): void => {
  if (process.env.NODE_ENV === 'development') {
    console.log(`🔍 [${operation}] Trace Info:`, traceInfo);
  }
};

// Create a new span for complex operations
export const createSpan = (operation: string): string => {
  const spanId = `span_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
  
  if (process.env.NODE_ENV === 'development') {
    console.log(`🔍 [${operation}] New Span:`, spanId);
  }
  
  return spanId;
};

// Enhanced axios interceptor for trace headers
export const addTraceHeadersToRequest = (config: any): any => {
  const traceHeaders = createTraceHeaders();
  
  // Add trace headers to the request
  config.headers = {
    ...config.headers,
    ...traceHeaders
  };
  
  // Log trace info in development
  if (process.env.NODE_ENV === 'development') {
    logTraceInfo('API Request', traceHeaders);
  }
  
  return config;
};

// Enhanced axios interceptor for trace response handling
export const handleTraceResponse = (response: any): any => {
  const traceInfo = extractTraceInfo(response);
  
  // Log trace info in development
  if (process.env.NODE_ENV === 'development') {
    logTraceInfo('API Response', traceInfo);
  }
  
  // Store trace info for potential use
  if (response.config) {
    response.config.traceInfo = traceInfo;
  }
  
  return response;
};

// Utility to get current trace context
export const getCurrentTraceContext = (): Record<string, string> => {
  return {
    traceId: getSessionTraceId(),
    correlationId: getSessionCorrelationId(),
    clientType: 'frontend',
    timestamp: new Date().toISOString()
  };
}; 