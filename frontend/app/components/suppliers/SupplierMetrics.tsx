'use client';

import React from 'react';

export interface SupplierMetric {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    direction: 'up' | 'down' | 'neutral';
    percentage?: number;
    label?: string;
  };
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'slate';
  highlight?: boolean;
}

export interface SupplierMetricsProps {
  metrics: SupplierMetric[];
  layout?: 'grid' | 'horizontal' | 'vertical';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const COLOR_CLASSES = {
  blue: {
    text: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20'
  },
  green: {
    text: 'text-green-400',
    bg: 'bg-green-500/10',
    border: 'border-green-500/20'
  },
  yellow: {
    text: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/20'
  },
  red: {
    text: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/20'
  },
  slate: {
    text: 'text-slate-400',
    bg: 'bg-slate-500/10',
    border: 'border-slate-500/20'
  }
};

const SIZE_CLASSES = {
  sm: {
    container: 'p-3',
    value: 'text-lg',
    label: 'text-xs',
    icon: 'w-4 h-4'
  },
  md: {
    container: 'p-4',
    value: 'text-2xl',
    label: 'text-sm',
    icon: 'w-5 h-5'
  },
  lg: {
    container: 'p-6',
    value: 'text-3xl',
    label: 'text-base',
    icon: 'w-6 h-6'
  }
};

export default function SupplierMetrics({
  metrics,
  layout = 'grid',
  size = 'md',
  className = ''
}: SupplierMetricsProps) {
  const sizeClasses = SIZE_CLASSES[size];

  const formatValue = (value: string | number): string => {
    if (typeof value === 'number') {
      // Format large numbers with K, M, B suffixes
      if (value >= 1000000000) {
        return `${(value / 1000000000).toFixed(1)}B`;
      } else if (value >= 1000000) {
        return `${(value / 1000000).toFixed(1)}M`;
      } else if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}K`;
      } else {
        return value.toLocaleString();
      }
    }
    return String(value);
  };

  const getTrendIcon = (direction: 'up' | 'down' | 'neutral') => {
    switch (direction) {
      case 'up':
        return (
          <svg className="w-3 h-3 text-green-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M7 14l5-5 5 5z"/>
          </svg>
        );
      case 'down':
        return (
          <svg className="w-3 h-3 text-red-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M7 10l5 5 5-5z"/>
          </svg>
        );
      case 'neutral':
        return (
          <svg className="w-3 h-3 text-slate-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 7h-2v5H7l5 5 5-5h-3V7z"/>
          </svg>
        );
      default:
        return null;
    }
  };

  const getLayoutClasses = () => {
    switch (layout) {
      case 'horizontal':
        return 'flex space-x-4 overflow-x-auto';
      case 'vertical':
        return 'flex flex-col space-y-4';
      case 'grid':
      default:
        return `grid gap-4 ${
          metrics.length <= 2 ? 'grid-cols-1 md:grid-cols-2' :
          metrics.length <= 4 ? 'grid-cols-2 lg:grid-cols-4' :
          'grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
        }`;
    }
  };

  return (
    <div className={`${getLayoutClasses()} ${className}`}>
      {metrics.map((metric, index) => {
        const color = COLOR_CLASSES[metric.color || 'slate'];
        const isHighlighted = metric.highlight;

        return (
          <div
            key={index}
            className={`
              glass rounded-lg border transition-all duration-200
              ${sizeClasses.container}
              ${isHighlighted ? 
                `${color.bg} ${color.border} ring-1 ring-opacity-20 ${color.text.replace('text-', 'ring-')}` :
                'bg-slate-800/30 border-slate-600/30 hover:bg-slate-800/50'
              }
            `}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                {/* Value */}
                <div className={`
                  font-bold tracking-tight
                  ${sizeClasses.value}
                  ${isHighlighted ? color.text : 'text-white'}
                `}>
                  {formatValue(metric.value)}
                </div>

                {/* Label */}
                <div className={`
                  font-medium mt-1
                  ${sizeClasses.label}
                  ${isHighlighted ? color.text.replace('400', '300') : 'text-slate-400'}
                `}>
                  {metric.label}
                </div>

                {/* Trend */}
                {metric.trend && (
                  <div className="flex items-center space-x-1 mt-2">
                    {getTrendIcon(metric.trend.direction)}
                    <span className={`
                      text-xs font-medium
                      ${metric.trend.direction === 'up' ? 'text-green-400' :
                        metric.trend.direction === 'down' ? 'text-red-400' :
                        'text-slate-400'
                      }
                    `}>
                      {metric.trend.percentage && `${metric.trend.percentage}%`}
                      {metric.trend.label && (
                        <span className="text-slate-500 ml-1">
                          {metric.trend.label}
                        </span>
                      )}
                    </span>
                  </div>
                )}
              </div>

              {/* Icon */}
              {metric.icon && (
                <div className={`
                  flex-shrink-0 ml-3
                  ${sizeClasses.icon}
                  ${isHighlighted ? color.text : 'text-slate-400'}
                `}>
                  {metric.icon}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Predefined metric builders for common supplier metrics
export const createContractMetric = (count: number, totalValue?: number): SupplierMetric => ({
  label: 'Active Contracts',
  value: count,
  icon: (
    <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  color: 'blue'
});

export const createValueMetric = (value: number): SupplierMetric => ({
  label: 'Contract Value',
  value: `$${value >= 1000000 ? `${(value / 1000000).toFixed(1)}M` : 
         value >= 1000 ? `${(value / 1000).toFixed(1)}K` : 
         value.toLocaleString()}`,
  icon: (
    <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
    </svg>
  ),
  color: 'green'
});

export const createRiskMetric = (riskScore: number, riskLevel: string): SupplierMetric => ({
  label: 'Risk Score',
  value: Math.round(riskScore),
  icon: (
    <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
  color: riskLevel === 'CRITICAL' || riskLevel === 'HIGH' ? 'red' :
         riskLevel === 'MEDIUM' ? 'yellow' : 'green',
  highlight: riskLevel === 'CRITICAL' || riskLevel === 'HIGH'
});

export const createEmployeeMetric = (count: number): SupplierMetric => ({
  label: 'Employees',
  value: count,
  icon: (
    <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  ),
  color: 'blue'
});

export const createAssessmentMetric = (lastAssessment: string): SupplierMetric => {
  const daysAgo = Math.floor((Date.now() - new Date(lastAssessment).getTime()) / (1000 * 60 * 60 * 24));
  
  return {
    label: 'Last Assessment',
    value: `${daysAgo}d ago`,
    icon: (
      <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: daysAgo > 90 ? 'red' : daysAgo > 30 ? 'yellow' : 'green',
    highlight: daysAgo > 90
  };
};
