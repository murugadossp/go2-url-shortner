'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  BarChart3, 
  Copy, 
  ExternalLink, 
  Eye, 
  Calendar,
  MousePointer,
  Globe,
  Smartphone,
  Download,
  MoreVertical,
  Edit,
  Trash2,
  Search,
  Filter,
  X,
  ChevronDown
} from 'lucide-react';
import { useApiClient } from '@/lib/api';
import { Button } from './ui/Button';
import { formatDate, formatDateTime } from '@/lib/utils';

interface LinkData {
  code: string;
  long_url: string;
  base_domain: string;
  created_at: string;
  disabled: boolean;
  expires_at?: string;
  total_clicks: number;
  owner_uid?: string;
  is_custom_code: boolean;
}

interface LinksListProps {
  onViewAnalytics?: (code: string, shortUrl: string) => void;
}

export function LinksList({ onViewAnalytics }: LinksListProps) {
  const apiClient = useApiClient();
  const [links, setLinks] = useState<LinkData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'created_at' | 'clicks' | 'expires_at' | 'code'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'expired' | 'disabled'>('all');
  const [filterType, setFilterType] = useState<'all' | 'custom' | 'generated'>('all');
  const [showFilters, setShowFilters] = useState(false);

  // Debounced search
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState(searchQuery);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearchQuery(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const loadLinks = async () => {
    if (!mounted) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Build query parameters
      const params = new URLSearchParams();
      
      if (debouncedSearchQuery.trim()) {
        params.set('search', debouncedSearchQuery.trim());
      }
      
      params.set('sort_by', sortBy);
      params.set('order', sortOrder);
      
      if (filterStatus !== 'all') {
        params.set('filter_status', filterStatus);
      }
      
      if (filterType !== 'all') {
        params.set('filter_type', filterType);
      }
      
      const queryString = params.toString();
      const endpoint = queryString ? `/api/links/?${queryString}` : '/api/links/';
      
      console.log('🔄 Making API call to:', endpoint);
      
      const data: LinkData[] = await apiClient.get(endpoint);
      
      console.log('✅ Links loaded successfully!');
      console.log('✅ Number of links:', data.length);
      
      setLinks(data);
    } catch (err) {
      console.error('❌ Failed to load links');
      console.error('❌ Error type:', typeof err);
      console.error('❌ Error object:', err);
      console.error('❌ Full error details:', JSON.stringify(err, null, 2));
      
      // Check if it's a structured API error
      if (err && typeof err === 'object') {
        if ('error' in err && err.error && typeof err.error === 'object') {
          if ('code' in err.error) {
            console.error('❌ API Error code:', err.error.code);
          }
          if ('message' in err.error) {
            console.error('❌ API Error message:', err.error.message);
          }
        }
        if ('message' in err) {
          console.error('❌ Error message:', err.message);
        }
        if ('status' in err) {
          console.error('❌ HTTP status:', err.status);
        }
      }
      
      // Extract meaningful error message
      let errorMessage = 'Failed to retrieve links';
      if (err && typeof err === 'object') {
        if ('error' in err && err.error && typeof err.error === 'object') {
          if ('message' in err.error && typeof err.error.message === 'string') {
            errorMessage = err.error.message;
            console.log('🔧 Using error.message:', errorMessage);
          } else if ('code' in err.error && typeof err.error.code === 'string') {
            if (err.error.code === 'NO_AUTH_TOKEN' || err.error.code === 'UNAUTHORIZED') {
              errorMessage = 'Please sign in to view your links';
            } else {
              errorMessage = `Error: ${err.error.code}`;
            }
            console.log('🔧 Using error code:', err.error.code, '→', errorMessage);
          }
        } else if ('message' in err && typeof err.message === 'string') {
          errorMessage = err.message;
          console.log('🔧 Using top-level message:', errorMessage);
        }
      }
      
      console.log('🔧 Final error message shown to user:', errorMessage);
      setError(errorMessage);
    } finally {
      console.log('🔄 loadLinks completed, setting loading to false');
      setLoading(false);
    }
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted) {
      loadLinks();
    }
  }, [mounted, debouncedSearchQuery, sortBy, sortOrder, filterStatus, filterType]);

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('');
    setSortBy('created_at');
    setSortOrder('desc');
    setFilterStatus('all');
    setFilterType('all');
  };

  // Check if any filters are active
  const hasActiveFilters = searchQuery || filterStatus !== 'all' || filterType !== 'all' || sortBy !== 'created_at' || sortOrder !== 'desc';

  const copyToClipboard = async (text: string) => {
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard) {
        await navigator.clipboard.writeText(text);
        // You could add a toast notification here
      }
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleViewAnalytics = (link: LinkData) => {
    const shortUrl = `https://${link.base_domain}/${link.code}`;
    if (onViewAnalytics) {
      onViewAnalytics(link.code, shortUrl);
    }
  };

  if (!mounted || loading) {
    return (
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
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">My Links</h2>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-red-800">
            <h3 className="font-medium">Error loading links</h3>
            <p className="text-sm mt-1">{error}</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadLinks}
            className="mt-3"
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (links.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">My Links</h2>
        </div>
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <MousePointer className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No links yet</h3>
          <p className="text-gray-600">Create your first short link to get started!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">My Links</h2>
        <Button variant="outline" size="sm" onClick={loadLinks}>
          Refresh
        </Button>
      </div>

      {/* Search and Sort Controls */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search Bar */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search links, URLs, or domains..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Sort Dropdown */}
          <div className="relative">
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-') as [typeof sortBy, typeof sortOrder];
                setSortBy(field);
                setSortOrder(order);
              }}
              className="appearance-none bg-white border border-gray-300 rounded-lg px-3 py-2 pr-8 focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-[160px]"
            >
              <option value="created_at-desc">Newest First</option>
              <option value="created_at-asc">Oldest First</option>
              <option value="clicks-desc">Most Clicks</option>
              <option value="clicks-asc">Least Clicks</option>
              <option value="code-asc">A-Z</option>
              <option value="code-desc">Z-A</option>
              <option value="expires_at-asc">Expiring Soon</option>
            </select>
            <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
          </div>

          {/* Filter Toggle */}
          <Button
            variant={showFilters ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <Filter className="h-4 w-4" />
            Filters
            {hasActiveFilters && (
              <span className="bg-blue-600 text-white text-xs rounded-full h-2 w-2"></span>
            )}
          </Button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
            <div className="flex flex-wrap gap-3">
              {/* Status Filter */}
              <div className="flex flex-col">
                <label className="text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value as typeof filterStatus)}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                >
                  <option value="all">All</option>
                  <option value="active">Active</option>
                  <option value="expired">Expired</option>
                  <option value="disabled">Disabled</option>
                </select>
              </div>

              {/* Type Filter */}
              <div className="flex flex-col">
                <label className="text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value as typeof filterType)}
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                >
                  <option value="all">All</option>
                  <option value="custom">Custom</option>
                  <option value="generated">Generated</option>
                </select>
              </div>
            </div>

            {/* Clear Filters */}
            {hasActiveFilters && (
              <div className="flex justify-end">
                <Button variant="ghost" size="sm" onClick={clearFilters} className="flex items-center gap-1">
                  <X className="h-3 w-3" />
                  Clear All
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Results Count */}
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            Showing {links.length} link{links.length !== 1 ? 's' : ''}
            {hasActiveFilters && ' (filtered)'}
          </span>
          {hasActiveFilters && !showFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters} className="flex items-center gap-1 text-xs">
              <X className="h-3 w-3" />
              Clear filters
            </Button>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {links.map((link) => {
          const shortUrl = `https://${link.base_domain}/${link.code}`;
          const isExpired = link.expires_at && new Date(link.expires_at) < new Date();
          
          return (
            <div
              key={link.code}
              className={`bg-white border rounded-lg p-4 hover:shadow-md transition-shadow ${
                link.disabled || isExpired ? 'opacity-60' : ''
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                {/* Link Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-medium text-gray-900 truncate">
                      {shortUrl}
                    </h3>
                    {link.is_custom_code && (
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                        Custom
                      </span>
                    )}
                    {link.disabled && (
                      <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                        Disabled
                      </span>
                    )}
                    {isExpired && (
                      <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded">
                        Expired
                      </span>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-600 truncate mb-2">
                    → {link.long_url}
                  </p>
                  
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <MousePointer className="h-3 w-3" />
                      {link.total_clicks.toLocaleString()} clicks
                    </div>
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {formatDate(new Date(link.created_at))}
                    </div>
                    {link.expires_at && (
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        Expires {formatDate(new Date(link.expires_at))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(shortUrl)}
                    title="Copy short URL"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => typeof window !== 'undefined' && window.open(shortUrl, '_blank')}
                    title="Open link"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleViewAnalytics(link)}
                    title="View analytics"
                    className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                  >
                    <BarChart3 className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Quick Stats */}
              {link.total_clicks > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Quick stats available</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewAnalytics(link)}
                      className="text-xs text-blue-600 hover:text-blue-700"
                    >
                      View detailed analytics →
                    </Button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
