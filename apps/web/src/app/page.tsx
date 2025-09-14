'use client';

import React, { useState } from 'react';
import { LinkCreator } from '@/components/LinkCreator';
import { LinkDisplay } from '@/components/LinkDisplay';
import { AnalyticsDashboard } from '@/components/AnalyticsDashboard';
import { AuthButton } from '@/components/AuthButton';
import { UserDashboard } from '@/components/UserDashboard';
import { AdminNavButton } from '@/components/AdminNavButton';
import { type CreateLinkResponse } from '@shared/types/link';
import { Button } from '@/components/ui/Button';
import { ToastContainer, useToast } from '@/components/ui/Toast';
import { ArrowLeft, Link as LinkIcon, User } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Navigation } from '@/components/Navigation';

type ViewMode = 'create' | 'display' | 'analytics' | 'dashboard';

export default function Home() {
  const [viewMode, setViewMode] = useState<ViewMode>('create');
  const [currentLink, setCurrentLink] = useState<CreateLinkResponse | null>(null);
  const [analyticsCode, setAnalyticsCode] = useState<string>('');
  const { toasts, removeToast } = useToast();
  const { user } = useAuth();

  const handleLinkCreated = (link: CreateLinkResponse) => {
    setCurrentLink(link);
    setViewMode('display');
  };

  const handleViewAnalytics = (code: string) => {
    setAnalyticsCode(code);
    setViewMode('analytics');
  };

  const handleBackToCreate = () => {
    setViewMode('create');
    setCurrentLink(null);
    setAnalyticsCode('');
  };

  const handleBackToDisplay = () => {
    setViewMode('display');
    setAnalyticsCode('');
  };

  const handleViewDashboard = () => {
    setViewMode('dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 relative overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-400/20 to-purple-600/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-cyan-400/20 to-blue-600/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-br from-purple-400/10 to-pink-600/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Header */}
      <header className="relative backdrop-blur-md bg-white/70 border-b border-white/20 shadow-lg z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              {/* Navigation Menu */}
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg p-1">
                <Navigation currentPage="home" />
              </div>
              
              {/* Logo and Title */}
              <div className="flex items-center">
                <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
                  <LinkIcon className="h-6 w-6 text-white" />
                </div>
                <h1 className="ml-3 text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                  Contextual URL Shortener
                </h1>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Navigation buttons */}
              {viewMode !== 'create' && (
                <div className="flex items-center space-x-2">
                  {viewMode === 'analytics' && currentLink && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleBackToDisplay}
                    >
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Back to Link
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleBackToCreate}
                  >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Create New Link
                  </Button>
                </div>
              )}
              
              {/* User Dashboard button (only show when authenticated) */}
              {user && viewMode !== 'dashboard' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleViewDashboard}
                  className="text-gray-700 hover:text-gray-900"
                >
                  <User className="h-4 w-4 mr-2" />
                  Dashboard
                </Button>
              )}
              
              {/* Admin button (only show for admin users) */}
              <AdminNavButton />
              
              {/* Authentication button */}
              <AuthButton />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {viewMode === 'create' && (
          <div className="space-y-12">
            <LinkCreator onLinkCreated={handleLinkCreated} />
            
            {/* Features */}
            <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="group relative animate-float" style={{ animationDelay: '0s' }}>
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-500"></div>
                <div className="relative glass-card rounded-2xl p-8 text-center group-hover:scale-105 transition-all duration-500">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg group-hover:shadow-2xl group-hover:scale-110 transition-all duration-300">
                    <LinkIcon className="h-8 w-8 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">
                    Contextual Domains
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    Choose from go2.video, go2.reviews, and go2.tools based on your content type
                  </p>
                </div>
              </div>
              
              <div className="group relative animate-float" style={{ animationDelay: '1s' }}>
                <div className="absolute inset-0 bg-gradient-to-r from-green-500/10 to-emerald-500/10 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-500"></div>
                <div className="relative glass-card rounded-2xl p-8 text-center group-hover:scale-105 transition-all duration-500">
                  <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg group-hover:shadow-2xl group-hover:scale-110 transition-all duration-300">
                    <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">
                    Safety First
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    All URLs are checked for safety with Google Safe Browsing and content filters
                  </p>
                </div>
              </div>
              
              <div className="group relative animate-float" style={{ animationDelay: '2s' }}>
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-500"></div>
                <div className="relative glass-card rounded-2xl p-8 text-center group-hover:scale-105 transition-all duration-500">
                  <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg group-hover:shadow-2xl group-hover:scale-110 transition-all duration-300">
                    <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">
                    Detailed Analytics
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    Track clicks, geographic data, devices, and referrers with beautiful charts
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {viewMode === 'display' && currentLink && (
          <LinkDisplay
            link={currentLink}
            onViewAnalytics={handleViewAnalytics}
          />
        )}

        {viewMode === 'analytics' && analyticsCode && (
          <AnalyticsDashboard
            code={analyticsCode}
            shortUrl={currentLink?.short_url}
          />
        )}

        {viewMode === 'dashboard' && (
          <UserDashboard />
        )}
      </main>

      {/* Footer */}
      <footer className="relative backdrop-blur-md bg-white/50 border-t border-white/20 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600">
            <p>&copy; 2024 Contextual URL Shortener. Built with Next.js and FastAPI.</p>
          </div>
        </div>
      </footer>

      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemoveToast={removeToast} />
    </div>
  );
}
