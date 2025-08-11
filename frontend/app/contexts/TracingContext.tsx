/**
 * Tracing context provider for managing tracing state across the application
 */

'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { 
  getCurrentTraceContext, 
  getSessionTraceId, 
  getSessionCorrelationId,
  createSpan,
  logTraceInfo 
} from '../lib/tracing';

interface TracingContextType {
  traceContext: ReturnType<typeof getCurrentTraceContext>;
  currentSpanId: string | null;
  createNewSpan: (operation: string) => string;
  logTraceEvent: (event: string, data?: Record<string, any>) => void;
  refreshTraceContext: () => void;
  isTracingEnabled: boolean;
}

const TracingContext = createContext<TracingContextType | undefined>(undefined);

export const useTracingContext = () => {
  const context = useContext(TracingContext);
  if (context === undefined) {
    throw new Error('useTracingContext must be used within a TracingProvider');
  }
  return context;
};

interface TracingProviderProps {
  children: React.ReactNode;
}

export const TracingProvider: React.FC<TracingProviderProps> = ({ children }) => {
  const [traceContext, setTraceContext] = useState(getCurrentTraceContext());
  const [currentSpanId, setCurrentSpanId] = useState<string | null>(null);
  const [isTracingEnabled] = useState(process.env.NODE_ENV === 'development');

  // Refresh trace context
  const refreshTraceContext = () => {
    setTraceContext(getCurrentTraceContext());
  };

  // Create a new span for operations
  const createNewSpan = (operation: string): string => {
    const spanId = createSpan(operation);
    setCurrentSpanId(spanId);
    return spanId;
  };

  // Log trace events
  const logTraceEvent = (event: string, data?: Record<string, any>) => {
    if (!isTracingEnabled) return;
    
    const eventData = {
      ...traceContext,
      event,
      spanId: currentSpanId,
      ...data
    };
    logTraceInfo(event, eventData);
  };

  // Initialize tracing on mount
  useEffect(() => {
    if (isTracingEnabled) {
      logTraceEvent('TracingProvider Initialized', {
        component: 'TracingProvider',
        sessionTraceId: getSessionTraceId(),
        sessionCorrelationId: getSessionCorrelationId()
      });
    }
  }, [isTracingEnabled]);

  // Update trace context when session storage changes
  useEffect(() => {
    if (!isTracingEnabled) return;

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
  }, [isTracingEnabled]);

  const value: TracingContextType = {
    traceContext,
    currentSpanId,
    createNewSpan,
    logTraceEvent,
    refreshTraceContext,
    isTracingEnabled
  };

  return (
    <TracingContext.Provider value={value}>
      {children}
    </TracingContext.Provider>
  );
}; 