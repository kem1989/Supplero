'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { api } from '../lib/auth';
import DocumentUpload from '../components/DocumentUpload';
import DocumentList from '../components/DocumentList';
import ProcessingStatus from '../components/ProcessingStatus';
import DocumentDetailsModal from '../components/DocumentDetailsModal';

interface Document {
  document_id: number;  // Backend returns document_id, not id
  filename: string;     // Backend returns filename, not original_filename
  original_filename?: string; // Keep for backward compatibility
  status: string;
  document_type: string;
  document_format: string;
  file_size?: number;   // Backend doesn't return this in DocumentStatusResponse
  confidence_score?: number;
  ocr_quality_score?: number;
  created_at?: string;  // Backend returns upload_timestamp
  updated_at?: string;
  processing_error?: string;
  upload_timestamp: string; // Backend returns this
}

export default function DocumentsPage() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingDocuments, setProcessingDocuments] = useState<Set<number>>(new Set());
  const [autoProcessingMessage, setAutoProcessingMessage] = useState<string | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const searchParams = useSearchParams();

  useEffect(() => {
    const requestedDocumentId = searchParams.get('documentId');
    const requestedPage = searchParams.get('page');

    if (requestedDocumentId) {
      // Show only the requested document
      fetchSingleDocument(Number(requestedDocumentId)).then((ok) => {
        if (ok) {
          setSelectedDocumentId(Number(requestedDocumentId));
          setShowDetailsModal(true);
        }
      });
    } else {
      fetchDocuments();
    }
    
    // Set up polling to refresh documents every 3 seconds when there are processing documents
    // Only poll when there are actually documents being processed
    const interval = setInterval(() => {
      if (processingDocuments.size > 0) {
        // Only fetch processing status, not the full documents list
        // This prevents flickering of the Document Library
        const fetchProcessingStatus = async () => {
          try {
            const response = await api.get('/documents?status=UPLOADED,PROCESSING,OCR_PROCESSING');
            const processingIds = response.data.documents.map((doc: Document) => doc.document_id as number);
            setProcessingDocuments(new Set(processingIds));
          } catch (err) {
            console.error('Failed to fetch processing status:', err);
          }
        };
        fetchProcessingStatus();
      }
    }, 3000);
    
    return () => clearInterval(interval);
  }, [processingDocuments.size, searchParams]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await api.get('/documents');
      
      // Only show completed documents in the Document Library
      const completedDocuments = response.data.documents.filter((doc: Document) => 
        doc.status === 'PROCESSED' || doc.status === 'FAILED'
      );
      setDocuments(completedDocuments);
      
      // Track processing documents separately for the ProcessingStatus component
      const processingIds = response.data.documents
        .filter((doc: Document) => 
          doc.status === 'UPLOADED' || 
          doc.status === 'PROCESSING' || 
          doc.status === 'OCR_PROCESSING'
        )
        .map((doc: Document) => doc.document_id as number);
      setProcessingDocuments(new Set(processingIds));
    } catch (err: any) {
      console.error('Failed to fetch documents:', err);
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSingleDocument = async (documentId: number): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await api.get(`/documents/${documentId}`);
      const doc = response.data;
      if (doc && doc.document_id) {
        // Normalize shape to match Document type if needed
        const normalized: Document = {
          document_id: doc.document_id,
          filename: doc.filename || doc.original_filename || `document_${doc.document_id}`,
          original_filename: doc.original_filename,
          status: doc.status || 'PROCESSED',
          document_type: doc.document_type || 'CONTRACT',
          document_format: doc.document_format || 'pdf',
          file_size: doc.file_size,
          confidence_score: doc.confidence_score,
          ocr_quality_score: doc.ocr_quality_score,
          created_at: doc.created_at,
          updated_at: doc.updated_at,
          processing_error: doc.processing_error,
          upload_timestamp: doc.upload_timestamp || doc.created_at || new Date().toISOString(),
        };
        setDocuments([normalized]);
        return true;
      }
      setDocuments([]);
      return false;
    } catch (err) {
      console.error('Failed to fetch document:', err);
      setError('Failed to load requested document.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentUploaded = async (newDocument: Document) => {
    // Show processing started message
    setAutoProcessingMessage('Document uploaded! Processing in progress...');
    
    // Add to processing documents set to show progress
    setProcessingDocuments(prev => new Set([...Array.from(prev), newDocument.document_id]));
    
    // The document is now being processed in the backend
    // Processing happens automatically during upload
    // We'll see the progress through the ProcessingStatus component
    
    // Clear the message after 3 seconds
    setTimeout(() => setAutoProcessingMessage(null), 3000);
  };

  const handleDocumentStatusUpdate = (documentId: number, status: string) => {
    setDocuments(prevDocs => 
      prevDocs.map(doc => 
        doc.document_id === documentId ? { ...doc, status } : doc
      )
    );
    
    // Remove from processing set if status is final
    if (['PROCESSED', 'FAILED'].includes(status)) {
      setProcessingDocuments(prev => {
        const newSet = new Set(prev);
        newSet.delete(documentId);
        return newSet;
      });
    }
  };

  const handleDocumentDeleted = (documentId: number) => {
    setDocuments(prev => prev.filter(doc => doc.document_id !== documentId));
    setProcessingDocuments(prev => {
      const newSet = new Set(prev);
      newSet.delete(documentId);
      return newSet;
    });
  };

  const handleViewDocumentDetails = (documentId: number) => {
    setSelectedDocumentId(documentId);
    setShowDetailsModal(true);
  };

  const closeDetailsModal = () => {
    setShowDetailsModal(false);
    setSelectedDocumentId(null);
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        {/* Navigation Header */}
        <div className="bg-slate-800/50 border-b border-slate-700/50">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-8">
                <h1 className="text-2xl font-bold text-white">Supplero</h1>
                <nav className="flex items-center space-x-6">
                  <a href="/dashboard" className="text-slate-300 hover:text-white transition-colors flex items-center space-x-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                    <span>Dashboard</span>
                  </a>
                </nav>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto p-6">
          {/* Page Header */}
          <div className="mb-8">
            <div className="mb-4">
              <h1 className="text-3xl font-bold text-white mb-2">
                📄 Document Processing Pipeline
              </h1>
              <p className="text-slate-300">
                Upload contracts, invoices, and other documents for AI-powered processing, OCR, and intelligent analysis. 
                Processing starts automatically and documents appear in the library when complete.
              </p>
            </div>
            
            {/* Processing Status Info */}
            {processingDocuments.size > 0 && (
              <div className="mt-4 p-3 bg-slate-800/50 border border-slate-700 rounded-lg">
                <p className="text-slate-300 text-sm">
                  📊 <span className="font-medium">{processingDocuments.size}</span> document{processingDocuments.size !== 1 ? 's' : ''} currently processing...
                </p>
              </div>
            )}
          </div>

          {/* Auto-processing Message */}
          {autoProcessingMessage && (
            <div className="mb-4 p-4 bg-gradient-to-r from-blue-500/20 to-purple-600/20 border border-blue-500/30 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-5 h-5 bg-blue-500 rounded-full animate-pulse"></div>
                <p className="text-blue-300 font-medium">{autoProcessingMessage}</p>
              </div>
            </div>
          )}

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
              onViewDocumentDetails={handleViewDocumentDetails}
            />
          </div>

          {/* Document List Section */}
          <div className="mb-8">
            {documents.length === 0 && !loading && !error ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 bg-slate-700 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-slate-300 mb-2">No documents yet</h3>
                <p className="text-slate-400">
                  Upload your first document to get started. It will appear here once processing is complete.
                </p>
              </div>
            ) : (
              <DocumentList 
                documents={documents}
                loading={loading}
                error={error}
                onRefresh={fetchDocuments}
                onDocumentDeleted={handleDocumentDeleted}
                onStatusUpdate={handleDocumentStatusUpdate}
              />
            )}
          </div>

          {/* Document Details Modal */}
          {selectedDocumentId && (
            <DocumentDetailsModal
              documentId={selectedDocumentId}
              isOpen={showDetailsModal}
              onClose={closeDetailsModal}
            />
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
