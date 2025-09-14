'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useApiClient } from '@/lib/api';
import { useToast } from './ui/Toast';
import { useAdminStatus } from '@/hooks/useAdminStatus';
import { Button } from './ui/Button';
import { 
  Users, 
  Link, 
  BarChart3, 
  Shield, 
  Settings,
  TrendingUp,
  AlertTriangle,
  Clock,
  Eye
} from 'lucide-react';

interface SystemStats {
  users: {
    total: number;
    free: number;
    paid: number;
    admin: number;
    recent_signups: number;
  };
  links: {
    total: number;
    custom_codes: number;
    disabled: number;
    recent_created: number;
  };
  engagement: {
    total_clicks: number;
    avg_clicks_per_link: number;
  };
  last_updated: string;
}

interface AdminDashboardProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export function AdminDashboard({ activeTab, onTabChange }: AdminDashboardProps) {
  const { user } = useAuth();
  const apiClient = useApiClient();
  const { toast } = useToast();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Use cached admin status
  const { isAdmin, refreshAdminStatus, lastChecked } = useAdminStatus();

  const loadStats = async () => {
    if (!isAdmin) return;
    
    setIsLoading(true);
    try {
      const response = await apiClient.get('/api/users/admin/stats/overview') as { data: SystemStats };
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load admin stats:', error);
      toast.error('Failed to load statistics', 'Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, [isAdmin]);

  if (!isAdmin) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="text-lg font-semibold text-red-800 mb-2">Access Denied</h2>
          <p className="text-red-600">You need administrator privileges to access this page.</p>
        </div>
      </div>
    );
  }

  return (
    <div>

      {/* Overview Content */}
      {(
        <div className="space-y-8">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Loading statistics...</span>
            </div>
          ) : stats ? (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Total Users */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Users className="h-8 w-8 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">Total Users</p>
                      <p className="text-2xl font-semibold text-gray-900">{stats.users.total}</p>
                      <p className="text-sm text-green-600">
                        +{stats.users.recent_signups} this week
                      </p>
                    </div>
                  </div>
                </div>

                {/* Total Links */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Link className="h-8 w-8 text-green-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">Total Links</p>
                      <p className="text-2xl font-semibold text-gray-900">{stats.links.total}</p>
                      <p className="text-sm text-green-600">
                        +{stats.links.recent_created} this week
                      </p>
                    </div>
                  </div>
                </div>

                {/* Total Clicks */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <TrendingUp className="h-8 w-8 text-purple-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">Total Clicks</p>
                      <p className="text-2xl font-semibold text-gray-900">{stats.engagement.total_clicks}</p>
                      <p className="text-sm text-gray-600">
                        {stats.engagement.avg_clicks_per_link} avg per link
                      </p>
                    </div>
                  </div>
                </div>

                {/* Issues */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <AlertTriangle className="h-8 w-8 text-red-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">Disabled Links</p>
                      <p className="text-2xl font-semibold text-gray-900">{stats.links.disabled}</p>
                      <p className="text-sm text-gray-600">
                        {((stats.links.disabled / stats.links.total) * 100).toFixed(1)}% of total
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Detailed Stats */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* User Breakdown */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">User Breakdown</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Free Plan Users</span>
                      <span className="font-semibold">{stats.users.free}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Paid Plan Users</span>
                      <span className="font-semibold">{stats.users.paid}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Admin Users</span>
                      <span className="font-semibold">{stats.users.admin}</span>
                    </div>
                    <div className="pt-2 border-t">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-900 font-medium">Total Users</span>
                        <span className="font-bold text-lg">{stats.users.total}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Link Breakdown */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Link Breakdown</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Custom Code Links</span>
                      <span className="font-semibold">{stats.links.custom_codes}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Auto-generated Links</span>
                      <span className="font-semibold">{stats.links.total - stats.links.custom_codes}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Disabled Links</span>
                      <span className="font-semibold text-red-600">{stats.links.disabled}</span>
                    </div>
                    <div className="pt-2 border-t">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-900 font-medium">Total Links</span>
                        <span className="font-bold text-lg">{stats.links.total}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Last Updated */}
              <div className="text-center text-sm text-gray-500 space-y-2">
                <div>
                  <Clock className="w-4 h-4 inline mr-1" />
                  Stats updated: {new Date(stats.last_updated).toLocaleString()}
                </div>
                {lastChecked && (
                  <div>
                    Admin status cached: {new Date(lastChecked).toLocaleString()}
                  </div>
                )}
                <div className="space-x-2">
                  <Button
                    onClick={loadStats}
                    variant="outline"
                    className="text-xs"
                  >
                    Refresh Stats
                  </Button>
                  <Button
                    onClick={refreshAdminStatus}
                    variant="outline"
                    className="text-xs"
                  >
                    Refresh Admin Status
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500">Failed to load statistics</p>
              <Button onClick={loadStats} className="mt-4">
                Try Again
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}