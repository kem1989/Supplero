'use client';

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { api } from '../lib/auth';

interface DocumentUploadProps {
  onDocumentUploaded: (document: any) => void;
  onStatusUpdate: (documentId: number, status: string) => void;
  onViewDocumentDetails?: (documentId: number) => void;
}

interface UploadProgress {
  [key: string]: {
    progress: number;
    status: 'uploading' | 'processing' | 'completed' | 'error';
    message: string | React.ReactNode;
  };
}

export default function DocumentUpload({ onDocumentUploaded, onStatusUpdate, onViewDocumentDetails }: DocumentUploadProps) {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({});
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setIsUploading(true);
    
    for (const file of acceptedFiles) {
      const fileId = `${file.name}-${Date.now()}`;
      
      // Initialize progress tracking
      setUploadProgress(prev => ({
        ...prev,
        [fileId]: {
          progress: 0,
          status: 'uploading',
          message: 'Starting upload...'
        }
      }));

      try {
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('file', file);
        formData.append('organization_id', '1'); // TODO: Get from user context

        // Upload file
        setUploadProgress(prev => ({
          ...prev,
          [fileId]: {
            ...prev[fileId],
            progress: 25,
            message: 'Uploading file...'
          }
        }));

        const response = await api.post('/documents/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setUploadProgress(prev => ({
                ...prev,
                [fileId]: {
                  ...prev[fileId],
                  progress: Math.min(progress, 90), // Cap at 90% until processing starts
                }
              }));
            }
          }
        });

        const document = response.data;
        
        // Update progress to processing
        setUploadProgress(prev => ({
          ...prev,
          [fileId]: {
            ...prev[fileId],
            progress: 90,
            status: 'processing',
            message: 'Processing document...'
          }
        }));

        // Notify parent component
        onDocumentUploaded(document);
        
        // Start polling for status updates
        pollDocumentStatus(document.document_id, fileId);

        // Show success message with insights summary
        setUploadProgress(prev => ({
          ...prev,
          [fileId]: {
            ...prev[fileId],
            progress: 100,
            status: 'completed',
            message: 'Upload successful! Click to view extracted insights.'
          }
        }));

        // Show insights summary after a short delay
        setTimeout(() => {
          showInsightsSummary(document.document_id, fileId);
        }, 1000);

        // Add clickable link to view details
        setTimeout(() => {
          setUploadProgress(prev => ({
            ...prev,
            [fileId]: {
              ...prev[fileId],
              progress: 100,
              status: 'completed',
              message: (
                <span>
                  Document processed successfully!{' '}
                  <button
                    onClick={() => viewDocumentDetails(document.document_id)}
                    className="text-blue-400 hover:text-blue-300 underline"
                  >
                    Click here to view extracted insights
                  </button>
                </span>
              )
            }
          }));
        }, 2000);

      } catch (error: any) {
        console.error('Upload failed:', error);
        setUploadProgress(prev => ({
          ...prev,
          [fileId]: {
            ...prev[fileId],
            progress: 0,
            status: 'error',
            message: error.response?.data?.detail || 'Upload failed'
          }
        }));
      }
    }
    
    setIsUploading(false);
  }, [onDocumentUploaded]);

  const pollDocumentStatus = async (documentId: number, fileId: string) => {
    const maxAttempts = 60; // 5 minutes with 5-second intervals
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await api.get(`/documents/${documentId}`);
        const document = response.data;
        
        // Update progress based on status
        let progress = 90;
        let message = 'Processing document...';
        
        switch (document.status) {
          case 'UPLOADED':
            progress = 90;
            message = 'Document uploaded, starting processing...';
            break;
          case 'PROCESSING':
            progress = 95;
            message = 'Extracting text and metadata...';
            break;
          case 'OCR_PROCESSING':
            progress = 97;
            message = 'Running OCR analysis...';
            break;
          case 'PROCESSED':
            progress = 100;
            message = 'Processing completed!';
            setUploadProgress(prev => ({
              ...prev,
              [fileId]: {
                ...prev[fileId],
                status: 'completed',
                progress: 100,
                message: 'Processing completed!'
              }
            }));
            onStatusUpdate(documentId, document.status);
            return; // Stop polling
          case 'FAILED':
            setUploadProgress(prev => ({
              ...prev,
              [fileId]: {
                ...prev[fileId],
                status: 'error',
                progress: 0,
                message: document.processing_error || 'Processing failed'
              }
            }));
            onStatusUpdate(documentId, document.status);
            return; // Stop polling
        }

        setUploadProgress(prev => ({
          ...prev,
          [fileId]: {
            ...prev[fileId],
            progress,
            message
          }
        }));

        // Continue polling if not completed
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000); // Poll every 5 seconds
        } else {
          setUploadProgress(prev => ({
            ...prev,
            [fileId]: {
              ...prev[fileId],
              status: 'error',
              message: 'Processing timeout - please check document status'
            }
          }));
        }

      } catch (error) {
        console.error('Status check failed:', error);
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        }
      }
    };

    // Start polling after a short delay
    setTimeout(poll, 2000);
  };

  const showInsightsSummary = async (documentId: number, fileId: string) => {
    try {
      // Fetch document details to get extracted clauses and metadata
      const response = await api.get(`/documents/${documentId}?details=true`);
      const documentDetails = response.data;
      
      let summaryText = 'Document processed successfully';
      
      // Add clause summary if available
      if (documentDetails.clauses_count > 0) {
        const clauseTypes = Array.from(new Set(documentDetails.extracted_clauses.map(c => c.clause_type)));
        summaryText += ` • ${documentDetails.clauses_count} clauses extracted (${clauseTypes.slice(0, 3).join(', ')}${clauseTypes.length > 3 ? '...' : ''})`;
      }
      
      // Add supplier information if available
      if (documentDetails.supplier_name) {
        summaryText += ` • Supplier: ${documentDetails.supplier_name}`;
      }
      
      // Add metadata summary if available
      if (documentDetails.extracted_metadata) {
        const metadata = documentDetails.extracted_metadata;
        if (metadata.total_value) {
          summaryText += ` • Contract Value: $${metadata.total_value}`;
        }
        if (metadata.start_date && metadata.end_date) {
          summaryText += ` • Term: ${metadata.start_date} to ${metadata.end_date}`;
        }
      }
      
      setUploadProgress(prev => ({
        ...prev,
        [fileId]: {
          ...prev[fileId],
          progress: 100,
          status: 'completed',
          message: summaryText
        }
      }));
      
    } catch (error) {
      console.error('Failed to fetch document details:', error);
      // Fallback to basic success message
      setUploadProgress(prev => ({
        ...prev,
        [fileId]: {
          ...prev[fileId],
          progress: 100,
          status: 'completed',
          message: 'Document processed successfully! Click "View Details" to see extracted insights.'
        }
      }));
    }
  };

  const viewDocumentDetails = async (documentId: number) => {
    if (onViewDocumentDetails) {
      onViewDocumentDetails(documentId);
    } else {
      try {
        const response = await api.get(`/documents/${documentId}?details=true`);
        const documentDetails = response.data;
        onDocumentUploaded(documentDetails); // Notify parent component with full document details
        onStatusUpdate(documentId, 'VIEWED'); // Update status to viewed
      } catch (error) {
        console.error('Failed to view document details:', error);
      }
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'image/*': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: true
  });

  const removeProgress = (fileId: string) => {
    setUploadProgress(prev => {
      const newProgress = { ...prev };
      delete newProgress[fileId];
      return newProgress;
    });
  };

  return (
    <div className="glass rounded-2xl p-6 border border-white/10">
      <h2 className="text-2xl font-bold text-white mb-4">
        📤 Upload Documents
      </h2>
      
      <div className="mb-6">
        <p className="text-slate-300 mb-4">
          Drag and drop your documents here, or click to browse. We support PDF, DOCX, and image files up to 50MB.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="flex items-center space-x-2 text-sm text-slate-400">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>PDF Documents</span>
          </div>
          <div className="flex items-center space-x-2 text-sm text-slate-400">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>Word Documents</span>
          </div>
          <div className="flex items-center space-x-2 text-sm text-slate-400">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <span>Scanned Images</span>
          </div>
        </div>
      </div>

      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer ${
          isDragActive
            ? 'border-blue-400 bg-blue-500/10'
            : 'border-slate-600 hover:border-slate-500 hover:bg-slate-800/50'
        }`}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full mx-auto flex items-center justify-center">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          
          <div>
            <p className="text-lg font-medium text-white">
              {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
            </p>
            <p className="text-slate-400 mt-1">
              or click to browse files
            </p>
          </div>
        </div>
      </div>

      {/* Upload Progress */}
      {Object.keys(uploadProgress).length > 0 && (
        <div className="mt-6 space-y-3">
          <h3 className="text-lg font-semibold text-white">Upload Progress</h3>
          
          {Object.entries(uploadProgress).map(([fileId, progress]) => (
            <div key={fileId} className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">
                  {fileId.split('-')[0]}
                </span>
                <div className="flex items-center space-x-2">
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    progress.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                    progress.status === 'error' ? 'bg-red-500/20 text-red-400' :
                    progress.status === 'processing' ? 'bg-blue-500/20 text-blue-400' :
                    'bg-slate-500/20 text-slate-400'
                  }`}>
                    {progress.status}
                  </span>
                  {progress.status === 'completed' && (
                    <button
                      onClick={() => removeProgress(fileId)}
                      className="text-slate-400 hover:text-white transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
              
              <div className="w-full bg-slate-700 rounded-full h-2 mb-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    progress.status === 'completed' ? 'bg-green-500' :
                    progress.status === 'error' ? 'bg-red-500' :
                    progress.status === 'processing' ? 'bg-blue-500' :
                    'bg-gradient-to-r from-blue-500 to-purple-500'
                  }`}
                  style={{ width: `${progress.progress}%` }}
                ></div>
              </div>
              
              <p className="text-xs text-slate-400">{progress.message}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
