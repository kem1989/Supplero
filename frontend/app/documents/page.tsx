'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { api } from '../lib/auth';
import ContractDetailsModal from '../components/ContractDetailsModal';

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

export default function DocumentsPage() {
  const { user } = useAuth();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedContractId, setSelectedContractId] = useState<number | null>(null);
  const searchParams = useSearchParams();

  useEffect(() => {
    const requestedContractId = searchParams.get('contractId');
    const requestedPage = searchParams.get('page');

    if (requestedContractId) {
      // Show only the requested contract
      fetchSingleContract(Number(requestedContractId)).then((ok) => {
        if (ok) {
          setSelectedContractId(Number(requestedContractId));
          setShowDetailsModal(true);
        }
      });
    } else {
      fetchContracts();
    }
  }, [searchParams]);

  const fetchContracts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/contracts');
      setContracts(response.data.contracts || []);
    } catch (err: any) {
      console.error('Failed to fetch contracts:', err);
      setError('Failed to load contracts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSingleContract = async (contractId: number): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await api.get(`/contracts/${contractId}`);
      const contract = response.data;
      if (contract && contract.id) {
        setContracts([contract]);
        return true;
      }
      setContracts([]);
      return false;
    } catch (err) {
      console.error('Failed to fetch contract:', err);
      setError('Failed to load requested contract.');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const handleContractDeleted = (contractId: number) => {
    setContracts(prev => prev.filter(contract => contract.id !== contractId));
  };

  const handleViewContractDetails = (contractId: number) => {
    setSelectedContractId(contractId);
    setShowDetailsModal(true);
  };

  const closeDetailsModal = () => {
    setShowDetailsModal(false);
    setSelectedContractId(null);
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
                📄 Contract Management
              </h1>
              <p className="text-slate-300">
                View and manage your contracts. Track contract status, values, terms, and important dates.
              </p>
            </div>
          </div>

          {/* Contract List Section */}
          <div className="mb-8">
            {contracts.length === 0 && !loading && !error ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 bg-slate-700 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-slate-300 mb-2">No contracts yet</h3>
                <p className="text-slate-400">
                  Contracts will appear here once they are added to the system.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {contracts.map((contract) => (
                  <div key={contract.id} className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition-colors">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-white mb-1">
                          {contract.title || 'Untitled Contract'}
                        </h3>
                        <p className="text-slate-400 text-sm">
                          {contract.type || 'Contract'}
                        </p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        contract.status === 'ACTIVE' 
                          ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                          : contract.status === 'EXPIRED'
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                          : 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
                      }`}>
                        {contract.status}
                      </span>
                    </div>
                    
                    <div className="space-y-2 mb-4">
                      {contract.contract_value && (
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Value:</span>
                          <span className="text-white">
                            {contract.currency} {contract.contract_value.toLocaleString()}
                          </span>
                        </div>
                      )}
                      {contract.effective_at && (
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Effective:</span>
                          <span className="text-white">
                            {new Date(contract.effective_at).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                      {contract.expires_at && (
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">Expires:</span>
                          <span className="text-white">
                            {new Date(contract.expires_at).toLocaleDateString()}
                          </span>
                        </div>
                      )}
                    </div>
                    
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleViewContractDetails(contract.id)}
                        className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                      >
                        View Details
                      </button>
                      <button
                        onClick={() => handleContractDeleted(contract.id)}
                        className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Contract Details Modal */}
          {selectedContractId && (
            <ContractDetailsModal
              contractId={selectedContractId}
              isOpen={showDetailsModal}
              onClose={closeDetailsModal}
            />
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}