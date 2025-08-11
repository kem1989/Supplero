/**
 * React hook for managing tracing context in components
 */

import { useEffect, useState, useCallback } from 'react';
import { 
  getCurrentTraceContext, 
  getSessionTraceId, 
  getSessionCorrelationId,
  createSpan,
  logTraceInfo 
} from '../lib/tracing';

export interface TraceContext {
  traceId: string;
  correlationId: string;
  clientType: string;
  timestamp: string;
}

export interface UseTracingReturn {
  traceContext: TraceContext;
  currentSpanId: string | null;
  createNewSpan: (operation: string) => string;
  logTraceEvent: (event: string, data?: Record<string, any>) => void;
  refreshTraceContext: () => void;
}

export const useTracing = (): UseTracingReturn => {
  const [traceContext, setTraceContext] = useState<TraceContext>(getCurrentTraceContext());
  const [currentSpanId, setCurrentSpanId] = useState<string | null>(null);

  // Refresh trace context
  const refreshTraceContext = useCallback(() => {
    setTraceContext(getCurrentTraceContext());
  }, []);

  // Create a new span for operations
  const createNewSpan = useCallback((operation: string): string => {
    const spanId = createSpan(operation);
    setCurrentSpanId(spanId);
    return spanId;
  }, []);

  // Log trace events
  const logTraceEvent = useCallback((event: string, data?: Record<string, any>) => {
    const eventData = {
      ...traceContext,
      event,
      spanId: currentSpanId,
      ...data
    };
    logTraceInfo(event, eventData);
  }, [traceContext, currentSpanId]);

  // Update trace context when session storage changes
  useEffect(() => {
    const handleStorageChange = () => {
      refreshTraceContext();
    };

    // Listen for storage events (when trace IDs change in other tabs)
    window.addEventListener('storage', handleStorageChange);
    
    // Also refresh on focus (in case session storage was updated)
    const handleFocus = () => {
      refreshTraceContext();
    };
    window.addEventListener('focus', handleFocus);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, [refreshTraceContext]);

  // Log component mount with trace context
  useEffect(() => {
    logTraceEvent('Component Mounted', {
      component: 'useTracing Hook'
    });
  }, [logTraceEvent]);

  return {
    traceContext,
    currentSpanId,
    createNewSpan,
    logTraceEvent,
    refreshTraceContext
  };
};

// Hook for specific component tracing
export const useComponentTracing = (componentName: string) => {
  const tracing = useTracing();
  
  // Log component lifecycle events
  useEffect(() => {
    tracing.logTraceEvent('Component Mounted', { component: componentName });
    
    return () => {
      tracing.logTraceEvent('Component Unmounted', { component: componentName });
    };
  }, [tracing, componentName]);

  return tracing;
};

// Hook for operation tracing
export const useOperationTracing = (operationName: string) => {
  const tracing = useTracing();
  
  const traceOperation = useCallback(async <T>(
    operation: () => Promise<T>,
    additionalData?: Record<string, any>
  ): Promise<T> => {
    const spanId = tracing.createNewSpan(operationName);
    
    try {
      tracing.logTraceEvent('Operation Started', {
        operation: operationName,
        spanId,
        ...additionalData
      });
      
      const startTime = Date.now();
      const result = await operation();
      const duration = Date.now() - startTime;
      
      tracing.logTraceEvent('Operation Completed', {
        operation: operationName,
        spanId,
        duration,
        success: true,
        ...additionalData
      });
      
      return result;
    } catch (error) {
      const duration = Date.now() - startTime;
      
      tracing.logTraceEvent('Operation Failed', {
        operation: operationName,
        spanId,
        duration,
        success: false,
        error: error instanceof Error ? error.message : String(error),
        ...additionalData
      });
      
      throw error;
    }
  }, [tracing, operationName]);

  return {
    ...tracing,
    traceOperation
  };
}; 