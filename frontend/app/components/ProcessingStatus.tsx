'use client';

import React, { useState, useEffect } from 'react';
import { api } from '../lib/auth';

interface ProcessingStatusProps {
  processingCount: number;
  onStatusUpdate: (documentId: number, status: string) => void;
}

interface ProcessingDocument {
  document_id: number;  // Backend returns document_id, not id
  filename: string;      // Backend returns filename, not original_filename
  status: string;
  progress: number;
  current_step: string;
  estimated_time?: string;
}

export default function ProcessingStatus({ processingCount, onStatusUpdate }: ProcessingStatusProps) {
  const [processingDocuments, setProcessingDocuments] = useState<ProcessingDocument[]>([]);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (processingCount > 0) {
      fetchProcessingDocuments();
      const interval = setInterval(fetchProcessingDocuments, 5000); // Poll every 5 seconds
      return () => clearInterval(interval);
    }
  }, [processingCount]);

  const fetchProcessingDocuments = async () => {
    try {
      const response = await api.get('/documents', {
        params: {
          status: 'UPLOADED,PROCESSING,OCR_PROCESSING'
        }
      });
      
      const documents = response.data.documents || [];
      const processing = documents.map((doc: any) => ({
        document_id: doc.document_id,
        filename: doc.filename,
        status: doc.status,
        progress: getProgressForStatus(doc.status),
        current_step: getCurrentStep(doc.status),
        estimated_time: getEstimatedTime(doc.status)
      }));
      
      setProcessingDocuments(processing);
    } catch (error) {
      console.error('Failed to fetch processing documents:', error);
    }
  };

  const getProgressForStatus = (status: string): number => {
    switch (status) {
      case 'UPLOADED':
        return 25;
      case 'PROCESSING':
        return 60;
      case 'OCR_PROCESSING':
        return 85;
      default:
        return 0;
    }
  };

  const getCurrentStep = (status: string): string => {
    switch (status) {
      case 'UPLOADED':
        return 'Starting processing...';
      case 'PROCESSING':
        return 'Extracting text and metadata...';
      case 'OCR_PROCESSING':
        return 'Running OCR analysis...';
      default:
        return 'Unknown status';
    }
  };

  const getEstimatedTime = (status: string): string => {
    switch (status) {
      case 'UPLOADED':
        return '~2-3 minutes';
      case 'PROCESSING':
        return '~1-2 minutes';
      case 'OCR_PROCESSING':
        return '~30 seconds';
      default:
        return 'Unknown';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PROCESSING':
      case 'OCR_PROCESSING':
        return 'text-blue-400';
      case 'UPLOADED':
        return 'text-yellow-400';
      default:
        return 'text-slate-400';
    }
  };

  if (processingCount === 0) {
    return null;
  }

  return (
    <div className="glass rounded-2xl p-6 border border-white/10 bg-gradient-to-r from-blue-500/10 to-purple-500/10">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">
              Processing {processingCount} Document{processingCount !== 1 ? 's' : ''}
            </h3>
            <p className="text-slate-300 text-sm">
              AI-powered document analysis in progress. Documents will appear in the library once complete.
            </p>
          </div>
        </div>
        
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg transition-colors"
        >
          <svg 
            className={`w-5 h-5 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Processing Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="bg-slate-800/50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-blue-400 mb-1">
            {processingDocuments.filter(doc => doc.status === 'UPLOADED').length}
          </div>
          <div className="text-sm text-slate-400">Queued</div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-purple-400 mb-1">
            {processingDocuments.filter(doc => doc.status === 'PROCESSING').length}
          </div>
          <div className="text-sm text-slate-400">Processing</div>
        </div>
        <div className="bg-slate-800/50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-400 mb-1">
            {processingDocuments.filter(doc => doc.status === 'OCR_PROCESSING').length}
          </div>
          <div className="text-sm text-slate-400">OCR Analysis</div>
        </div>
      </div>

      {/* Expanded Processing Details */}
      {expanded && (
        <div className="space-y-3">
          <h4 className="font-medium text-white">Processing Details</h4>
          
          {processingDocuments.map((doc) => (
            <div key={doc.document_id} className="bg-slate-800/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <h5 className="font-medium text-white text-sm">{doc.filename}</h5>
                    <p className={`text-xs ${getStatusColor(doc.status)}`}>
                      {doc.current_step}
                    </p>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-sm text-slate-400">
                    Est: {doc.estimated_time}
                  </div>
                </div>
              </div>
              
              {/* Progress Bar */}
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="h-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500"
                  style={{ width: `${doc.progress}%` }}
                ></div>
              </div>
              
              <div className="flex items-center justify-between mt-2 text-xs text-slate-400">
                <span>{doc.progress}% Complete</span>
                <span className="capitalize">{doc.status.replace('_', ' ')}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Processing Pipeline Info */}
      <div className="mt-4 p-4 bg-slate-800/30 rounded-lg">
        <h4 className="font-medium text-white mb-2">Processing Pipeline</h4>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-slate-400">1. Upload</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <span className="text-slate-400">2. Format Detection</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-slate-400">3. Text Extraction</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span className="text-slate-400">4. AI Analysis</span>
          </div>
        </div>
      </div>
    </div>
  );
}
