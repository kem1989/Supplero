'use client';

import React, { useState } from 'react';
import RiskIndicator, { RiskDot } from './RiskIndicator';
import SupplierMetrics, { 
  createContractMetric, 
  createValueMetric, 
  createRiskMetric, 
  createEmployeeMetric, 
  createAssessmentMetric,
  type SupplierMetric 
} from './SupplierMetrics';

export interface SupplierCardData {
  id: number;
  name: string;
  industry?: string;
  location?: string;
  country?: string;
  contact_email?: string;
  contact_phone?: string;
  website?: string;
  company_size?: string;
  employee_count?: number;
  revenue_range?: string;
  risk_score: number;
  risk_level: string;
  risk_factors?: any;
  is_active: boolean;
  is_watchlisted: boolean;
  watchlist_reason?: string;
  last_risk_assessment?: string;
  created_at: string;
  updated_at: string;
  relevance_score?: number;
  contract_count?: number;
  total_contract_value?: number;
  latest_contract_date?: string;
  match_reasons?: string[];
  key_highlights?: string[];
}

export interface SupplierCardProps {
  supplier: SupplierCardData;
  variant?: 'default' | 'compact' | 'detailed';
  showMetrics?: boolean;
  showActions?: boolean;
  onViewDetails?: (supplier: SupplierCardData) => void;
  onAnalyzeRisk?: (supplier: SupplierCardData) => void;
  onEditSupplier?: (supplier: SupplierCardData) => void;
  onToggleWatchlist?: (supplier: SupplierCardData) => void;
  className?: string;
}

export default function SupplierCard({
  supplier,
  variant = 'default',
  showMetrics = true,
  showActions = true,
  onViewDetails,
  onAnalyzeRisk,
  onEditSupplier,
  onToggleWatchlist,
  className = ''
}: SupplierCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getSupplierMetrics = (): SupplierMetric[] => {
    const metrics: SupplierMetric[] = [];

    if (supplier.contract_count !== undefined) {
      metrics.push(createContractMetric(supplier.contract_count, supplier.total_contract_value));
    }

    if (supplier.total_contract_value && supplier.total_contract_value > 0) {
      metrics.push(createValueMetric(supplier.total_contract_value));
    }

    metrics.push(createRiskMetric(supplier.risk_score, supplier.risk_level));

    if (supplier.employee_count) {
      metrics.push(createEmployeeMetric(supplier.employee_count));
    }

    if (supplier.last_risk_assessment) {
      metrics.push(createAssessmentMetric(supplier.last_risk_assessment));
    }

    return metrics;
  };

  const getCardClasses = () => {
    const baseClasses = "glass rounded-lg border transition-all duration-200 bg-slate-800/30 hover:bg-slate-800/50";
    
    switch (variant) {
      case 'compact':
        return `${baseClasses} p-4 border-slate-600/50`;
      case 'detailed':
        return `${baseClasses} p-6 border-slate-600/50 hover:shadow-lg`;
      default:
        return `${baseClasses} p-6 border-slate-600/50 hover:shadow-md`;
    }
  };

  // Compact variant for list views
  if (variant === 'compact') {
    return (
      <div className={`${getCardClasses()} ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <RiskDot riskLevel={supplier.risk_level} size="sm" />
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-white truncate">{supplier.name}</h4>
              <div className="flex items-center space-x-4 text-sm text-slate-400">
                {supplier.industry && <span>{supplier.industry}</span>}
                {supplier.location && <span>{supplier.location}</span>}
                {supplier.contract_count !== undefined && (
                  <span>{supplier.contract_count} contracts</span>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            {supplier.is_watchlisted && (
              <svg className="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
            )}
            <RiskIndicator 
              riskLevel={supplier.risk_level} 
              riskScore={supplier.risk_score} 
              size="sm" 
              showLabel={false}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${getCardClasses()} ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-3 mb-2">
            <h4 className="font-semibold text-white text-lg truncate">{supplier.name}</h4>
            {supplier.is_watchlisted && (
              <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs rounded-full border border-yellow-500/30 flex items-center space-x-1">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
                <span>Watchlisted</span>
              </span>
            )}
            {!supplier.is_active && (
              <span className="px-2 py-1 bg-slate-500/20 text-slate-400 text-xs rounded-full border border-slate-500/30">
                Inactive
              </span>
            )}
          </div>
          
          {/* Basic Info Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm text-slate-400">
            {supplier.industry && (
              <div>
                <span className="text-slate-500">Industry:</span>
                <span className="ml-1 text-slate-300">{supplier.industry}</span>
              </div>
            )}
            {supplier.location && (
              <div>
                <span className="text-slate-500">Location:</span>
                <span className="ml-1 text-slate-300">{supplier.location}</span>
              </div>
            )}
            {supplier.company_size && (
              <div>
                <span className="text-slate-500">Size:</span>
                <span className="ml-1 text-slate-300 capitalize">{supplier.company_size}</span>
              </div>
            )}
            {supplier.contract_count !== undefined && (
              <div>
                <span className="text-slate-500">Contracts:</span>
                <span className="ml-1 text-slate-300">{supplier.contract_count}</span>
              </div>
            )}
          </div>
          
          {/* Contact Info */}
          {supplier.contact_email && (
            <div className="mt-2 text-sm">
              <span className="text-slate-500">Contact:</span>
              <span className="ml-1 text-blue-400">{supplier.contact_email}</span>
            </div>
          )}
        </div>
        
        {/* Risk Indicator */}
        <div className="flex-shrink-0 ml-4">
          <RiskIndicator 
            riskLevel={supplier.risk_level} 
            riskScore={supplier.risk_score}
            size="md"
          />
        </div>
      </div>

      {/* Metrics Section */}
      {showMetrics && variant === 'detailed' && (
        <div className="mb-4">
          <SupplierMetrics 
            metrics={getSupplierMetrics()} 
            layout="horizontal"
            size="sm"
          />
        </div>
      )}

      {/* Additional Details (Expandable) */}
      {variant === 'detailed' && (
        <div className="border-t border-slate-600/30 pt-4">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center justify-between w-full text-left text-sm text-slate-400 hover:text-slate-300 transition-colors"
          >
            <span>Additional Details</span>
            <svg 
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {isExpanded && (
            <div className="mt-3 space-y-3 text-sm">
              {supplier.revenue_range && (
                <div>
                  <span className="text-slate-500">Revenue Range:</span>
                  <span className="ml-1 text-slate-300">{supplier.revenue_range}</span>
                </div>
              )}
              
              {supplier.website && (
                <div>
                  <span className="text-slate-500">Website:</span>
                  <a 
                    href={supplier.website} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="ml-1 text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    {supplier.website}
                  </a>
                </div>
              )}
              
              {supplier.contact_phone && (
                <div>
                  <span className="text-slate-500">Phone:</span>
                  <span className="ml-1 text-slate-300">{supplier.contact_phone}</span>
                </div>
              )}
              
              {supplier.watchlist_reason && (
                <div>
                  <span className="text-slate-500">Watchlist Reason:</span>
                  <span className="ml-1 text-yellow-300">{supplier.watchlist_reason}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="pt-4 border-t border-slate-600/30">
        <div className="flex justify-between items-center text-sm">
          <div className="flex space-x-6 text-slate-400">
            {supplier.total_contract_value && supplier.total_contract_value > 0 && (
              <span>Value: {formatCurrency(supplier.total_contract_value)}</span>
            )}
            {supplier.last_risk_assessment && (
              <span>Last Assessment: {formatDate(supplier.last_risk_assessment)}</span>
            )}
            {supplier.employee_count && (
              <span>Employees: {supplier.employee_count.toLocaleString()}</span>
            )}
            {supplier.relevance_score && (
              <span className="text-blue-400">
                Match: {Math.round(supplier.relevance_score * 100)}%
              </span>
            )}
          </div>
          
          {/* Action Buttons */}
          {showActions && (
            <div className="flex space-x-2">
              <button 
                onClick={() => onViewDetails?.(supplier)}
                className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs rounded transition-colors"
              >
                View Details
              </button>
              <button 
                onClick={() => onAnalyzeRisk?.(supplier)}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
              >
                Analyze Risk
              </button>
              {onToggleWatchlist && (
                <button 
                  onClick={() => onToggleWatchlist(supplier)}
                  className={`px-3 py-1 text-xs rounded transition-colors ${
                    supplier.is_watchlisted
                      ? 'bg-yellow-600 hover:bg-yellow-700 text-white'
                      : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
                  }`}
                >
                  {supplier.is_watchlisted ? 'Unwatch' : 'Watch'}
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Match Highlights */}
      {supplier.key_highlights && supplier.key_highlights.length > 0 && (
        <div className="mt-3 p-3 bg-slate-800/50 rounded-lg border border-slate-600/20">
          <h5 className="text-xs font-medium text-slate-400 mb-2">Key Highlights:</h5>
          <div className="space-y-1">
            {supplier.key_highlights.slice(0, 3).map((highlight, idx) => (
              <p key={idx} className="text-xs text-slate-300">• {highlight}</p>
            ))}
            {supplier.key_highlights.length > 3 && (
              <p className="text-xs text-slate-500">
                +{supplier.key_highlights.length - 3} more highlights
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
