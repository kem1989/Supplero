'use client';

import React from 'react';

export interface RiskIndicatorProps {
  riskLevel: string;
  riskScore: number;
  size?: 'sm' | 'md' | 'lg';
  showScore?: boolean;
  showLabel?: boolean;
  className?: string;
}

const RISK_COLORS = {
  CRITICAL: {
    text: 'text-red-500',
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
    ring: 'ring-red-500/20',
    dot: 'bg-red-500'
  },
  HIGH: {
    text: 'text-red-400',
    bg: 'bg-red-400/10',
    border: 'border-red-400/20',
    ring: 'ring-red-400/20',
    dot: 'bg-red-400'
  },
  MEDIUM: {
    text: 'text-yellow-400',
    bg: 'bg-yellow-400/10',
    border: 'border-yellow-400/20',
    ring: 'ring-yellow-400/20',
    dot: 'bg-yellow-400'
  },
  LOW: {
    text: 'text-green-400',
    bg: 'bg-green-400/10',
    border: 'border-green-400/20',
    ring: 'ring-green-400/20',
    dot: 'bg-green-400'
  },
  UNKNOWN: {
    text: 'text-slate-400',
    bg: 'bg-slate-400/10',
    border: 'border-slate-400/20',
    ring: 'ring-slate-400/20',
    dot: 'bg-slate-400'
  }
};

const SIZE_CLASSES = {
  sm: {
    badge: 'px-2 py-1 text-xs',
    dot: 'w-2 h-2',
    text: 'text-xs',
    score: 'text-xs'
  },
  md: {
    badge: 'px-3 py-1 text-sm',
    dot: 'w-3 h-3',
    text: 'text-sm',
    score: 'text-sm'
  },
  lg: {
    badge: 'px-4 py-2 text-base',
    dot: 'w-4 h-4',
    text: 'text-base',
    score: 'text-lg'
  }
};

export default function RiskIndicator({
  riskLevel,
  riskScore,
  size = 'md',
  showScore = true,
  showLabel = true,
  className = ''
}: RiskIndicatorProps) {
  const normalizedRiskLevel = riskLevel?.toUpperCase() || 'UNKNOWN';
  const colors = RISK_COLORS[normalizedRiskLevel as keyof typeof RISK_COLORS] || RISK_COLORS.UNKNOWN;
  const sizeClasses = SIZE_CLASSES[size];

  const getRiskIcon = () => {
    switch (normalizedRiskLevel) {
      case 'CRITICAL':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L1 21h22L12 2zm0 16a2 2 0 110-4 2 2 0 010 4zm0-6a1 1 0 01-1-1V8a1 1 0 012 0v3a1 1 0 01-1 1z"/>
          </svg>
        );
      case 'HIGH':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
          </svg>
        );
      case 'MEDIUM':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15v-2h2v2h-2zm2-4V7h-2v6h2z"/>
          </svg>
        );
      case 'LOW':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
          </svg>
        );
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {/* Risk Badge */}
      <div className={`
        inline-flex items-center justify-center space-x-1 rounded-lg border font-medium
        ${colors.text} ${colors.bg} ${colors.border} ${sizeClasses.badge}
      `}>
        {getRiskIcon()}
        {showLabel && <span>{normalizedRiskLevel}</span>}
      </div>

      {/* Risk Score */}
      {showScore && (
        <div className="flex flex-col items-end">
          <div className={`font-bold ${colors.text} ${sizeClasses.score}`}>
            {Math.round(riskScore)}
          </div>
          <div className={`text-slate-500 ${sizeClasses.text}`}>
            /100
          </div>
        </div>
      )}
    </div>
  );
}

export function RiskDot({ riskLevel, size = 'md', className = '' }: Pick<RiskIndicatorProps, 'riskLevel' | 'size' | 'className'>) {
  const normalizedRiskLevel = riskLevel?.toUpperCase() || 'UNKNOWN';
  const colors = RISK_COLORS[normalizedRiskLevel as keyof typeof RISK_COLORS] || RISK_COLORS.UNKNOWN;
  const sizeClasses = SIZE_CLASSES[size];

  return (
    <div 
      className={`
        rounded-full ${colors.dot} ${sizeClasses.dot} ${className}
      `}
      title={`Risk Level: ${normalizedRiskLevel}`}
    />
  );
}

export function RiskBar({ riskScore, height = 'h-2', className = '' }: { riskScore: number; height?: string; className?: string }) {
  const percentage = Math.min(Math.max(riskScore, 0), 100);
  
  const getBarColor = () => {
    if (percentage >= 80) return 'bg-red-500';
    if (percentage >= 60) return 'bg-red-400';
    if (percentage >= 40) return 'bg-yellow-400';
    return 'bg-green-400';
  };

  return (
    <div className={`w-full bg-slate-700 rounded-full overflow-hidden ${height} ${className}`}>
      <div 
        className={`${getBarColor()} ${height} transition-all duration-300 ease-out`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}
