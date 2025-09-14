'use client';

import React, { useState } from 'react';
import { AdminDashboard } from '@/components/AdminDashboard';
import { AdminUserManagement } from '@/components/AdminUserManagement';
import { AdminLinkManagement } from '@/components/AdminLinkManagement';
import { AdminAuditLog } from '@/components/AdminAuditLog';
import { AdminDomainConfig } from '@/components/AdminDomainConfig';
import { AuthButton } from '@/components/AuthButton';
import { Button } from '@/components/ui/Button';
import { ArrowLeft, Link as LinkIcon, Shield, Users, BarChart3, Settings } from 'lucide-react';
import Link from 'next/link';
import { Navigation } from '@/components/Navigation';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'links', label: 'Links', icon: LinkIcon },
    { id: 'audit', label: 'Audit Log', icon: Shield },
    { id: 'config', label: 'Configuration', icon: Settings }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <AdminDashboard activeTab={activeTab} onTabChange={setActiveTab} />;
      case 'users':
        return <AdminUserManagement />;
      case 'links':
        return <AdminLinkManagement />;
      case 'audit':
        return <AdminAuditLog />;
      case 'config':
        return <AdminDomainConfig />;
      default:
        return <AdminDashboard activeTab={activeTab} onTabChange={setActiveTab} />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 relative overflow-hidden">
      {/* Animated Background Elements - Same as main page */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-400/20 to-purple-600/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-cyan-400/20 to-blue-600/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-br from-purple-400/10 to-pink-600/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Header - Same style as main page */}
      <header className="relative backdrop-blur-md bg-white/70 border-b border-white/20 shadow-lg z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              {/* Navigation Menu */}
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg p-1">
                <Navigation currentPage="admin" />
              </div>
              
              {/* Logo and Title */}
              <div className="flex items-center">
                <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
                  <Shield className="h-6 w-6 text-white" />
                </div>
                <h1 className="ml-3 text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                  Admin Panel
                </h1>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Back to main site */}
              <Link href="/">
                <Button
                  variant="outline"
                  size="sm"
                >
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Back to Site
                </Button>
              </Link>
              
              {/* Authentication button */}
              <AuthButton />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Admin Header */}
        <div className="mb-8">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-cyan-500/10 rounded-2xl blur-xl"></div>
            <div className="relative backdrop-blur-xl bg-white/70 border border-white/20 rounded-2xl shadow-xl p-6">
              <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent">
                Admin Dashboard
              </h1>
              <p className="text-gray-600 mt-2">System administration and monitoring</p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        {renderTabContent()}
      </main>
    </div>
  );
}