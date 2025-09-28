'use client';

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { api } from '../lib/auth';

interface Contract {
  id: number;
  title: string | null;
  type: string | null;
  status: string;
  contract_value: number | null;
  currency: string;
  effective_at: string | null;
  expires_at: string | null;
  auto_renewal: boolean;
  renewal_term_months: number | null;
  governing_law: string | null;
  jurisdiction: string | null;
  payment_terms_days: number | null;
  liability_cap_amount: number | null;
  liability_cap_type: string | null;
  sla_uptime_percent: number | null;
  termination_notice_days: number | null;
  penalty_rate_percent: number | null;
  created_at: string;
  updated_at: string;
}

interface ContractDetailsModalProps {
  contractId: number;
  isOpen: boolean;
  onClose: () => void;
}

export default function ContractDetailsModal({ contractId, isOpen, onClose }: ContractDetailsModalProps) {
  const [contract, setContract] = useState<Contract | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    if (isOpen && contractId) {
      fetchContractDetails();
    }
  }, [isOpen, contractId]);

  // Track mount to safely use portals on client only
  useEffect(() => {
    setMounted(true);
  }, []);

  // Disable background scroll when modal is open
  useEffect(() => {
    if (!mounted) return;
    const originalOverflow = document.body.style.overflow;
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = originalOverflow;
    }
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [isOpen, mounted]);

  const fetchContractDetails = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/contracts/${contractId}`);
      setContract(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch contract details');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'ACTIVE':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'EXPIRED':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'TERMINATED':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'PENDING':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  const formatCurrency = (value: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const isExpiringSoon = (expiresAt: string) => {
    const expiryDate = new Date(expiresAt);
    const now = new Date();
    const daysUntilExpiry = Math.ceil((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return daysUntilExpiry <= 90 && daysUntilExpiry > 0;
  };

  const isExpired = (expiresAt: string) => {
    const expiryDate = new Date(expiresAt);
    const now = new Date();
    return expiryDate < now;
  };

  if (!isOpen || !mounted) return null;

  return createPortal(
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 rounded-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Contract Details</h2>
              <p className="text-slate-400 text-sm">
                {contract?.title || 'Contract Information'}
              </p>
            </div>
          </div>
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
                onClick={fetchContractDetails}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                Retry
              </button>
            </div>
          ) : contract ? (
            <div className="space-y-6">
              {/* Contract Overview */}
              <div className="bg-slate-800/50 rounded-lg p-6">
                <div className="flex items-start justify-between mb-6">
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-white mb-2">
                      {contract.title || 'Untitled Contract'}
                    </h3>
                    <p className="text-slate-400 text-lg">
                      {contract.type || 'Contract'}
                    </p>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className={`px-4 py-2 rounded-full text-sm font-medium ${getStatusColor(contract.status)}`}>
                      {contract.status}
                    </span>
                    {contract.expires_at && isExpiringSoon(contract.expires_at) && !isExpired(contract.expires_at) && (
                      <span className="px-3 py-1 bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded-full text-xs font-medium">
                        Expiring Soon
                      </span>
                    )}
                    {contract.expires_at && isExpired(contract.expires_at) && (
                      <span className="px-3 py-1 bg-red-500/20 text-red-400 border border-red-500/30 rounded-full text-xs font-medium">
                        Expired
                      </span>
                    )}
                  </div>
                </div>

                {contract.contract_value && (
                  <div className="bg-gradient-to-r from-blue-500/10 to-purple-600/10 rounded-lg p-4 border border-blue-500/20">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-slate-400 text-sm">Contract Value</p>
                        <p className="text-3xl font-bold text-white">
                          {formatCurrency(contract.contract_value, contract.currency)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-slate-400 text-sm">Currency</p>
                        <p className="text-xl font-semibold text-white">{contract.currency}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Contract Terms */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Key Dates */}
                <div className="bg-slate-800/50 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Key Dates
                  </h4>
                  <div className="space-y-3">
                    {contract.effective_at && (
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400">Effective Date:</span>
                        <span className="text-white font-medium">{formatDate(contract.effective_at)}</span>
                      </div>
                    )}
                    {contract.expires_at && (
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400">Expiry Date:</span>
                        <span className={`font-medium ${isExpired(contract.expires_at) ? 'text-red-400' : isExpiringSoon(contract.expires_at) ? 'text-yellow-400' : 'text-white'}`}>
                          {formatDate(contract.expires_at)}
                        </span>
                      </div>
                    )}
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Created:</span>
                      <span className="text-white font-medium">{formatDate(contract.created_at)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Last Updated:</span>
                      <span className="text-white font-medium">{formatDateTime(contract.updated_at)}</span>
                    </div>
                  </div>
                </div>

                {/* Contract Terms */}
                <div className="bg-slate-800/50 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Contract Terms
                  </h4>
                  <div className="space-y-3">
                    {contract.auto_renewal !== null && (
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400">Auto Renewal:</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${contract.auto_renewal ? 'bg-green-500/20 text-green-400' : 'bg-slate-500/20 text-slate-400'}`}>
                          {contract.auto_renewal ? 'Yes' : 'No'}
                        </span>
                      </div>
                    )}
                    {contract.renewal_term_months && (
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400">Renewal Term:</span>
                        <span className="text-white font-medium">{contract.renewal_term_months} months</span>
                      </div>
                    )}
                    {contract.payment_terms_days && (
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400">Payment Terms:</span>
                        <span className="text-white font-medium">{contract.payment_terms_days} days</span>
                      </div>
                    )}
                    {contract.termination_notice_days && (
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400">Termination Notice:</span>
                        <span className="text-white font-medium">{contract.termination_notice_days} days</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Legal & Compliance */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Legal Information */}
                <div className="bg-slate-800/50 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                    </svg>
                    Legal Information
                  </h4>
                  <div className="space-y-3">
                    {contract.governing_law && (
                      <div>
                        <span className="text-slate-400 text-sm">Governing Law:</span>
                        <p className="text-white font-medium">{contract.governing_law}</p>
                      </div>
                    )}
                    {contract.jurisdiction && (
                      <div>
                        <span className="text-slate-400 text-sm">Jurisdiction:</span>
                        <p className="text-white font-medium">{contract.jurisdiction}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Financial Terms */}
                <div className="bg-slate-800/50 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                    Financial Terms
                  </h4>
                  <div className="space-y-3">
                    {contract.liability_cap_amount && (
                      <div>
                        <span className="text-slate-400 text-sm">Liability Cap:</span>
                        <p className="text-white font-medium">
                          {formatCurrency(contract.liability_cap_amount, contract.currency)}
                          {contract.liability_cap_type && ` (${contract.liability_cap_type})`}
                        </p>
                      </div>
                    )}
                    {contract.penalty_rate_percent && (
                      <div>
                        <span className="text-slate-400 text-sm">Penalty Rate:</span>
                        <p className="text-white font-medium">{contract.penalty_rate_percent}%</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Service Level Agreement */}
              {contract.sla_uptime_percent && (
                <div className="bg-slate-800/50 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-white mb-4 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    Service Level Agreement
                  </h4>
                  <div className="flex items-center space-x-4">
                    <div className="flex-1">
                      <span className="text-slate-400 text-sm">Uptime Guarantee:</span>
                      <p className="text-2xl font-bold text-white">{contract.sla_uptime_percent}%</p>
                    </div>
                    <div className="w-24 h-24 relative">
                      <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
                        <circle
                          cx="50"
                          cy="50"
                          r="40"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="none"
                          className="text-slate-700"
                        />
                        <circle
                          cx="50"
                          cy="50"
                          r="40"
                          stroke="currentColor"
                          strokeWidth="8"
                          fill="none"
                          strokeDasharray={`${2 * Math.PI * 40}`}
                          strokeDashoffset={`${2 * Math.PI * 40 * (1 - contract.sla_uptime_percent / 100)}`}
                          className="text-cyan-400"
                          strokeLinecap="round"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-white font-bold text-sm">{contract.sla_uptime_percent}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>,
    document.body
  );
}
