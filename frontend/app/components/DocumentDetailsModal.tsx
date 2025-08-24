'use client';

import React, { useState, useEffect } from 'react';
import { api } from '../lib/auth';

interface ContractClause {
  id: number;
  clause_type: string;
  clause_text: string;
  extracted_text?: string;
  risk_level?: string;
  confidence_score?: number;
  ai_analysis?: any;
  created_at: string;
}

interface DocumentAnalysis {
  analysis_available: boolean;
  document_id: number;
  filename: string;
  analysis_timestamp: string;
  clauses_analyzed: number;
  overall_risk_assessment: string;
  risk_summary: string;
  key_findings: string[];
  recommendations: string[];
  ai_confidence: number;
}

interface DocumentDetails {
  document_id: number;
  filename: string;
  original_filename: string;
  status: string;
  document_type: string;
  document_format: string;
  file_size: number;
  mime_type: string;
  
  // Processing information
  upload_timestamp: string;
  processing_started_at?: string;
  processing_completed_at?: string;
  processed_at?: string;
  error_message?: string;
  
  // Content extraction
  extracted_text?: string;
  extracted_metadata?: any;
  confidence_score?: number;
  
  // OCR details
  ocr_required: boolean;
  ocr_quality_score?: number;
  
  // Extracted clauses
  extracted_clauses: ContractClause[];
  clauses_count: number;
  
  // Supplier information
  supplier_name?: string;
  supplier_linked: boolean;
}

interface DocumentDetailsModalProps {
  documentId: number;
  isOpen: boolean;
  onClose: () => void;
}

export default function DocumentDetailsModal({ documentId, isOpen, onClose }: DocumentDetailsModalProps) {
  const [documentDetails, setDocumentDetails] = useState<DocumentDetails | null>(null);
  const [documentAnalysis, setDocumentAnalysis] = useState<DocumentAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [scrollPosition, setScrollPosition] = useState(0);

  useEffect(() => {
    if (isOpen && documentId) {
      // Capture current scroll position when modal opens
      setScrollPosition(window.scrollY);
      fetchDocumentDetails();
      fetchDocumentAnalysis();
    }
  }, [isOpen, documentId]);

  const fetchDocumentDetails = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/documents/${documentId}?details=true`);
      setDocumentDetails(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch document details');
    } finally {
      setLoading(false);
    }
  };

  const fetchDocumentAnalysis = async () => {
    setAnalysisLoading(true);
    setAnalysisError(null);
    
    try {
      console.log('Fetching document analysis for document ID:', documentId);
      const response = await api.get(`/documents/${documentId}/analysis`);
      console.log('Document analysis response:', response.data);
      setDocumentAnalysis(response.data);
    } catch (err: any) {
      console.error('Document analysis error:', err);
      console.error('Error response:', err.response);
      setAnalysisError(err.response?.data?.detail || err.message || 'Failed to fetch document analysis');
    } finally {
      setAnalysisLoading(false);
    }
  };

  const getRiskLevelColor = (riskLevel?: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'high':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'medium':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'low':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  const getConfidenceColor = (score?: number) => {
    if (!score) return 'text-slate-400';
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatConfidence = (confidence: number) => {
    return Math.round(confidence * 100);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" style={{ top: scrollPosition }}>
      <div className="bg-slate-900 rounded-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white">Document Details</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="text-red-400 mb-4">{error}</div>
              <button
                onClick={fetchDocumentDetails}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                Retry
              </button>
            </div>
          ) : documentDetails ? (
            <div className="space-y-6">
              {/* Basic Information */}
              <div className="bg-slate-800/50 rounded-lg p-4">
                <h3 className="text-lg font-medium text-white mb-4">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-slate-400">Filename:</span>
                    <p className="text-white font-medium">{documentDetails.original_filename}</p>
                  </div>
                  <div>
                    <span className="text-slate-400">Document Type:</span>
                    <p className="text-white capitalize">{documentDetails.document_type}</p>
                  </div>
                  <div>
                    <span className="text-slate-400">Format:</span>
                    <p className="text-white capitalize">{documentDetails.document_format}</p>
                  </div>
                  <div>
                    <span className="text-slate-400">File Size:</span>
                    <p className="text-white">{formatFileSize(documentDetails.file_size)}</p>
                  </div>
                  <div>
                    <span className="text-slate-400">Status:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(documentDetails.status)}`}>
                      {documentDetails.status}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400">Uploaded:</span>
                    <p className="text-white">{formatDate(documentDetails.upload_timestamp)}</p>
                  </div>
                </div>
              </div>

              {/* Analysis Summary */}
              <div className="bg-slate-800/50 rounded-lg p-4">
                                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-white">Analysis Summary</h3>
                    {documentAnalysis && documentAnalysis.ai_confidence && (
                      <div className="flex items-center space-x-2">
                        <span className="text-slate-400 text-sm">AI Confidence:</span>
                        <span className={`text-sm font-medium ${getConfidenceColor(formatConfidence(documentAnalysis.ai_confidence))}`}>
                          {formatConfidence(documentAnalysis.ai_confidence)}%
                        </span>
                      </div>
                    )}
                  </div>
                
                {analysisLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                    <span className="text-slate-400 ml-3">Analyzing document...</span>
                  </div>
                ) : analysisError ? (
                  <div className="text-center py-8">
                    <div className="text-red-400 mb-4">{analysisError}</div>
                    <button
                      onClick={fetchDocumentAnalysis}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm"
                    >
                      Retry Analysis
                    </button>
                  </div>
                ) : documentAnalysis ? (
                  <div className="space-y-4">
                    {/* Overall Risk Assessment */}
                    <div className="flex items-center space-x-3">
                      <span className="text-slate-400 text-sm">Overall Risk:</span>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskLevelColor(documentAnalysis.overall_risk_assessment || 'medium')}`}>
                        {(documentAnalysis.overall_risk_assessment || 'medium').toUpperCase()}
                      </span>
                      <span className="text-slate-400 text-sm">
                        ({documentAnalysis.clauses_analyzed || 0} clauses analyzed)
                      </span>
                    </div>

                    {/* Risk Summary */}
                    {documentAnalysis.risk_summary && documentAnalysis.risk_summary.trim() && (
                      <div>
                        <span className="text-slate-400 text-sm">Risk Summary:</span>
                        <p className="text-white text-sm mt-1 bg-slate-700/50 p-3 rounded border border-slate-600/20">
                          {documentAnalysis.risk_summary}
                        </p>
                      </div>
                    )}

                    {/* Key Findings */}
                    {documentAnalysis.key_findings && documentAnalysis.key_findings.length > 0 && (
                      <div>
                        <span className="text-slate-400 text-sm">Key Findings:</span>
                        <ul className="mt-2 space-y-1">
                          {documentAnalysis.key_findings.map((finding, index) => (
                            <li key={index} className="text-white text-sm bg-slate-700/50 p-2 rounded border border-slate-600/20 flex items-start">
                              <span className="text-blue-400 mr-2">•</span>
                              {finding}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Recommendations */}
                    {documentAnalysis.recommendations && documentAnalysis.recommendations.length > 0 && (
                      <div>
                        <span className="text-slate-400 text-sm">Recommendations:</span>
                        <ul className="mt-2 space-y-1">
                          {documentAnalysis.recommendations.map((recommendation, index) => (
                            <li key={index} className="text-white text-sm bg-slate-700/50 p-2 rounded border border-slate-600/20 flex items-start">
                              <span className="text-green-400 mr-2">→</span>
                              {recommendation}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}



                    {/* Analysis Timestamp */}
                    {documentAnalysis.analysis_timestamp && (
                      <div className="text-right">
                        <span className="text-slate-500 text-xs">
                          Analysis generated: {formatDate(documentAnalysis.analysis_timestamp)}
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400">
                    <div className="space-y-3">
                      <p className="text-lg font-medium">No Analysis Available</p>
                      <p className="text-sm">
                        This document was uploaded before analysis generation was implemented.
                      </p>
                      <p className="text-sm text-slate-500">
                        To get AI-powered risk analysis, please re-upload this document.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Supplier Information */}
              {documentDetails.supplier_name && (
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-white mb-4">Supplier Information</h3>
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-white font-medium">{documentDetails.supplier_name}</p>
                      <p className="text-slate-400 text-sm">
                        {documentDetails.supplier_linked ? 'Linked to supplier database' : 'Extracted from document'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Extracted Clauses */}
              {documentDetails.clauses_count > 0 && (
                <div className="bg-slate-800/50 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-white mb-4">
                    Extracted Clauses ({documentDetails.clauses_count})
                  </h3>
                  <div className="space-y-4">
                    {documentDetails.extracted_clauses.map((clause) => (
                      <div key={clause.id} className="bg-slate-700/50 rounded-lg p-4 border border-slate-600/20">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(clause.risk_level)}`}>
                              {clause.clause_type.replace('_', ' ').toUpperCase()}
                            </span>
                            {clause.risk_level && (
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(clause.risk_level)}`}>
                                {clause.risk_level.toUpperCase()}
                              </span>
                            )}
                          </div>
                          {clause.confidence_score && (
                            <span className={`text-sm font-medium ${getConfidenceColor(clause.confidence_score)}`}>
                              {clause.confidence_score}% confidence
                            </span>
                          )}
                        </div>
                        
                        <div className="space-y-3">
                          <div>
                            <span className="text-slate-400 text-sm">Clause Text:</span>
                            <p className="text-white text-sm mt-1 bg-slate-800/50 p-3 rounded border border-slate-600/20">
                              {clause.clause_text}
                            </p>
                          </div>
                          
                          {clause.extracted_text && clause.extracted_text !== clause.clause_text && (
                            <div>
                              <span className="text-slate-400 text-sm">Extracted Content:</span>
                              <p className="text-white text-sm mt-1 bg-slate-800/50 p-3 rounded border border-slate-600/20">
                                {clause.extracted_text}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Processing Information */}
              <div className="bg-slate-800/50 rounded-lg p-4">
                <h3 className="text-lg font-medium text-white mb-4">Processing Information</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {documentDetails.processing_started_at && (
                    <div>
                      <span className="text-slate-400">Processing Started:</span>
                      <p className="text-white">{formatDate(documentDetails.processing_started_at)}</p>
                    </div>
                  )}
                  {documentDetails.processing_completed_at && (
                    <div>
                      <span className="text-slate-400">Processing Completed:</span>
                      <p className="text-white">{formatDate(documentDetails.processing_completed_at)}</p>
                    </div>
                  )}
                  {documentDetails.confidence_score && (
                    <div>
                      <span className="text-slate-400">Extraction Confidence:</span>
                      <p className="text-white">{documentDetails.confidence_score}%</p>
                    </div>
                  )}
                  {documentDetails.ocr_required && (
                    <div>
                      <span className="text-slate-400">OCR Required:</span>
                      <p className="text-white">{documentDetails.ocr_required ? 'Yes' : 'No'}</p>
                    </div>
                  )}
                  {documentDetails.ocr_quality_score && (
                    <div>
                      <span className="text-slate-400">OCR Quality:</span>
                      <p className="text-white">{documentDetails.ocr_quality_score}%</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
