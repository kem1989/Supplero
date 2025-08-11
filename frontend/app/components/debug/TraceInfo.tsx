/**
 * Debug component to display trace information
 * Only visible in development mode
 */

'use client';

import React from 'react';
import { useTracing } from '../../hooks/useTracing';

interface TraceInfoProps {
  showDetails?: boolean;
  className?: string;
}

export const TraceInfo: React.FC<TraceInfoProps> = ({ 
  showDetails = false, 
  className = '' 
}) => {
  const { traceContext, currentSpanId } = useTracing();

  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div className={`bg-gray-100 border border-gray-300 rounded p-3 text-xs font-mono ${className}`}>
      <div className="font-semibold text-gray-700 mb-2">🔍 Trace Info (Dev)</div>
      
      <div className="space-y-1">
        <div>
          <span className="text-gray-600">Trace ID:</span>
          <span className="ml-2 text-blue-600 font-medium">
            {traceContext.traceId.substring(0, 20)}...
          </span>
        </div>
        
        <div>
          <span className="text-gray-600">Correlation ID:</span>
          <span className="ml-2 text-green-600 font-medium">
            {traceContext.correlationId.substring(0, 20)}...
          </span>
        </div>
        
        {currentSpanId && (
          <div>
            <span className="text-gray-600">Current Span:</span>
            <span className="ml-2 text-purple-600 font-medium">
              {currentSpanId.substring(0, 20)}...
            </span>
          </div>
        )}
        
        {showDetails && (
          <>
            <div>
              <span className="text-gray-600">Client Type:</span>
              <span className="ml-2 text-gray-800">{traceContext.clientType}</span>
            </div>
            
            <div>
              <span className="text-gray-600">Timestamp:</span>
              <span className="ml-2 text-gray-800">
                {new Date(traceContext.timestamp).toLocaleTimeString()}
              </span>
            </div>
            
            <div className="pt-2 border-t border-gray-300">
              <button
                onClick={() => {
                  console.log('Full Trace Context:', traceContext);
                  console.log('Current Span ID:', currentSpanId);
                }}
                className="text-blue-600 hover:text-blue-800 underline"
              >
                Log to Console
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

// Compact version for headers/footers
export const TraceInfoCompact: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { traceContext } = useTracing();

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <div className={`text-xs text-gray-500 ${className}`}>
      <span className="font-mono">
        🔍 {traceContext.traceId.substring(0, 12)}...
      </span>
    </div>
  );
};

// Inline trace ID display
export const InlineTraceId: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { traceContext } = useTracing();

  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <span className={`text-xs text-gray-500 font-mono ${className}`}>
      {traceContext.traceId.substring(0, 8)}...
    </span>
  );
}; 