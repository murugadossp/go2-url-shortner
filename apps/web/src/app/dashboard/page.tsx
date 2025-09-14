'use client';

import React, { useState } from 'react';
import { Navigation } from '@/components/Navigation';
import { LinksList } from '@/components/LinksList';
import { AnalyticsDashboard } from '@/components/AnalyticsDashboard';
import { AuthButton } from '@/components/AuthButton';
import { ClientOnly } from '@/components/ClientOnly';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { useAuth } from '@/contexts/AuthContext';
import { ArrowLeft, BarChart3 } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function DashboardPage() {
  const { user } = useAuth();
  const [currentView, setCurrentView] = useState<'links' | 'analytics'>('links');
  const [selectedLink, setSelectedLink] = useState<{ code: string; shortUrl: string } | null>(null);

  const handleViewAnalytics = (code: string, shortUrl: string) => {
    setSelectedLink({ code, shortUrl });
    setCurrentView('analytics');
  };

  const handleBackToLinks = () => {
    setCurrentView('links');
    setSelectedLink(null);
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Dashboard</h1>
          <p className="text-gray-600 mb-6">Please sign in to view your dashboard</p>
          <AuthButton />
        </div>
      </div>
    );
  }

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
                <Navigation currentPage="dashboard" />
              </div>
              
              {/* Logo and Title */}
              <div className="flex items-center">
                <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <h1 className="ml-3 text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                  {currentView === 'analytics' ? 'Analytics' : 'Dashboard'}
                </h1>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <AuthButton />
            </div>
          </div>
        </div>
      </header>
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-7xl mx-auto">
          <ErrorBoundary>
            {currentView === 'links' ? (
              <>
                {/* Page Description */}
                <div className="mb-8">
                  <p className="text-gray-600">
                    Manage your short links and view analytics
                  </p>
                </div>

                {/* Links List */}
                <ClientOnly fallback={
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h2 className="text-xl font-semibold text-gray-900">My Links</h2>
                    </div>
                    <div className="space-y-3">
                      {[...Array(3)].map((_, i) => (
                        <div key={i} className="animate-pulse bg-gray-100 rounded-lg h-24"></div>
                      ))}
                    </div>
                  </div>
                }>
                  <LinksList onViewAnalytics={handleViewAnalytics} />
                </ClientOnly>
              </>
            ) : (
            <>
              {/* Analytics Navigation */}
              <div className="mb-8">
                <div className="flex items-center gap-4 mb-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleBackToLinks}
                    className="flex items-center gap-2"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    Back to Links
                  </Button>
                </div>
                
                <div className="bg-white/50 backdrop-blur-sm rounded-lg p-4 border border-white/20">
                  <p className="text-gray-600">
                    Detailed analytics for <span className="font-mono text-blue-600">{selectedLink?.shortUrl}</span>
                  </p>
                </div>
              </div>

              {/* Analytics Dashboard */}
              {selectedLink && (
                <ClientOnly fallback={
                  <div className="space-y-6">
                    <div className="animate-pulse space-y-6">
                      <div className="h-8 bg-gray-200 rounded w-1/3"></div>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        {[...Array(4)].map((_, i) => (
                          <div key={i} className="h-24 bg-gray-200 rounded"></div>
                        ))}
                      </div>
                      <div className="h-64 bg-gray-200 rounded"></div>
                    </div>
                  </div>
                }>
                  <AnalyticsDashboard 
                    code={selectedLink.code} 
                    shortUrl={selectedLink.shortUrl}
                  />
                </ClientOnly>
              )}
            </>
            )}
          </ErrorBoundary>
        </div>
      </div>
    </div>
  );
}