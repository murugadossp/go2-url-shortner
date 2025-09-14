'use client';

import React, { useState, useEffect } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { type LinkStats } from '@shared/types/analytics';
import { useApiClient } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { formatDate, formatDateTime } from '@/lib/utils';
import { 
  BarChart3, 
  Globe, 
  Smartphone, 
  Calendar, 
  Download,
  RefreshCw,
  TrendingUp,
  Users,
  MousePointer,
  Clock
} from 'lucide-react';
import { Button } from './ui/Button';
import { Select } from './ui/Select';
import { GeographicAnalytics } from './GeographicAnalytics';
import { ApiStatus } from './ApiStatus';

interface AnalyticsDashboardProps {
  code: string;
  shortUrl?: string;
}

interface ChartDataPoint {
  date: string;
  clicks: number;
}

interface TopItem {
  name: string;
  count: number;
  percentage: number;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

export function AnalyticsDashboard({ code, shortUrl }: AnalyticsDashboardProps) {
  const apiClient = useApiClient();
  const { getIdToken } = useAuth();
  const [stats, setStats] = useState<LinkStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<'7d' | '30d'>('7d');
  const [exporting, setExporting] = useState(false);

  const loadStats = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Loading analytics stats for code:', code, 'period:', period);
      
      // Use the original links stats endpoint (known to work)
      const data: LinkStats = await apiClient.get(`/api/links/stats/${code}?period=${period}`);
      setStats(data);
      console.log('Analytics loaded successfully:', data);
    } catch (err) {
      console.error('All analytics endpoints failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, [code, period]);

  const handleExport = async (format: 'json' | 'csv') => {
    setExporting(true);
    
    try {
      // Use the authenticated API client approach
      const token = await getIdToken();
      if (!token) {
        throw new Error('Authentication required for export');
      }

      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      console.log('Exporting analytics:', { code, format, period, apiBaseUrl });
      console.log('Auth token available:', !!token);
      
      // Test API connectivity first
      try {
        const healthResponse = await fetch(`${apiBaseUrl}/health`);
        console.log('API health check:', {
          status: healthResponse.status,
          ok: healthResponse.ok,
          contentType: healthResponse.headers.get('content-type')
        });
        
        if (healthResponse.ok) {
          const healthData = await healthResponse.text();
          console.log('Health response:', healthData.substring(0, 200));
        }
      } catch (healthError) {
        console.log('API health check failed - API server may not be running:', healthError);
      }
      
      const response = await fetch(`${apiBaseUrl}/api/links/export/${code}?format=${format}&period=${period}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        let errorMessage = 'Export failed';
        const contentType = response.headers.get('content-type');
        
        console.log('Export failed:', {
          status: response.status,
          statusText: response.statusText,
          contentType,
          url: response.url,
          headers: Object.fromEntries(response.headers.entries())
        });
        
        // Log the actual response text to see what we're getting
        const responseText = await response.text();
        console.log('Response text (first 500 chars):', responseText.substring(0, 500));
        
        if (contentType && contentType.includes('application/json')) {
          try {
            // Parse the response text we already got
            const errorData = JSON.parse(responseText);
            console.log('Error data:', errorData);
            errorMessage = errorData.detail || errorData.error?.message || errorMessage;
          } catch (parseError) {
            console.log('Failed to parse error JSON:', parseError);
            errorMessage = `Export failed: ${response.status} ${response.statusText}`;
          }
        } else {
          // If it's not JSON, it might be an HTML error page
          console.log('Non-JSON response, likely HTML error page');
          console.log('Response content type:', contentType);
          errorMessage = `Export failed: ${response.status} ${response.statusText}. Server returned HTML instead of JSON.`;
        }
        throw new Error(errorMessage);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${code}-analytics-${period}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Export failed:', err);
      
      // Try fallback to the original links router export endpoint
      try {
        console.log('Trying fallback export endpoint...');
        const token = await getIdToken(); // Get token again for fallback
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        
        const fallbackResponse = await fetch(`${apiBaseUrl}/api/analytics/export/${code}?format=${format}&period=${period}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (fallbackResponse.ok) {
          const blob = await fallbackResponse.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${code}-analytics-${period}.${format}`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          console.log('Fallback export successful');
          return; // Success with fallback
        }
      } catch (fallbackErr) {
        console.error('Fallback export also failed:', fallbackErr);
      }
      
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="w-full max-w-6xl mx-auto p-6">
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
    );
  }

  if (error) {
    return (
      <div className="w-full max-w-6xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-center">
            <div className="text-red-800">
              <h3 className="font-medium">Error loading analytics</h3>
              <p className="text-sm mt-1">{error}</p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadStats}
            className="mt-3"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  // Prepare chart data
  const chartData: ChartDataPoint[] = Object.entries(stats.clicks_by_day)
    .map(([date, clicks]) => ({
      date: formatDate(new Date(date)),
      clicks,
    }))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  // Prepare top referrers data
  const topReferrers: TopItem[] = Object.entries(stats.top_referrers)
    .map(([name, count]) => ({
      name: name || 'Direct',
      count,
      percentage: Math.round((count / stats.total_clicks) * 100),
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  // Prepare top devices data
  const topDevices: TopItem[] = Object.entries(stats.top_devices)
    .map(([name, count]) => ({
      name,
      count,
      percentage: Math.round((count / stats.total_clicks) * 100),
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  // Prepare geographic data
  const topCountries: TopItem[] = Object.entries(stats.geographic_stats.countries)
    .map(([name, count]) => ({
      name,
      count,
      percentage: Math.round((count / stats.total_clicks) * 100),
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  const periodOptions = [
    { value: '7d', label: 'Last 7 days' },
    { value: '30d', label: 'Last 30 days' },
  ];

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      {/* API Status */}
      <ApiStatus />
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <BarChart3 className="h-6 w-6 mr-2" />
            Analytics Dashboard
          </h2>
          {shortUrl && (
            <p className="text-gray-600 mt-1 font-mono text-sm">{shortUrl}</p>
          )}
        </div>
        
        <div className="flex items-center gap-3">
          <Select
            value={period}
            onChange={(e) => setPeriod(e.target.value as '7d' | '30d')}
            options={periodOptions}
            className="w-40"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={loadStats}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport('csv')}
            loading={exporting}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <MousePointer className="h-8 w-8 text-blue-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Clicks</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_clicks.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <Globe className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Countries</p>
              <p className="text-2xl font-bold text-gray-900">
                {Object.keys(stats.geographic_stats.countries).length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <Smartphone className="h-8 w-8 text-purple-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Devices</p>
              <p className="text-2xl font-bold text-gray-900">
                {Object.keys(stats.top_devices).length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-orange-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Last Click</p>
              <p className="text-sm font-bold text-gray-900">
                {stats.last_clicked 
                  ? formatDateTime(new Date(stats.last_clicked))
                  : 'Never'
                }
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Clicks Over Time Chart */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <TrendingUp className="h-5 w-5 mr-2" />
          Clicks Over Time
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="clicks" 
                stroke="#3B82F6" 
                strokeWidth={2}
                dot={{ fill: '#3B82F6' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Referrers and Devices */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Referrers */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Top Referrers
          </h3>
          {topReferrers.length > 0 ? (
            <div className="space-y-3">
              {topReferrers.map((referrer, index) => (
                <div key={referrer.name} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div 
                      className="w-3 h-3 rounded-full mr-3"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="text-sm text-gray-700 truncate max-w-48">
                      {referrer.name}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium text-gray-900">
                      {referrer.count}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      ({referrer.percentage}%)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No referrer data available</p>
          )}
        </div>

        {/* Top Devices */}
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Top Devices
          </h3>
          {topDevices.length > 0 ? (
            <div className="space-y-3">
              {topDevices.map((device, index) => (
                <div key={device.name} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div 
                      className="w-3 h-3 rounded-full mr-3"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="text-sm text-gray-700 capitalize">
                      {device.name}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium text-gray-900">
                      {device.count}
                    </span>
                    <span className="text-xs text-gray-500 ml-2">
                      ({device.percentage}%)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No device data available</p>
          )}
        </div>
      </div>

      {/* Enhanced Geographic Analytics */}
      <GeographicAnalytics 
        stats={stats.geographic_stats} 
        totalClicks={stats.total_clicks} 
      />

      {/* No Data State */}
      {stats.total_clicks === 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-md p-8 text-center">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No clicks yet
          </h3>
          <p className="text-gray-600">
            Share your link to start seeing analytics data here.
          </p>
        </div>
      )}
    </div>
  );
}