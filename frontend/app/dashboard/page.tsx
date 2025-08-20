'use client';

import { useAuth } from '../contexts/AuthContext';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { useState } from 'react';

// Mock data for visualizations
const mockStats = {
  totalUsers: 1247,
  activeUsers: 892,
  newUsers: 156,
  growthRate: 12.5,
  organizationCount: 89,
  lastUpdated: '2 hours ago'
};

const mockChartData = [
  { month: 'Jan', users: 65, growth: 12 },
  { month: 'Feb', users: 78, growth: 20 },
  { month: 'Mar', users: 90, growth: 15 },
  { month: 'Apr', users: 105, growth: 17 },
  { month: 'May', users: 120, growth: 14 },
  { month: 'Jun', users: 135, growth: 13 },
];

const mockRecentActivity = [
  { id: 1, action: 'New user registered', user: 'john.doe@example.com', time: '2 minutes ago', type: 'success' },
  { id: 2, action: 'Organization updated', user: 'admin@supplero.com', time: '15 minutes ago', type: 'info' },
  { id: 3, action: 'Password reset requested', user: 'jane.smith@example.com', time: '1 hour ago', type: 'warning' },
  { id: 4, action: 'Login successful', user: 'mike.wilson@example.com', time: '2 hours ago', type: 'success' },
];

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');

  const handleLogout = async () => {
    await logout();
  };

  const StatCard = ({ title, value, change, icon, color }: any) => (
    <div className="glass rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all duration-300 hover:shadow-lg">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-white mt-2">{value}</p>
          {change && (
            <div className={`flex items-center mt-2 text-sm ${change > 0 ? 'text-green-400' : 'text-red-400'}`}>
              <svg className={`w-4 h-4 mr-1 ${change > 0 ? 'rotate-0' : 'rotate-180'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
              {Math.abs(change)}%
            </div>
          )}
        </div>
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );

  const ActivityItem = ({ activity }: any) => (
    <div className="flex items-center space-x-3 p-3 rounded-xl hover:bg-slate-800/50 transition-colors duration-200">
      <div className={`w-2 h-2 rounded-full ${
        activity.type === 'success' ? 'bg-green-400' : 
        activity.type === 'warning' ? 'bg-yellow-400' : 
        'bg-blue-400'
      }`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{activity.action}</p>
        <p className="text-xs text-slate-400">{activity.user}</p>
      </div>
      <span className="text-xs text-slate-500">{activity.time}</span>
    </div>
  );

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        {/* Navigation */}
        <nav className="glass border-b border-white/10 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center space-x-4">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h1 className="text-xl font-bold text-white">Supplero Dashboard</h1>
                <nav className="hidden md:flex items-center space-x-2 text-sm text-slate-400">
                  <span>/</span>
                  <a href="/contract-discovery" className="hover:text-blue-400 transition-colors">Contract Discovery</a>
                  <span>/</span>
                  <a href="/suppliers/discovery" className="hover:text-blue-400 transition-colors">Supplier Discovery</a>
                  <span>/</span>
                  <a href="/documents" className="hover:text-blue-400 transition-colors">Documents</a>
                  <span>/</span>
                  <a href="/audit" className="hover:text-blue-400 transition-colors">Audit</a>
                </nav>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-white">
                      {user?.first_name?.[0] || user?.username?.[0] || 'U'}
                    </span>
                  </div>
                  <div className="hidden md:block">
                    <p className="text-sm font-medium text-white">
                      {user?.first_name || user?.username}
                    </p>
                    <p className="text-xs text-slate-400">{user?.role}</p>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="bg-red-500/10 hover:bg-red-500/20 text-red-400 hover:text-red-300 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 border border-red-500/20 hover:border-red-500/40"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          {/* Header Section */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-white mb-2">Welcome back, {user?.first_name || user?.username}!</h2>
            <p className="text-slate-400">Here's what's happening with your account today.</p>
          </div>

          {/* Quick Actions */}
          <div className="mb-8">
            <h3 className="text-xl font-bold text-white mb-4">Quick Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <a
                href="/contract-discovery"
                className="glass rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all duration-300 hover:shadow-lg group"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-white">Contract Discovery</h4>
                    <p className="text-slate-400 text-sm">AI-powered contract search and analysis</p>
                  </div>
                </div>
              </a>
              
              <a
                href="/suppliers/discovery"
                className="glass rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all duration-300 hover:shadow-lg group"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM17 8l4 4-4 4M3 12h18" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-white">Supplier Discovery</h4>
                    <p className="text-slate-400 text-sm">AI-powered supplier search and intelligence</p>
                  </div>
                </div>
              </a>
              
              <a
                href="/documents"
                className="glass rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all duration-300 hover:shadow-lg group"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-white">Documents</h4>
                    <p className="text-slate-400 text-sm">Upload and manage documents</p>
                  </div>
                </div>
              </a>
              
              <a
                href="/suppliers"
                className="glass rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all duration-300 hover:shadow-lg group"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 10-8 0v4M5 11h14l-1 10H6L5 11z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-white">Suppliers</h4>
                    <p className="text-slate-400 text-sm">Create profiles and view risk</p>
                  </div>
                </div>
              </a>

              <a
                href="/audit"
                className="glass rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all duration-300 hover:shadow-lg group"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold text-white">Audit & Compliance</h4>
                    <p className="text-slate-400 text-sm">View audit logs and compliance data</p>
                  </div>
                </div>
              </a>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              title="Total Users"
              value={mockStats.totalUsers.toLocaleString()}
              change={mockStats.growthRate}
              icon={<svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>}
              color="bg-gradient-to-br from-blue-500 to-blue-600"
            />
            <StatCard
              title="Active Users"
              value={mockStats.activeUsers.toLocaleString()}
              change={8.2}
              icon={<svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>}
              color="bg-gradient-to-br from-green-500 to-green-600"
            />
            <StatCard
              title="New Users"
              value={mockStats.newUsers}
              change={-2.1}
              icon={<svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>}
              color="bg-gradient-to-br from-purple-500 to-purple-600"
            />
            <StatCard
              title="Organizations"
              value={mockStats.organizationCount}
              change={5.7}
              icon={<svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>}
              color="bg-gradient-to-br from-orange-500 to-orange-600"
            />
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* User Profile Card */}
            <div className="lg:col-span-1">
              <div className="glass rounded-2xl p-6 border border-white/10">
                <div className="text-center mb-6">
                  <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full mx-auto mb-4 flex items-center justify-center">
                    <span className="text-2xl font-bold text-white">
                      {user?.first_name?.[0] || user?.username?.[0] || 'U'}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-white">
                    {user?.first_name} {user?.last_name}
                  </h3>
                  <p className="text-slate-400">{user?.email}</p>
                </div>

                <div className="space-y-4">
                  <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                    <span className="text-slate-400">Username</span>
                    <span className="text-white font-medium">{user?.username}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                    <span className="text-slate-400">Role</span>
                    <span className="text-white font-medium capitalize">{user?.role}</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                    <span className="text-slate-400">Status</span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      user?.is_active 
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                        : 'bg-red-500/20 text-red-400 border border-red-500/30'
                    }`}>
                      {user?.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-slate-700/50">
                    <span className="text-slate-400">Verified</span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      user?.is_verified 
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                        : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                    }`}>
                      {user?.is_verified ? 'Verified' : 'Pending'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-slate-400">Organization ID</span>
                    <span className="text-white font-medium">{user?.organization_id}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Charts and Activity */}
            <div className="lg:col-span-2 space-y-8">
              {/* Growth Chart */}
              <div className="glass rounded-2xl p-6 border border-white/10">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">User Growth</h3>
                  <span className="text-sm text-slate-400">Last 6 months</span>
                </div>
                <div className="h-64 flex items-end justify-between space-x-2">
                  {mockChartData.map((data, index) => (
                    <div key={data.month} className="flex-1 flex flex-col items-center">
                      <div className="w-full bg-gradient-to-t from-blue-500/20 to-blue-500/5 rounded-t-lg relative group">
                        <div 
                          className="bg-gradient-to-t from-blue-500 to-blue-400 rounded-t-lg transition-all duration-300 group-hover:from-blue-400 group-hover:to-blue-300"
                          style={{ height: `${(data.users / 135) * 100}%` }}
                        />
                        <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-slate-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap">
                          {data.users} users
                        </div>
                      </div>
                      <span className="text-xs text-slate-400 mt-2">{data.month}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Activity */}
              <div className="glass rounded-2xl p-6 border border-white/10">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">Recent Activity</h3>
                  <button className="text-sm text-blue-400 hover:text-blue-300 transition-colors duration-200">
                    View all
                  </button>
                </div>
                <div className="space-y-2">
                  {mockRecentActivity.map((activity) => (
                    <ActivityItem key={activity.id} activity={activity} />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Info */}
          <div className="mt-8 text-center">
            <p className="text-sm text-slate-500">
              Last updated: {mockStats.lastUpdated} • Data refreshes automatically
            </p>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
} 