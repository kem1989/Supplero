'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { api } from '../lib/auth';
import DocumentUpload from '../components/DocumentUpload';
import DocumentList from '../components/DocumentList';
import ProcessingStatus from '../components/ProcessingStatus';

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

export default function DocumentsPage() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingDocuments, setProcessingDocuments] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await api.get('/documents');
      setDocuments(response.data.documents || []);
      
      const processingIds = response.data.documents
        .filter((doc: Document) => 
          doc.status === 'uploaded' || 
          doc.status === 'processing' || 
          doc.status === 'ocr_processing'
        )
        .map((doc: Document) => doc.id as number);
      setProcessingDocuments(new Set(processingIds));
    } catch (err: any) {
      console.error('Failed to fetch documents:', err);
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentUploaded = (newDocument: Document) => {
    setDocuments(prev => [newDocument, ...prev]);
    setProcessingDocuments(prev => new Set([...Array.from(prev), newDocument.id]));
  };

  const handleDocumentStatusUpdate = (documentId: number, status: string) => {
    setDocuments(prev => 
      prev.map(doc => 
        doc.id === documentId 
          ? { ...doc, status, updated_at: new Date().toISOString() }
          : doc
      )
    );

    if (status === 'processed' || status === 'failed') {
      setProcessingDocuments(prev => {
        const newSet = new Set(Array.from(prev));
        newSet.delete(documentId);
        return newSet;
      });
    }
  };

  const handleDocumentDeleted = (documentId: number) => {
    setDocuments(prev => prev.filter(doc => doc.id !== documentId));
    setProcessingDocuments(prev => {
      const newSet = new Set(prev);
      newSet.delete(documentId);
      return newSet;
    });
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        {/* Navigation Header */}
        <div className="glass border-b border-white/10 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center space-x-4">
                <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h1 className="text-xl font-bold text-white">Document Management</h1>
                <a
                  href="/dashboard"
                  className="text-sm text-slate-400 hover:text-blue-400 transition-colors flex items-center space-x-1"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                  <span>Dashboard</span>
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto p-6">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              📄 Document Processing Pipeline
            </h1>
            <p className="text-slate-300">
              Upload contracts, invoices, and other documents for AI-powered processing, OCR, and intelligent analysis.
            </p>
          </div>

          {/* Processing Status Overview */}
          {processingDocuments.size > 0 && (
            <div className="mb-6">
              <ProcessingStatus 
                processingCount={processingDocuments.size}
                onStatusUpdate={handleDocumentStatusUpdate}
              />
            </div>
          )}

          {/* Document Upload Section */}
          <div className="mb-8">
            <DocumentUpload 
              onDocumentUploaded={handleDocumentUploaded}
              onStatusUpdate={handleDocumentStatusUpdate}
            />
          </div>

          {/* Document List Section */}
          <div className="mb-8">
            <DocumentList 
              documents={documents}
              loading={loading}
              error={error}
              onRefresh={fetchDocuments}
              onDocumentDeleted={handleDocumentDeleted}
              onStatusUpdate={handleDocumentStatusUpdate}
            />
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
