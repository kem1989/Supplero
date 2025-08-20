'use client';

import React, { useState } from 'react';
import { 
  SupplierCard, 
  RiskIndicator, 
  SupplierMetrics, 
  QuickActions,
  createContractMetric,
  createValueMetric,
  createRiskMetric,
  createAnalysisActions,
  createViewActions,
  type SupplierCardData,
  type SupplierMetric 
} from '../../components/suppliers';

// Sample supplier data for demonstration
const sampleSuppliers: SupplierCardData[] = [
  {
    id: 1,
    name: "TechCorp Industries",
    industry: "Technology",
    location: "San Francisco, CA",
    country: "United States",
    contact_email: "contact@techcorp.com",
    contact_phone: "+1-555-0123",
    website: "https://techcorp.com",
    company_size: "large",
    employee_count: 5000,
    revenue_range: "$100M - $500M",
    risk_score: 75,
    risk_level: "HIGH",
    is_active: true,
    is_watchlisted: true,
    watchlist_reason: "Recent supply chain disruptions",
    last_risk_assessment: "2024-01-15",
    created_at: "2023-06-15",
    updated_at: "2024-01-15",
    relevance_score: 0.92,
    contract_count: 12,
    total_contract_value: 2500000,
    latest_contract_date: "2023-12-01",
    key_highlights: [
      "High-value supplier with recent contract increases",
      "Located in earthquake-prone region",
      "Strong financial performance but supply chain vulnerabilities"
    ]
  },
  {
    id: 2,
    name: "GlobalSupply Co",
    industry: "Manufacturing",
    location: "Shanghai, China",
    country: "China",
    contact_email: "business@globalsupply.cn",
    company_size: "medium",
    employee_count: 1200,
    risk_score: 45,
    risk_level: "MEDIUM",
    is_active: true,
    is_watchlisted: false,
    last_risk_assessment: "2024-01-10",
    created_at: "2023-03-20",
    updated_at: "2024-01-10",
    relevance_score: 0.78,
    contract_count: 6,
    total_contract_value: 850000,
    key_highlights: [
      "Consistent delivery performance",
      "Moderate geopolitical risk exposure"
    ]
  },
  {
    id: 3,
    name: "EcoSolutions Ltd",
    industry: "Renewable Energy",
    location: "Berlin, Germany",
    country: "Germany",
    contact_email: "info@ecosolutions.de",
    website: "https://ecosolutions.de",
    company_size: "small",
    employee_count: 350,
    risk_score: 25,
    risk_level: "LOW",
    is_active: true,
    is_watchlisted: false,
    last_risk_assessment: "2024-01-20",
    created_at: "2023-09-10",
    updated_at: "2024-01-20",
    relevance_score: 0.65,
    contract_count: 3,
    total_contract_value: 420000,
    key_highlights: [
      "Excellent sustainability credentials",
      "Growing market presence in renewable energy"
    ]
  }
];

export default function SupplierComponentsDemo() {
  const [selectedVariant, setSelectedVariant] = useState<'default' | 'compact' | 'detailed'>('default');

  const handleSupplierAction = (actionId: string, supplier: SupplierCardData) => {
    console.log(`Action "${actionId}" triggered for supplier:`, supplier.name);
    alert(`Action "${actionId}" triggered for supplier: ${supplier.name}`);
  };

  const sampleMetrics: SupplierMetric[] = [
    createContractMetric(8, 1500000),
    createValueMetric(1500000),
    createRiskMetric(65, "MEDIUM"),
    {
      label: "Delivery Performance",
      value: "94%",
      icon: (
        <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      color: 'green',
      trend: { direction: 'up', percentage: 5, label: 'vs last quarter' }
    },
    {
      label: "Quality Score",
      value: "4.2",
      icon: (
        <svg className="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'yellow',
      trend: { direction: 'neutral' }
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Navigation Header */}
      <div className="glass border-b border-white/10 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM21 5H9a2 2 0 00-2 2v12a4 4 0 004 4h6a2 2 0 002-2V7a2 2 0 00-2-2z" />
                </svg>
              </div>
              <h1 className="text-xl font-bold text-white">Supplier Components Demo</h1>
              <div className="flex items-center space-x-4 text-sm">
                <a href="/suppliers/discovery" className="text-slate-400 hover:text-blue-400 transition-colors">
                  ← Back to Discovery
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-6">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Supplier Result Components</h1>
          <p className="text-slate-300">
            Demonstration of the new modular supplier result components: SupplierCard, RiskIndicator, SupplierMetrics, and QuickActions.
          </p>
        </div>

        {/* Component Controls */}
        <div className="glass rounded-2xl p-6 border border-white/10 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Component Variants</h2>
          <div className="flex space-x-4">
            {(['default', 'compact', 'detailed'] as const).map((variant) => (
              <button
                key={variant}
                onClick={() => setSelectedVariant(variant)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedVariant === variant
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {variant.charAt(0).toUpperCase() + variant.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Individual Component Demos */}
        <div className="space-y-8">
          {/* Risk Indicator Demo */}
          <div className="glass rounded-xl p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4">Risk Indicator Component</h2>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((level) => (
                <div key={level} className="p-4 bg-slate-800/30 rounded-lg border border-slate-600/30">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">{level}</h3>
                  <RiskIndicator 
                    riskLevel={level} 
                    riskScore={level === 'CRITICAL' ? 90 : level === 'HIGH' ? 70 : level === 'MEDIUM' ? 50 : 20}
                    size="md"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Metrics Demo */}
          <div className="glass rounded-xl p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4">Supplier Metrics Component</h2>
            <SupplierMetrics metrics={sampleMetrics} layout="grid" />
          </div>

          {/* Quick Actions Demo */}
          <div className="glass rounded-xl p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4">Quick Actions Component</h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-medium text-white mb-2">View Actions</h3>
                <QuickActions
                  supplier={sampleSuppliers[0]}
                  actions={createViewActions(sampleSuppliers[0])}
                  layout="horizontal"
                  onAction={handleSupplierAction}
                />
              </div>
              <div>
                <h3 className="text-lg font-medium text-white mb-2">Analysis Actions</h3>
                <QuickActions
                  supplier={sampleSuppliers[0]}
                  actions={createAnalysisActions(sampleSuppliers[0])}
                  layout="horizontal"
                  onAction={handleSupplierAction}
                />
              </div>
              <div>
                <h3 className="text-lg font-medium text-white mb-2">Dropdown Layout</h3>
                <QuickActions
                  supplier={sampleSuppliers[0]}
                  layout="dropdown"
                  onAction={handleSupplierAction}
                />
              </div>
            </div>
          </div>

          {/* Supplier Cards Demo */}
          <div className="glass rounded-xl p-6 border border-white/10">
            <h2 className="text-xl font-semibold text-white mb-4">
              Supplier Cards - {selectedVariant.charAt(0).toUpperCase() + selectedVariant.slice(1)} Variant
            </h2>
            <div className="space-y-4">
              {sampleSuppliers.map((supplier) => (
                <SupplierCard
                  key={supplier.id}
                  supplier={supplier}
                  variant={selectedVariant}
                  showMetrics={selectedVariant !== 'compact'}
                  showActions={true}
                  onViewDetails={handleSupplierAction}
                  onAnalyzeRisk={handleSupplierAction}
                  onToggleWatchlist={(supplier) => handleSupplierAction('toggle-watchlist', supplier)}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Usage Examples */}
        <div className="glass rounded-xl p-6 border border-white/10 mt-8">
          <h2 className="text-xl font-semibold text-white mb-4">Usage Examples</h2>
          <div className="space-y-4 text-sm">
            <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-600/20">
              <h3 className="font-medium text-white mb-2">Basic Supplier Card</h3>
              <pre className="text-slate-300 text-xs overflow-x-auto">
{`<SupplierCard
  supplier={supplierData}
  variant="default"
  onViewDetails={(supplier) => navigateToDetails(supplier.id)}
  onAnalyzeRisk={(supplier) => openRiskAnalysis(supplier)}
/>`}
              </pre>
            </div>
            
            <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-600/20">
              <h3 className="font-medium text-white mb-2">Standalone Risk Indicator</h3>
              <pre className="text-slate-300 text-xs overflow-x-auto">
{`<RiskIndicator 
  riskLevel="HIGH" 
  riskScore={75} 
  size="lg" 
  showLabel={true}
/>`}
              </pre>
            </div>

            <div className="p-4 bg-slate-800/30 rounded-lg border border-slate-600/20">
              <h3 className="font-medium text-white mb-2">Custom Metrics</h3>
              <pre className="text-slate-300 text-xs overflow-x-auto">
{`const metrics = [
  createContractMetric(5, 500000),
  createRiskMetric(65, "MEDIUM"),
  { label: "Custom Metric", value: "95%", color: "green" }
];

<SupplierMetrics metrics={metrics} layout="horizontal" />`}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
