'use client';

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { api } from '../lib/auth';

interface SearchResult {
  documents: Array<{
    id?: string | number;
    document_id?: string;
    filename: string;
    original_filename?: string;
    supplier_name?: string;
    contract_amount?: number;
    currency?: string;
    contract_type?: string;
    risk_level?: string;
    status?: string;
    score?: number;
    relevance_score?: number;
    extracted_text?: string;
    match_reasons?: string[];
    key_excerpts?: string[];
    search_highlights?: string[];
    contract_date?: string;
  }>;
  total_count: number;
  search_time_ms: number;
  performance_met: boolean;
  search_strategy?: string;
  search_method?: string;
  fallback_reason?: string;
  clause_analysis?: {
    clause_findings: Array<{
      clause_type: string;
      risk_level: string;
      details: string;
      extracted_text: string;
    }>;
    risk_indicators: string[];
    recommendations: string[];
  };
  ai_insights?: {
    summary: string;
    total_contracts: number;
    total_value: number;
    suppliers_count: number;
  };
  query_processing?: {
    intent: string;
    confidence: number;
    extracted_parameters: Record<string, any>;
    confidence_threshold_met: boolean;
  };
}

export default function ContractDiscovery() {
  const { user } = useAuth();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      // Use the unified endpoint which automatically routes queries to the right service
      const response = await api.post('/ai-assistant/execute', {
        query: query.trim(),
        user_context: null
      });

      const data = response.data;
      console.log('Raw API response:', data); // Debug log
      console.log('Documents from API:', data.execution_result?.search_results?.documents); // Debug documents
      
      // Transform unified endpoint response to match SearchResult interface
      const searchResults = data.execution_result?.search_results || {};
      const transformedResult: SearchResult = {
        documents: searchResults.documents || [],
        total_count: searchResults.total_count || 0,
        search_time_ms: searchResults.search_time_ms || data.execution_time_ms || 0,
        performance_met: searchResults.performance_met || (data.execution_time_ms || 0) < 500,
        search_strategy: searchResults.search_strategy,
        search_method: searchResults.search_method,
        fallback_reason: searchResults.fallback_reason,
        ai_insights: {
          summary: `Query processed as: ${data.intent || 'unknown'}`,
          total_contracts: searchResults.total_count || 0,
          total_value: (searchResults.documents || []).reduce((sum: number, doc: any) => 
            sum + (doc.contract_amount || 0), 0),
          suppliers_count: new Set(
            (searchResults.documents || []).map((d: any) => d.supplier_name || d.filename)
          ).size
        },
        query_processing: {
          intent: data.intent || 'unknown',
          confidence: data.confidence || 0,
          extracted_parameters: data.execution_result?.parameters_used || {},
          confidence_threshold_met: (data.confidence || 0) >= 0.9
        },
        clause_analysis: searchResults.clause_analysis
      };
      
      console.log('Transformed result:', transformedResult); // Debug log
      console.log('Transformed documents:', transformedResult.documents); // Debug transformed documents
      setResults(transformedResult);
    } catch (err: any) {
      console.error('Search error:', err);
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('Search failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const exampleQueries = [
    "Find contracts with semiconductor suppliers that have ISO 9001 certification",
    "Show me contracts with force majeure clauses and penalty terms",
    "Which agreements have confidentiality terms longer than 3 years?",
    "Find contracts with automotive suppliers over $100,000",
    "Show contracts requiring quality certifications and warranty clauses",
    "Find agreements with intellectual property restrictions",
    "Which contracts have termination clauses with notice periods?",
    "Show contracts with dispute resolution through arbitration",
    "Find suppliers with compliance certifications and liability coverage",
    "Which agreements have performance metrics and penalty clauses?",
    "Show contracts with export control restrictions",
    "Find agreements with non-compete clauses longer than 2 years"
  ];

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
                <h1 className="text-xl font-bold text-white">Contract Discovery</h1>
                <a
                  href="/dashboard"
                  className="text-sm text-slate-400 hover:text-blue-400 transition-colors flex items-center space-x-1"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  <span>Back to Dashboard</span>
                </a>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-white">
                      {user?.first_name?.[0] || user?.username?.[0] || 'U'}
                    </span>
                  </div>
                  <div className="hidden md:block">
                    <p className="text-sm font-medium text-white">
                      {user?.first_name || user?.username}
                    </p>
                    <p className="text-xs text-slate-400">{user?.role}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-6xl mx-auto p-6">
          <div className="glass rounded-2xl p-6 border border-white/10">
            <h1 className="text-3xl font-bold text-white mb-6">
              🔍 Contract Discovery Engine
            </h1>
        
                  <div className="mb-8">
            <p className="text-slate-300 mb-4">
              Use natural language to search for contracts and analyze clauses. The AI will understand your query, 
              automatically route it to the right service, and provide intelligent results including risk analysis, 
              compliance gaps, and clause comparisons.
            </p>
            
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Find contracts with supplier ABC Corp over $50,000"
                className="flex-1 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-slate-500"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <button
                onClick={handleSearch}
                disabled={loading || !query.trim()}
                className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>

          <div className="mb-4">
            <p className="text-sm text-slate-400 mb-2">Try these example queries:</p>
            <div className="flex flex-wrap gap-2">
              {exampleQueries.map((example, index) => (
                <button
                  key={index}
                  onClick={() => setQuery(example)}
                  className="px-3 py-1 text-sm bg-slate-700/50 text-slate-300 rounded-full hover:bg-slate-600/50 transition-colors border border-slate-600/50"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {results && (
          <div className="space-y-6">
            {/* Performance Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-blue-800">Search Time</h3>
                <p className="text-2xl font-bold text-blue-900">
                  {results.search_time_ms.toFixed(1)}ms
                </p>
                <p className={`text-sm ${results.performance_met ? 'text-green-600' : 'text-red-600'}`}>
                  {results.performance_met ? '✅ <500ms requirement met' : '❌ Above 500ms threshold'}
                </p>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-green-800">Results Found</h3>
                <p className="text-2xl font-bold text-green-900">{results.total_count}</p>
                <p className="text-sm text-green-600">Contracts</p>
              </div>
              
              {results.ai_insights && (
                <div className="bg-purple-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-purple-800">Total Value</h3>
                  <p className="text-2xl font-bold text-purple-900">
                    ${results.ai_insights.total_value.toLocaleString()}
                  </p>
                  <p className="text-sm text-purple-600">Across all contracts</p>
                </div>
              )}
              
              {results.ai_insights && (
                <div className="bg-orange-50 p-4 rounded-lg">
                  <h3 className="text-sm font-medium text-orange-800">Suppliers</h3>
                  <p className="text-2xl font-bold text-orange-900">{results.ai_insights.suppliers_count}</p>
                  <p className="text-sm text-orange-600">Unique suppliers</p>
                </div>
              )}
            </div>

            {/* Query Processing Info */}
            {results.query_processing && (
              <div className="bg-slate-800/30 p-4 rounded-lg border border-slate-600/50">
                <h3 className="text-lg font-semibold text-white mb-3">Query Processing</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-slate-400">Intent Detected</p>
                    <p className="font-medium text-white">{results.query_processing.intent}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">Confidence</p>
                    <p className="font-medium text-white">
                      {(results.query_processing.confidence * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400">Threshold Met</p>
                    <p className={`font-medium ${results.query_processing.confidence_threshold_met ? 'text-green-400' : 'text-red-400'}`}>
                      {results.query_processing.confidence_threshold_met ? 'Yes' : 'No'}
                    </p>
                  </div>
                </div>
                
                {Object.keys(results.query_processing.extracted_parameters).length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm text-slate-400 mb-2">Extracted Parameters:</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(results.query_processing.extracted_parameters).map(([key, value]) => (
                        <span key={key} className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
                          {key}: {String(value)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* RAG Search Strategy Info */}
            {(results.search_strategy || results.search_method) && (
              <div className="bg-gradient-to-r from-green-500/10 to-blue-500/10 p-4 rounded-lg border border-green-500/20">
                <h3 className="text-lg font-semibold text-white mb-3">🔍 Search Strategy</h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                      results.search_strategy === 'RAG_FALLBACK' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {results.search_strategy === 'RAG_FALLBACK' 
                        ? '🤖 RAG Semantic Search' 
                        : '⚡ Elasticsearch Search'}
                    </div>
                    <div className="text-sm text-slate-400">
                      {results.search_strategy === 'RAG_FALLBACK' 
                        ? 'AI-powered semantic document analysis'
                        : 'Fast indexed keyword search'}
                    </div>
                  </div>
                  
                  {results.fallback_reason && (
                    <div className="bg-slate-800/50 p-3 rounded-lg">
                      <div className="text-sm text-slate-300">
                        <span className="text-yellow-400">⚠️ Fallback Reason:</span> {results.fallback_reason}
                      </div>
                    </div>
                  )}
                  
                  {results.search_method && (
                    <div className="text-sm text-slate-400">
                      Search Method: <span className="text-slate-300">{results.search_method}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Clause Analysis Results */}
            {results.clause_analysis && Object.keys(results.clause_analysis).length > 0 && (
              <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 p-6 rounded-lg border border-purple-500/20">
                <h3 className="text-lg font-semibold text-white mb-3">📋 Clause Analysis Results</h3>
                
                {results.clause_analysis.clause_findings && results.clause_analysis.clause_findings.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-md font-medium text-white mb-2">Clause Findings:</h4>
                    <div className="space-y-2">
                      {results.clause_analysis.clause_findings.map((finding: any, index: number) => (
                        <div key={index} className="bg-slate-800/50 p-3 rounded-lg">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-medium text-purple-300">
                              {finding.clause_type || 'Unknown'}
                            </span>
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              finding.risk_level === 'high' ? 'bg-red-100 text-red-800' :
                              finding.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {finding.risk_level || 'low'} risk
                            </span>
                          </div>
                          <p className="text-sm text-slate-300">{finding.details || finding.extracted_text || 'No details available'}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {results.clause_analysis.risk_indicators && results.clause_analysis.risk_indicators.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-md font-medium text-white mb-2">Risk Indicators:</h4>
                    <div className="flex flex-wrap gap-2">
                      {results.clause_analysis.risk_indicators.map((risk: string, index: number) => (
                        <span key={index} className="px-3 py-1 bg-red-100 text-red-800 text-sm rounded-full">
                          ⚠️ {risk}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {results.clause_analysis.recommendations && results.clause_analysis.recommendations.length > 0 && (
                  <div>
                    <h4 className="text-md font-medium text-white mb-2">Recommendations:</h4>
                    <div className="space-y-2">
                      {results.clause_analysis.recommendations.map((rec: string, index: number) => (
                        <div key={index} className="flex items-start gap-2">
                          <span className="text-green-400 mt-1">💡</span>
                          <span className="text-sm text-slate-300">{rec}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* AI Insights */}
            {results.ai_insights && (
              <div className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 p-6 rounded-lg border border-purple-500/20">
                <h3 className="text-lg font-semibold text-white mb-3">🤖 AI Insights</h3>
                <p className="text-slate-300 mb-4">{results.ai_insights.summary}</p>
                <div className="text-sm text-slate-400">
                  <p>• Total contracts analyzed: {results.ai_insights.total_contracts}</p>
                  <p>• Combined contract value: ${results.ai_insights.total_value.toLocaleString()}</p>
                  <p>• Unique suppliers: {results.ai_insights.suppliers_count}</p>
                </div>
              </div>
            )}

            {/* Search Results */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">
                Search Results ({results.documents.length} of {results.total_count})
              </h3>
              
              {results.documents.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  No contracts found matching your search criteria.
                </div>
              ) : (
                <div className="space-y-4">
                  {results.documents.map((doc, index) => (
                    <div key={doc.id || doc.document_id || index} className="border border-slate-600/50 rounded-lg p-4 hover:shadow-md transition-shadow bg-slate-800/30">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <h4 className="font-medium text-white">{doc.filename}</h4>
                          {doc.original_filename && doc.original_filename !== doc.filename && (
                            <p className="text-xs text-slate-500">Original: {doc.original_filename}</p>
                          )}
                          <p className="text-sm text-slate-400">
                            Supplier: {doc.supplier_name || 'Unknown'}
                          </p>
                          <div className="flex gap-4 mt-2 text-sm text-slate-500">
                            {doc.contract_type && <span>Type: {doc.contract_type}</span>}
                            {doc.status && <span>Status: {doc.status}</span>}
                            {doc.risk_level && <span>Risk: {doc.risk_level}</span>}
                            {doc.contract_amount && doc.contract_amount > 0 && (
                              <span>Amount: ${doc.contract_amount.toLocaleString()}</span>
                            )}
                            {doc.contract_date && <span>Date: {doc.contract_date}</span>}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-slate-500">Relevance</div>
                          <div className="font-medium text-white">
                            {((doc.relevance_score || doc.score || 0) * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                      
                      {/* RAG-specific information */}
                      {doc.match_reasons && doc.match_reasons.length > 0 && (
                        <div className="mt-3 p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
                          <h5 className="text-sm font-medium text-blue-300 mb-2">🎯 Why this matches:</h5>
                          <ul className="text-sm text-slate-300 space-y-1">
                            {doc.match_reasons.map((reason, idx) => (
                              <li key={idx} className="flex items-start gap-2">
                                <span className="text-blue-400 mt-1">•</span>
                                <span>{reason}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {doc.key_excerpts && doc.key_excerpts.length > 0 && (
                        <div className="mt-3 p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                          <h5 className="text-sm font-medium text-green-300 mb-2">📄 Key excerpts:</h5>
                          <div className="text-sm text-slate-300 space-y-2">
                            {doc.key_excerpts.map((excerpt, idx) => (
                              <div key={idx} className="bg-slate-800/50 p-2 rounded text-xs font-mono">
                                "{excerpt.length > 200 ? excerpt.substring(0, 200) + '...' : excerpt}"
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
