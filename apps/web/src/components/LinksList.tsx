'use client';

import React, { useState, useEffect } from 'react';
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
  Trash2
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

  const loadLinks = async () => {
    if (!mounted) return;
    
    setLoading(true);
    setError(null);
    
    try {
      console.log('Loading user links...');
      console.log('API Base URL:', process.env.NEXT_PUBLIC_API_BASE_URL);
      const data: LinkData[] = await apiClient.get('/api/links/');
      console.log('Links loaded successfully:', data.length, 'links');
      setLinks(data);
    } catch (err) {
      console.error('Failed to load links - Full error:', err);
      
      // Extract meaningful error message
      let errorMessage = 'Failed to load links';
      if (err && typeof err === 'object') {
        if ('error' in err && err.error && typeof err.error === 'object') {
          if ('message' in err.error) {
            errorMessage = err.error.message;
          } else if ('code' in err.error) {
            if (err.error.code === 'NO_AUTH_TOKEN' || err.error.code === 'UNAUTHORIZED') {
              errorMessage = 'Please sign in to view your links';
            } else {
              errorMessage = `Error: ${err.error.code}`;
            }
          }
        } else if ('message' in err) {
          errorMessage = err.message;
        }
      }
      
      setError(errorMessage);
    } finally {
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
  }, [mounted]);

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
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">
          My Links ({links.length})
        </h2>
        <Button
          variant="outline"
          size="sm"
          onClick={loadLinks}
        >
          Refresh
        </Button>
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