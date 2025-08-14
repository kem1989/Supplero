'use client';

import React, { useState } from 'react';
import { api } from '../lib/auth';

interface Document {
  id: number;
  filename: string;
  original_filename: string;
  status: string;
  document_type: string;
  document_format: string;
  file_size: number;
  confidence_score?: number;
  ocr_quality_score?: number;
  created_at: string;
  updated_at: string;
  processing_error?: string;
}

interface DocumentListProps {
  documents: Document[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onDocumentDeleted: (documentId: number) => void;
  onStatusUpdate: (documentId: number, status: string) => void;
}

export default function DocumentList({
  documents,
  loading,
  error,
  onRefresh,
  onDocumentDeleted,
  onStatusUpdate
}: DocumentListProps) {
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletingDocument, setDeletingDocument] = useState<number | null>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processed':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'processing':
      case 'ocr_processing':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'failed':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'uploaded':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processed':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'processing':
      case 'ocr_processing':
        return (
          <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      case 'uploaded':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        );
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleDelete = async (documentId: number) => {
    try {
      setDeletingDocument(documentId);
      await api.delete(`/documents/${documentId}`);
      onDocumentDeleted(documentId);
      setShowDeleteModal(false);
      setSelectedDocument(null);
    } catch (error) {
      console.error('Failed to delete document:', error);
    } finally {
      setDeletingDocument(null);
    }
  };

  const handleRetryProcessing = async (documentId: number) => {
    try {
      await api.post(`/documents/${documentId}/process`);
      onStatusUpdate(documentId, 'processing');
    } catch (error) {
      console.error('Failed to retry processing:', error);
    }
  };

  if (loading) {
    return (
      <div className="glass rounded-2xl p-6 border border-white/10">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-slate-400">Loading documents...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass rounded-2xl p-6 border border-white/10">
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-red-500/20 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Error Loading Documents</h3>
          <p className="text-slate-400 mb-4">{error}</p>
          <button
            onClick={onRefresh}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-2xl p-6 border border-white/10">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">
          📋 Document Library
        </h2>
        <div className="flex items-center space-x-3">
          <button
            onClick={onRefresh}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors flex items-center space-x-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {documents.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-slate-700/50 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">No Documents Yet</h3>
          <p className="text-slate-400">
            Upload your first document to get started with AI-powered processing and analysis.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {documents.map((document) => (
            <div
              key={document.id}
              className="bg-slate-800/50 rounded-lg p-4 hover:bg-slate-800/70 transition-colors cursor-pointer"
              onClick={() => setSelectedDocument(document)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-white">{document.original_filename}</h4>
                    <div className="flex items-center space-x-4 text-sm text-slate-400 mt-1">
                      <span>{formatFileSize(document.file_size)}</span>
                      <span>•</span>
                      <span className="capitalize">{document.document_type}</span>
                      <span>•</span>
                      <span className="capitalize">{document.document_format}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  {/* Status Badge */}
                  <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${getStatusColor(document.status)}`}>
                    {getStatusIcon(document.status)}
                    <span className="text-xs font-medium capitalize">{document.status.replace('_', ' ')}</span>
                  </div>

                  {/* Confidence Score */}
                  {document.confidence_score && (
                    <div className="text-sm text-slate-400">
                      Confidence: {document.confidence_score}%
                    </div>
                  )}

                  {/* OCR Quality Score */}
                  {document.ocr_quality_score && (
                    <div className="text-sm text-slate-400">
                      OCR: {document.ocr_quality_score}%
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    {document.status === 'failed' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRetryProcessing(document.id);
                        }}
                        className="p-2 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded-lg transition-colors"
                        title="Retry processing"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      </button>
                    )}
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedDocument(document);
                        setShowDeleteModal(true);
                      }}
                      className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
                      title="Delete document"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-slate-700/50">
                <div className="flex items-center justify-between text-sm text-slate-400">
                  <span>Uploaded: {formatDate(document.created_at)}</span>
                  {document.updated_at !== document.created_at && (
                    <span>Updated: {formatDate(document.updated_at)}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && selectedDocument && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="glass rounded-2xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">Delete Document</h3>
            <p className="text-slate-300 mb-6">
              Are you sure you want to delete "{selectedDocument.original_filename}"? This action cannot be undone.
            </p>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(selectedDocument.id)}
                disabled={deletingDocument === selectedDocument.id}
                className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {deletingDocument === selectedDocument.id ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
