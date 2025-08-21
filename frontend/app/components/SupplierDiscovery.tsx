'use client';

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { api } from '../lib/auth';
import { SupplierCard, type SupplierCardData, AdvancedSearchInterface, type AdvancedSearchFilters } from './suppliers';

interface SupplierSearchResult {
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
  contract_insights?: {
    matching_contracts: Array<{
      document_id: string | number;
      filename: string;
      relevance_score?: number;
      key_excerpts?: string[];
      match_reasons?: string[];
      clause_badges?: string[];
      extracted_values?: Record<string, any>;
    }>;
    total_contracts?: number;
    confidence_score?: number;
  };
}

interface SearchResponse {
  suppliers: SupplierSearchResult[];
  total_count: number;
  search_time_ms: number;
  performance_met: boolean;
  search_strategy?: string;
  search_method?: string;
  fallback_reason?: string;
  statistics?: {
    total_suppliers_in_org: number;
    matched_suppliers: number;
    risk_level_distribution: Record<string, number>;
    industry_distribution: Record<string, number>;
    country_distribution: Record<string, number>;
    company_size_distribution: Record<string, number>;
    average_risk_score: number;
    watchlisted_suppliers: number;
  };
  ai_insights?: {
    summary: string;
    total_suppliers: number;
    high_risk_count: number;
    watchlisted_count: number;
    top_industries: string[];
  };
  query_processing?: {
    intent: string;
    confidence: number;
    confidence_threshold_met: boolean;
  };
}

const EXAMPLE_QUERIES = [
  "Find high-risk suppliers in pharmaceuticals",
  "Show me suppliers with contracts over $5 million",
  "Which suppliers have negative news coverage?",
  "Find suppliers in China with medium risk",
  "Large technology companies with low risk",
  "Watchlisted suppliers in manufacturing",
  "Recent supplier assessments this month",
  "European suppliers with high contract value",
  // NEW: Enhanced supplier-contract relationship examples
  "Show me suppliers with contracts over $100k",
  "Find suppliers with service contracts in technology",
  "Suppliers with contracts expiring in 30 days",
  "High-value contract suppliers in manufacturing",
  "Suppliers with payment terms net 60",
  "Contracts with suppliers in the healthcare industry",
  "Suppliers with multiple contracts over $1M",
  "Find suppliers with contracts in Europe over $500k"
];



export default function SupplierDiscovery() {
  const { user } = useAuth();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedExample, setSelectedExample] = useState<string>('');
  const [advancedFilters, setAdvancedFilters] = useState<AdvancedSearchFilters>({});
  const [useAdvancedSearch, setUseAdvancedSearch] = useState(false);

  const handleAdvancedSearch = async (filters: AdvancedSearchFilters) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setAdvancedFilters(filters);

    try {
      // Build query string from filters
      const filterQuery = buildFilterQuery(filters);
      
      // Use the unified AI assistant endpoint with advanced filters
      const response = await api.post('/ai-assistant/execute', {
        query: filterQuery,
        context: 'supplier_search',
        parameters: {
          filters: filters,
          search_type: 'advanced'
        }
      });
      
      const data = response.data;
      const executionResult = data.execution_result || data;
      
      // Handle different supplier response types: direct search, search_results, and risk_analyses
      if (executionResult.suppliers || executionResult.search_results?.suppliers || executionResult.risk_analyses) {
        const searchResults = executionResult.search_results || executionResult;
        
        // Extract suppliers from various response formats
        let suppliers = searchResults.suppliers || [];
        
        // If we have risk_analyses, extract supplier info from them
        if (executionResult.risk_analyses && !suppliers.length) {
          suppliers = executionResult.risk_analyses.map((analysis: any) => ({
            id: analysis.supplier_id || analysis.id,
            name: analysis.supplier_name || analysis.name,
            industry: analysis.industry,
            country: analysis.country,
            risk_score: analysis.risk_score || 0,
            risk_level: analysis.risk_level || 'UNKNOWN',
            is_active: true,
            is_watchlisted: analysis.is_watchlisted || false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }));
        }
        
        const transformedResult: SearchResponse = {
          suppliers: suppliers,
          total_count: searchResults.total_count || searchResults.total_found || executionResult.analysis_summary?.total_suppliers || suppliers.length,
          search_time_ms: searchResults.search_time_ms || data.execution_time_ms || 0,
          performance_met: searchResults.performance_met ?? true,
          search_strategy: searchResults.search_strategy,
          search_method: searchResults.search_method,
          fallback_reason: searchResults.fallback_reason,
          statistics: searchResults.statistics,
          ai_insights: searchResults.search_insights || {
            summary: `Found ${suppliers.length} suppliers matching your advanced search criteria.`,
            total_suppliers: suppliers.length,
            high_risk_count: suppliers.filter(s => s.risk_level === 'HIGH' || s.risk_level === 'CRITICAL').length,
            watchlisted_count: suppliers.filter(s => s.is_watchlisted).length,
            top_industries: Array.from(new Set(suppliers.map(s => s.industry).filter(Boolean))).slice(0, 3)
          },
          query_processing: searchResults.query_processing || {
            intent: 'advanced_supplier_search',
            confidence: 1.0,
            confidence_threshold_met: true
          }
        };
        
        setResults(transformedResult);
      } else {
        setError('This query doesn\'t appear to be related to supplier search. Please try a supplier-focused query.');
      }
    } catch (err: any) {
      console.error('Advanced search error:', err);
      const errorMessage = err?.response?.data?.detail || err.message || 'Advanced search failed. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const buildFilterQuery = (filters: AdvancedSearchFilters): string => {
    const parts: string[] = [];
    
    if (filters.name) parts.push(`name: ${filters.name}`);
    if (filters.industry) parts.push(`industry: ${filters.industry}`);
    if (filters.country) parts.push(`country: ${filters.country}`);
    if (filters.risk_level) parts.push(`risk level: ${filters.risk_level}`);
    if (filters.company_size) parts.push(`company size: ${filters.company_size}`);
    if (filters.is_watchlisted) parts.push('watchlisted suppliers');
    if (filters.has_contracts) parts.push('suppliers with contracts');
    
    return parts.length > 0 ? parts.join(', ') : 'all suppliers';
  };

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      // Use the unified AI assistant endpoint which routes supplier queries appropriately
      const response = await api.post('/ai-assistant/execute', {
        query: query.trim(),
        user_context: null
      });

      const data = response.data;
      console.log('Raw API response:', data);
      
      // Transform unified endpoint response to match SupplierDiscovery interface
      // The actual handler response is in data.result, not data.execution_result
      const executionResult = data.result || {};
      
      // Check if this is a supplier-related result
      // Handle different supplier response types: direct search, search_results, and risk_analyses
      if (executionResult.suppliers || executionResult.search_results?.suppliers || executionResult.risk_analyses) {
        const searchResults = executionResult.search_results || executionResult;
        
        // Transform risk analysis results to supplier format if needed
        let suppliers = searchResults.suppliers || [];
        if (executionResult.risk_analyses && !suppliers.length) {
          suppliers = executionResult.risk_analyses.map((analysis: any) => ({
            id: analysis.supplier_id,
            name: analysis.supplier_name,
            risk_score: analysis.current_risk_score,
            risk_level: analysis.current_risk_level,
            industry: analysis.risk_factors?.industry_risk?.industry || null,
            country: analysis.risk_factors?.country_risk?.country || null,
            is_watchlisted: false,
            company_size: analysis.risk_factors?.size_risk?.company_size || null,
            contact_email: null,
            last_risk_assessment: analysis.last_assessment
          }));
        }
        // Preserve semantic contract insights if present
        if (Array.isArray(suppliers)) {
          suppliers = suppliers.map((s: any) => ({
            ...s,
            contract_insights: s.contract_insights || undefined,
          }));
        }
        
        const transformedResult: SearchResponse = {
          suppliers: suppliers,
          total_count: searchResults.total_count || searchResults.total_found || executionResult.analysis_summary?.total_suppliers || suppliers.length,
          search_time_ms: searchResults.search_time_ms || data.execution_time_ms || 0,
          performance_met: searchResults.performance_met ?? true,
          search_strategy: searchResults.search_strategy,
          search_method: searchResults.search_method,
          fallback_reason: searchResults.fallback_reason,
          statistics: searchResults.statistics,
          ai_insights: searchResults.search_insights || {
            summary: executionResult.message || `Found ${suppliers.length} suppliers`,
            total_suppliers: suppliers.length,
            average_risk_score: executionResult.analysis_summary?.average_risk_score || 0,
            high_risk_count: executionResult.analysis_summary?.high_risk_count || 0,
            risk_distribution: executionResult.risk_distribution
          },
          query_processing: {
            intent: data.tool_name || 'unknown',
            confidence: executionResult.intent_classification?.confidence || 1.0,
            confidence_threshold_met: true
          }
        };
        
        setResults(transformedResult);
      } else {
        // Handle non-supplier responses
        console.log('Execution result structure:', executionResult); // Debug log
        setError('This query doesn\'t appear to be related to supplier search. Please try a supplier-focused query.');
      }

    } catch (err: any) {
      console.error('Search error:', err);
      const errorMessage = err?.response?.data?.detail || err.message || 'Search failed. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
    setSelectedExample(example);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleViewDetails = (supplier: SupplierCardData) => {
    // TODO: Navigate to supplier details page
    console.log('View details for supplier:', supplier.name);
    // Example: router.push(`/suppliers/${supplier.id}`);
  };

  const handleAnalyzeRisk = (supplier: SupplierCardData) => {
    // TODO: Open risk analysis modal or navigate to risk analysis page
    console.log('Analyze risk for supplier:', supplier.name);
    // Example: setShowRiskAnalysis(supplier);
  };

  const handleToggleWatchlist = async (supplier: SupplierCardData) => {
    try {
      // TODO: Implement watchlist toggle API call
      console.log(`${supplier.is_watchlisted ? 'Remove from' : 'Add to'} watchlist:`, supplier.name);
      
      // Example API call:
      // await api.post(`/suppliers/${supplier.id}/watchlist`, {
      //   action: supplier.is_watchlisted ? 'remove' : 'add'
      // });
      
      // Refresh results to show updated status
      // handleSearch();
    } catch (error) {
      console.error('Failed to toggle watchlist:', error);
    }
  };

  const handleClear = () => {
    setQuery('');
    setResults(null);
    setError(null);
    setSelectedExample('');
  };

  const handleAdvancedClear = () => {
    setAdvancedFilters({});
    setResults(null);
    setError(null);
  };



  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        {/* Navigation Header */}
        <div className="glass border-b border-white/10 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center space-x-4">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <h1 className="text-xl font-bold text-white">Supplier Discovery</h1>
                <div className="flex items-center space-x-4 text-sm">
                  <a href="/dashboard" className="text-slate-400 hover:text-blue-400 transition-colors flex items-center space-x-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                    <span>Dashboard</span>
                  </a>
                  <a href="/suppliers" className="text-slate-400 hover:text-blue-400 transition-colors flex items-center space-x-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    <span>Supplier Management</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto p-6">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Intelligent Supplier Search</h1>
            <p className="text-slate-300">
              Use natural language to find suppliers, analyze risk, and discover insights across your supplier portfolio.
            </p>
          </div>

          {/* Search Interface */}
          <div className="glass rounded-2xl p-6 border border-white/10 mb-6">
            {/* Search Type Toggle */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setUseAdvancedSearch(false)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    !useAdvancedSearch
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  Natural Language Search
                </button>
                <button
                  onClick={() => setUseAdvancedSearch(true)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    useAdvancedSearch
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  Advanced Search
                </button>
              </div>
            </div>

            {!useAdvancedSearch ? (
              <div className="space-y-4">
                {/* Natural Language Search Input */}
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask anything about your suppliers... e.g., 'Find high-risk suppliers in China with recent assessments'"
                    className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-600/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

              {/* Search Button */}
              <div className="flex justify-between items-center">
                <button
                  onClick={handleSearch}
                  disabled={loading || !query.trim()}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:opacity-50 text-white rounded-lg font-medium transition-colors flex items-center space-x-2"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span>Searching...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                      <span>Search Suppliers</span>
                    </>
                  )}
                </button>

                {results && (
                  <div className="text-sm text-slate-400">
                    {results.total_count} suppliers found in {results.search_time_ms}ms
                    {!results.performance_met && (
                      <span className="text-yellow-400 ml-2">⚠ Slower than expected</span>
                    )}
                  </div>
                )}
              </div>
            </div>
            ) : (
              <AdvancedSearchInterface
                onSearch={handleAdvancedSearch}
                onClear={handleAdvancedClear}
                loading={loading}
              />
            )}

            {/* Example Queries - Only show for natural language search */}
            {!useAdvancedSearch && (
              <div className="mt-6 pt-6 border-t border-slate-600/30">
                <h3 className="text-sm font-medium text-slate-300 mb-3">Try these examples:</h3>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                  {EXAMPLE_QUERIES.map((example, index) => (
                    <button
                      key={index}
                      onClick={() => handleExampleClick(example)}
                      className={`text-left p-2 rounded-lg text-xs transition-colors ${
                        selectedExample === example
                          ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                          : 'bg-slate-800/50 text-slate-400 hover:bg-slate-700/50 hover:text-slate-300 border border-transparent'
                      }`}
                    >
                      "{example}"
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="glass rounded-lg p-4 border border-red-500/20 bg-red-500/5 mb-6">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-red-400 font-medium">Search Error</span>
              </div>
              <p className="text-red-300 mt-1 text-sm">{error}</p>
            </div>
          )}

          {/* Results */}
          {results && (
            <div className="space-y-6">
              {/* Search Insights */}
              {(results.ai_insights || results.statistics) && (
                <div className="glass rounded-xl p-6 border border-white/10">
                  <h3 className="text-lg font-semibold text-white mb-4">Search Insights</h3>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {results.ai_insights && (
                      <>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-400">{results.ai_insights.total_suppliers}</div>
                          <div className="text-xs text-slate-400">Total Suppliers</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-red-400">{results.ai_insights.high_risk_count}</div>
                          <div className="text-xs text-slate-400">High Risk</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-yellow-400">{results.ai_insights.watchlisted_count}</div>
                          <div className="text-xs text-slate-400">Watchlisted</div>
                        </div>
                      </>
                    )}
                    {results.statistics && (
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-400">{Math.round(results.statistics.average_risk_score)}</div>
                        <div className="text-xs text-slate-400">Avg Risk Score</div>
                      </div>
                    )}
                  </div>
                  
                  {results.ai_insights?.summary && (
                    <div className="mt-4 p-3 bg-slate-800/30 rounded-lg border border-slate-600/20">
                      <p className="text-slate-300 text-sm">{results.ai_insights.summary}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Results Header */}
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-semibold text-white">
                  Supplier Results ({results.total_count})
                </h3>
                
                {results.query_processing && (
                  <div className="text-sm text-slate-400">
                    Intent: {results.query_processing.intent} 
                    <span className={`ml-2 ${results.query_processing.confidence_threshold_met ? 'text-green-400' : 'text-yellow-400'}`}>
                      ({Math.round(results.query_processing.confidence * 100)}%)
                    </span>
                  </div>
                )}
              </div>
              
              {/* Results List */}
              {results.suppliers.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <svg className="mx-auto h-12 w-12 text-slate-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  <p className="text-lg font-medium">No suppliers found matching your search criteria.</p>
                  <p className="text-sm mt-1">Try adjusting your query or using different keywords.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {results.suppliers.map((supplier) => (
                    <div key={supplier.id} className="space-y-2">
                      <SupplierCard
                        supplier={supplier as SupplierCardData}
                        variant="default"
                        showMetrics={true}
                        showActions={true}
                        onViewDetails={handleViewDetails}
                        onAnalyzeRisk={handleAnalyzeRisk}
                        onToggleWatchlist={handleToggleWatchlist}
                      />
                      {supplier.contract_insights?.matching_contracts?.length ? (
                        <div className="ml-4 p-3 bg-slate-800/40 rounded-lg border border-slate-600/30">
                          <div className="text-xs text-slate-400 mb-2">
                            Matching Contracts ({supplier.contract_insights.total_contracts})
                            {supplier.contract_insights.confidence_score ? (
                              <span className="ml-2 text-blue-400">Top score: {Math.round((supplier.contract_insights.confidence_score || 0) * 100)}%</span>
                            ) : null}
                          </div>
                          <div className="space-y-3">
                            {supplier.contract_insights.matching_contracts.slice(0, 3).map((c: any, idx: number) => (
                              <div key={`${c.document_id}-${idx}`} className="text-xs text-slate-300">
                                <div className="flex items-center justify-between">
                                  <div className="font-semibold text-slate-200">{c.filename}</div>
                                  {typeof c.relevance_score === 'number' && (
                                    <div className="text-blue-400">{Math.round(c.relevance_score * 100)}%</div>
                                  )}
                                </div>
                                {c.clause_badges?.length ? (
                                  <div className="mt-1 flex flex-wrap gap-1">
                                    {c.clause_badges.slice(0, 4).map((b: string, i: number) => (
                                      <span key={i} className="px-2 py-0.5 bg-slate-700/60 border border-slate-600/60 rounded-full text-[10px] text-slate-300">{b}</span>
                                    ))}
                                  </div>
                                ) : null}
                                {c.key_excerpts?.length ? (
                                  <div className="mt-2 space-y-1">
                                    {c.key_excerpts.slice(0, 2).map((ex: string, i: number) => (
                                      <p key={i} className="italic text-slate-400">“{ex}”</p>
                                    ))}
                                  </div>
                                ) : null}
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
