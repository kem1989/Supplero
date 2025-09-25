'use client';

import React, { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { api } from '../lib/auth';
import { useAuth } from '../contexts/AuthContext';

interface SupplierCreate {
  name: string;
  industry?: string;
  location?: string;
  country?: string;
  company_size?: string;
  revenue_range?: string;
  employee_count?: number;
}

interface SupplierResponse {
  id: number;
  name: string;
  industry?: string;
  country?: string;
  risk_score: number;
  risk_level: string;
}

interface SupplierRiskResponse {
  supplier_id: number;
  supplier_name: string;
  risk_score: number;
  risk_level: string;
  alert_level: string;
  recommendations?: string[];
  latest_news?: Array<{
    title: string;
    description?: string;
    url: string;
    source?: string;
    published_at?: string;
    sentiment_score?: number;
    relevance_score?: number;
    risk_keywords?: string[];
  }>;
}

export default function SuppliersPage() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const [form, setForm] = useState<SupplierCreate>({ name: '' });
  const [creating, setCreating] = useState(false);
  const [createdSupplier, setCreatedSupplier] = useState<SupplierResponse | null>(null);
  const [risk, setRisk] = useState<SupplierRiskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [suppliers, setSuppliers] = useState<SupplierResponse[]>([]);
  const [loadingList, setLoadingList] = useState<boolean>(false);
  const [enhancing, setEnhancing] = useState<boolean>(false);
  const [currentSupplier, setCurrentSupplier] = useState<SupplierResponse | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: name === 'employee_count' ? Number(value) || undefined : value }));
  };

  const createSupplier = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setCreating(true);
    setRisk(null);
    try {
      const payload: any = { ...form };
      if (user?.organization_id) {
        payload.organization_id = user.organization_id;
      }
      const response = await api.post('/suppliers/profile', payload);
      setCreatedSupplier(response.data);
      setCurrentSupplier(response.data);
      fetchSuppliers();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to create supplier');
    } finally {
      setCreating(false);
    }
  };

  const fetchRisk = async () => {
    if (!currentSupplier) return;
    setError(null);
    try {
      const response = await api.get(`/suppliers/${currentSupplier.id}/risk`);
      setRisk(response.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to fetch risk');
    }
  };

  const fetchEnhancedRisk = async () => {
    if (!currentSupplier) return;
    setError(null);
    setEnhancing(true);
    try {
      const response = await api.post(`/suppliers/${currentSupplier.id}/risk/enhanced`);
      setRisk(response.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to get enhanced risk');
    } finally {
      setEnhancing(false);
    }
  };

  const fetchSuppliers = async () => {
    try {
      setLoadingList(true);
      const ids = searchParams.get('ids');
      const country = searchParams.get('country');

      if (ids) {
        const idList = ids.split(',').map((v) => v.trim()).filter(Boolean);
        console.log('Fetching suppliers with IDs:', idList);
        // Fetch individually and aggregate to preserve accuracy
        const results: SupplierResponse[] = [];
        for (const id of idList) {
          try {
            console.log(`Fetching supplier ${id}...`);
            const resp = await api.get(`/suppliers/${id}`);
            console.log(`Supplier ${id} response:`, resp.data);
            if (resp.data) {
              // Backend returns single supplier object, not array
              results.push(resp.data);
            }
          } catch (e) {
            console.warn(`Failed to fetch supplier ${id}:`, e);
            // ignore failed ids
          }
        }
        console.log('Final suppliers array:', results);
        setSuppliers(results);
      } else if (country) {
        const response = await api.get(`/suppliers/search?country=${encodeURIComponent(country)}&page=1&page_size=50`);
        setSuppliers(response.data.suppliers || []);
      } else {
        const response = await api.get('/suppliers?page=1&page_size=20');
        setSuppliers(response.data.suppliers || []);
      }
    } catch (err: any) {
      console.error('Failed to fetch suppliers:', err);
    } finally {
      setLoadingList(false);
    }
  };

  React.useEffect(() => {
    fetchSuppliers();
    // re-run when filters change
  }, [searchParams]);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        {/* Navigation Header */}
        <div className="glass border-b border-white/10 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center space-x-4">
                <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 10-8 0v4M5 11h14l-1 10H6L5 11z" />
                  </svg>
                </div>
                <h1 className="text-xl font-bold text-white">Suppliers</h1>
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
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-white mb-2">Supplier Profiling & Risk</h1>
            <p className="text-slate-300">Create a supplier profile and retrieve its current risk assessment.</p>
          </div>

          <form onSubmit={createSupplier} className="glass rounded-2xl p-6 border border-white/10 mb-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-300 text-sm mb-1">Name</label>
                <input name="name" required value={form.name} onChange={handleChange} className="w-full bg-slate-800 text-white rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-600" />
              </div>
              <div>
                <label className="block text-slate-300 text-sm mb-1">Industry</label>
                <input name="industry" value={form.industry || ''} onChange={handleChange} className="w-full bg-slate-800 text-white rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-600" />
              </div>
              <div>
                <label className="block text-slate-300 text-sm mb-1">Country</label>
                <input name="country" value={form.country || ''} onChange={handleChange} className="w-full bg-slate-800 text-white rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-600" />
              </div>
              <div>
                <label className="block text-slate-300 text-sm mb-1">Location</label>
                <input name="location" value={form.location || ''} onChange={handleChange} className="w-full bg-slate-800 text-white rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-600" />
              </div>
              <div>
                <label className="block text-slate-300 text-sm mb-1">Company Size</label>
                <select name="company_size" value={form.company_size || ''} onChange={handleChange} className="w-full bg-slate-800 text-white rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-600">
                  <option value="">Select</option>
                  <option value="small">Small</option>
                  <option value="medium">Medium</option>
                  <option value="large">Large</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-300 text-sm mb-1">Employee Count</label>
                <input name="employee_count" type="number" min={1} value={form.employee_count || ''} onChange={handleChange} className="w-full bg-slate-800 text-white rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-600" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-slate-300 text-sm mb-1">Revenue Range</label>
                <input name="revenue_range" value={form.revenue_range || ''} onChange={handleChange} className="w-full bg-slate-800 text-white rounded-lg px-3 py-2 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-600" />
              </div>
            </div>
            <div className="flex gap-3">
              <button type="submit" disabled={creating} className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-60">{creating ? 'Creating...' : 'Create Supplier'}</button>
              {currentSupplier && (
                <>
                  <button type="button" onClick={fetchRisk} className="px-5 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white">Get Risk</button>
                  <button type="button" onClick={fetchEnhancedRisk} disabled={enhancing} className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-60">{enhancing ? 'Enhancing...' : 'Enhanced Risk'}</button>
                </>
              )}
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
          </form>

          {currentSupplier && (
            <div className="glass rounded-2xl p-6 border border-white/10 mb-6">
              <h2 className="text-xl text-white font-semibold mb-2">Selected Supplier</h2>
              <p className="text-slate-300"><span className="text-slate-400">Name:</span> {currentSupplier.name}</p>
              <p className="text-slate-300"><span className="text-slate-400">Industry:</span> {currentSupplier.industry || '—'}</p>
              <p className="text-slate-300"><span className="text-slate-400">Country:</span> {currentSupplier.country || '—'}</p>
              <p className="text-slate-300"><span className="text-slate-400">Risk:</span> {currentSupplier.risk_level} ({Math.round(currentSupplier.risk_score)})</p>
            </div>
          )}

          {risk && (
            <div className="glass rounded-2xl p-6 border border-white/10">
              <h2 className="text-xl text-white font-semibold mb-2">Current Risk Assessment</h2>
              <p className="text-slate-300"><span className="text-slate-400">Supplier:</span> {risk.supplier_name}</p>
              <p className="text-slate-300"><span className="text-slate-400">Risk Score:</span> {Math.round(risk.risk_score)} ({risk.risk_level})</p>
              <p className="text-slate-300"><span className="text-slate-400">Alert Level:</span> {risk.alert_level}</p>
              {risk.recommendations && risk.recommendations.length > 0 && (
                <div className="mt-3">
                  <p className="text-slate-300 mb-1">Recommendations:</p>
                  <ul className="list-disc pl-5 text-slate-300">
                    {risk.recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
              {risk.latest_news && risk.latest_news.length > 0 && (
                <div className="mt-6">
                  <p className="text-slate-300 mb-2">Latest News</p>
                  <div className="space-y-3">
                    {risk.latest_news.slice(0,5).map((n, idx) => (
                      <a key={idx} href={n.url} target="_blank" rel="noreferrer" className="block rounded-lg border border-white/10 bg-slate-800/50 p-3 hover:border-white/20">
                        <p className="text-white font-medium">{n.title}</p>
                        {n.source || n.published_at ? (
                          <p className="text-slate-400 text-xs mt-1">{n.source || 'Unknown source'}{n.published_at ? ` • ${new Date(n.published_at).toLocaleString()}` : ''}</p>
                        ) : null}
                        {typeof n.sentiment_score === 'number' && (
                          <p className="text-slate-400 text-xs mt-1">Sentiment: {n.sentiment_score.toFixed(2)}</p>
                        )}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Suppliers List */}
          <div className="glass rounded-2xl p-6 border border-white/10 mt-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl text-white font-semibold">Your Suppliers</h2>
              <button onClick={fetchSuppliers} className="px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm">Refresh</button>
            </div>
            {loadingList ? (
              <p className="text-slate-400">Loading...</p>
            ) : suppliers.length === 0 ? (
              <p className="text-slate-400">No suppliers yet. Create one above.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {suppliers.map((s) => (
                  <div key={s.id} className={`rounded-xl p-4 border ${currentSupplier?.id === s.id ? 'border-blue-500/50 bg-slate-800/70' : 'border-white/10 bg-slate-800/50'}`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-white font-medium">{s.name}</p>
                        <p className="text-slate-400 text-sm">{s.industry || '—'} {s.country ? `• ${s.country}` : ''}</p>
                      </div>
                      <span className="text-sm px-2 py-0.5 rounded-full border"
                        style={{
                          borderColor: 'rgba(255,255,255,0.15)',
                          color: s.risk_level === 'HIGH' || s.risk_level === 'CRITICAL' ? '#f87171' : s.risk_level === 'MEDIUM' ? '#fbbf24' : '#34d399'
                        }}
                      >
                        {s.risk_level}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-slate-400 text-sm">
                      <span>Risk Score: {Math.round(s.risk_score)}</span>
                      <button onClick={() => { setCurrentSupplier(s); setRisk(null); }} className="text-blue-400 hover:text-blue-300">View</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}


