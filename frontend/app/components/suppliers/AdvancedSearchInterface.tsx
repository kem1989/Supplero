'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../lib/auth';

interface AdvancedSearchFilters {
  name?: string;
  industry?: string;
  country?: string;
  risk_level?: string;
  risk_score_min?: number;
  risk_score_max?: number;
  company_size?: string;
  is_watchlisted?: boolean;
  is_active?: boolean;
  has_contracts?: boolean;
}

interface SavedSearch {
  id: string;
  name: string;
  description?: string;
  filters: AdvancedSearchFilters;
  created_at: string;
  is_favorite: boolean;
  usage_count: number;
}

interface SearchHistory {
  id: string;
  query: string;
  filters: AdvancedSearchFilters;
  results_count: number;
  search_time_ms: number;
  created_at: string;
}

interface AdvancedSearchInterfaceProps {
  onSearch: (filters: AdvancedSearchFilters) => void;
  onClear: () => void;
  loading?: boolean;
  className?: string;
}

const RISK_LEVELS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
const COMPANY_SIZES = ['small', 'medium', 'large', 'enterprise'];

export default function AdvancedSearchInterface({
  onSearch,
  onClear,
  loading = false,
  className = ''
}: AdvancedSearchInterfaceProps) {
  const { user } = useAuth();
  const [filters, setFilters] = useState<AdvancedSearchFilters>({});
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([]);
  const [showSavedSearches, setShowSavedSearches] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const handleFilterChange = (key: keyof AdvancedSearchFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSearch = () => {
    onSearch(filters);
  };

  const handleClear = () => {
    setFilters({});
    onClear();
  };

  const hasActiveFilters = Object.values(filters).some(value => 
    value !== undefined && value !== '' && value !== null
  );

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Quick Actions Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowSavedSearches(!showSavedSearches)}
            className="px-3 py-2 text-sm bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            Saved Searches
          </button>
          
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="px-3 py-2 text-sm bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            History
          </button>
        </div>

        <div className="flex items-center space-x-3">
          {hasActiveFilters && (
            <button
              onClick={handleClear}
              className="px-3 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              Clear All
            </button>
          )}
          
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="px-3 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced
          </button>
        </div>
      </div>

      {/* Advanced Filters Panel */}
      {showAdvanced && (
        <div className="glass rounded-xl p-6 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">Advanced Search Filters</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Basic Information */}
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-slate-300">Basic Information</h4>
              
              <div>
                <label className="block text-xs text-slate-400 mb-1">Name</label>
                <input
                  type="text"
                  value={filters.name || ''}
                  onChange={(e) => handleFilterChange('name', e.target.value)}
                  placeholder="Supplier name"
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-xs text-slate-400 mb-1">Industry</label>
                <input
                  type="text"
                  value={filters.industry || ''}
                  onChange={(e) => handleFilterChange('industry', e.target.value)}
                  placeholder="e.g., Technology"
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-xs text-slate-400 mb-1">Country</label>
                <input
                  type="text"
                  value={filters.country || ''}
                  onChange={(e) => handleFilterChange('country', e.target.value)}
                  placeholder="e.g., United States"
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Risk Assessment */}
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-slate-300">Risk Assessment</h4>
              
              <div>
                <label className="block text-xs text-slate-400 mb-1">Risk Level</label>
                <select
                  value={filters.risk_level || ''}
                  onChange={(e) => handleFilterChange('risk_level', e.target.value || undefined)}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Any Risk Level</option>
                  {RISK_LEVELS.map(level => (
                    <option key={level} value={level}>{level}</option>
                  ))}
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Min Risk Score</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={filters.risk_score_min || ''}
                    onChange={(e) => handleFilterChange('risk_score_min', e.target.value ? Number(e.target.value) : undefined)}
                    placeholder="0"
                    className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Max Risk Score</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={filters.risk_score_max || ''}
                    onChange={(e) => handleFilterChange('risk_score_max', e.target.value ? Number(e.target.value) : undefined)}
                    placeholder="100"
                    className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Status & Business */}
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-slate-300">Status & Business</h4>
              
              <div>
                <label className="block text-xs text-slate-400 mb-1">Company Size</label>
                <select
                  value={filters.company_size || ''}
                  onChange={(e) => handleFilterChange('company_size', e.target.value || undefined)}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-600/50 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Any Size</option>
                  {COMPANY_SIZES.map(size => (
                    <option key={size} value={size}>{size.charAt(0).toUpperCase() + size.slice(1)}</option>
                  ))}
                </select>
              </div>
              
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.is_watchlisted || false}
                    onChange={(e) => handleFilterChange('is_watchlisted', e.target.checked ? true : undefined)}
                    className="mr-2 rounded border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-300">Watchlisted</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.is_active !== false}
                    onChange={(e) => handleFilterChange('is_active', e.target.checked ? true : undefined)}
                    className="mr-2 rounded border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-300">Active Only</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={filters.has_contracts || false}
                    onChange={(e) => handleFilterChange('has_contracts', e.target.checked ? true : undefined)}
                    className="mr-2 rounded border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-300">Has Contracts</span>
                </label>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between mt-6 pt-6 border-t border-slate-600/30">
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
            
            <div className="text-sm text-slate-400">
              {hasActiveFilters && (
                <span>Active filters: {Object.keys(filters).filter(k => filters[k as keyof AdvancedSearchFilters]).join(', ')}</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
