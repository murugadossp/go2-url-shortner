'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useApiClient } from '@/lib/api';
import { useToast } from './ui/Toast';
import { useAdminStatus } from '@/hooks/useAdminStatus';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { 
  Link as LinkIcon, 
  Search, 
  Trash2, 
  Ban,
  Calendar,
  ExternalLink,
  User,
  Eye,
  RefreshCw,
  CheckSquare,
  Square,
  AlertTriangle
} from 'lucide-react';

interface LinkData {
  code: string;
  long_url: string;
  base_domain: string;
  owner_uid?: string;
  owner_info?: {
    uid: string;
    email: string;
    display_name: string;
  };
  disabled: boolean;
  expires_at?: string;
  created_at: string;
  click_count: number;
  is_custom_code: boolean;
  plan_type: 'free' | 'paid';
}

export function AdminLinkManagement() {

  const apiClient = useApiClient();
  const { toast } = useToast();
  const [links, setLinks] = useState<LinkData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLinks, setSelectedLinks] = useState<Set<string>>(new Set());
  const [isPerformingBulkAction, setIsPerformingBulkAction] = useState(false);
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'disabled' | 'expired'>('all');

  // Use cached admin status
  const { isAdmin } = useAdminStatus();

  const loadLinks = async () => {
    if (!isAdmin) return;
    
    setIsLoading(true);
    try {
      const response = await apiClient.get('/api/links/admin/all?limit=100') as { data: LinkData[] };
      setLinks(response.data);
    } catch (error) {
      console.error('Failed to load links:', error);
      toast.error('Failed to load links', 'Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleLinkSelection = (code: string) => {
    setSelectedLinks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(code)) {
        newSet.delete(code);
      } else {
        newSet.add(code);
      }
      return newSet;
    });
  };

  const toggleSelectAll = () => {
    if (selectedLinks.size === filteredLinks.length) {
      setSelectedLinks(new Set());
    } else {
      setSelectedLinks(new Set(filteredLinks.map(link => link.code)));
    }
  };

  const bulkDisableLinks = async () => {
    if (selectedLinks.size === 0) return;
    
    setIsPerformingBulkAction(true);
    try {
      const codes = Array.from(selectedLinks);
      const response = await apiClient.post('/api/links/admin/bulk-disable', codes) as {
        data: { disabled_count: number; errors: string[] }
      };
      
      const { disabled_count, errors } = response.data;
      
      if (errors && errors.length > 0) {
        toast.error(`Disabled ${disabled_count} links`, `${errors.length} errors occurred.`);
      } else {
        toast.success(`Successfully disabled ${disabled_count} links`);
      }
      
      // Refresh the links list
      await loadLinks();
      setSelectedLinks(new Set());
    } catch (error) {
      console.error('Failed to disable links:', error);
      toast.error('Failed to disable links', 'Please try again.');
    } finally {
      setIsPerformingBulkAction(false);
    }
  };

  const bulkDeleteLinks = async () => {
    if (selectedLinks.size === 0) return;
    
    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedLinks.size} links? This action cannot be undone.`
    );
    
    if (!confirmed) return;
    
    setIsPerformingBulkAction(true);
    try {
      const codes = Array.from(selectedLinks);
      const response = await apiClient.post('/api/links/admin/bulk-delete', codes) as {
        data: { deleted_count: number; errors: string[] }
      };
      
      const { deleted_count, errors } = response.data;
      
      if (errors && errors.length > 0) {
        toast.error(`Deleted ${deleted_count} links`, `${errors.length} errors occurred.`);
      } else {
        toast.success(`Successfully deleted ${deleted_count} links`);
      }
      
      // Refresh the links list
      await loadLinks();
      setSelectedLinks(new Set());
    } catch (error) {
      console.error('Failed to delete links:', error);
      toast.error('Failed to delete links', 'Please try again.');
    } finally {
      setIsPerformingBulkAction(false);
    }
  };

  const bulkUpdateExpiry = async (expiryDate: Date | null) => {
    if (selectedLinks.size === 0) return;
    
    setIsPerformingBulkAction(true);
    try {
      const codes = Array.from(selectedLinks);
      const response = await apiClient.post('/api/links/admin/bulk-update-expiry', {
        codes,
        expires_at: expiryDate?.toISOString() || null
      }) as {
        data: { updated_count: number; errors: string[] }
      };
      
      const { updated_count, errors } = response.data;
      
      if (errors && errors.length > 0) {
        toast.error(`Updated ${updated_count} links`, `${errors.length} errors occurred.`);
      } else {
        toast.success(`Successfully updated expiry for ${updated_count} links`);
      }
      
      // Refresh the links list
      await loadLinks();
      setSelectedLinks(new Set());
    } catch (error) {
      console.error('Failed to update expiry:', error);
      toast.error('Failed to update expiry', 'Please try again.');
    } finally {
      setIsPerformingBulkAction(false);
    }
  };

  const isLinkExpired = (expiresAt?: string) => {
    if (!expiresAt) return false;
    return new Date(expiresAt) < new Date();
  };

  const filteredLinks = (links || []).filter(link => {
    const matchesSearch = 
      link.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      link.long_url.toLowerCase().includes(searchTerm.toLowerCase()) ||
      link.owner_info?.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      link.owner_info?.display_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = 
      filterStatus === 'all' ||
      (filterStatus === 'active' && !link.disabled && !isLinkExpired(link.expires_at)) ||
      (filterStatus === 'disabled' && link.disabled) ||
      (filterStatus === 'expired' && isLinkExpired(link.expires_at));
    
    return matchesSearch && matchesFilter;
  });

  useEffect(() => {
    loadLinks();
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
      {/* Header */}
      <div className="mb-8">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-cyan-500/10 rounded-2xl blur-xl"></div>
          <div className="relative backdrop-blur-xl bg-white/70 border border-white/20 rounded-2xl shadow-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent">
                  Link Management
                </h2>
                <p className="text-gray-600 mt-1">Manage and monitor all shortened links</p>
              </div>
              <Button
                onClick={loadLinks}
                disabled={isLoading}
                variant="outline"
                className="flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6">

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            type="text"
            placeholder="Search links by code, URL, or owner..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as any)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">All Links</option>
          <option value="active">Active</option>
          <option value="disabled">Disabled</option>
          <option value="expired">Expired</option>
        </select>
      </div>

      {/* Bulk Actions */}
      {selectedLinks.size > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-blue-800 font-medium">
              {selectedLinks.size} link{selectedLinks.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex gap-2">
              <Button
                onClick={bulkDisableLinks}
                disabled={isPerformingBulkAction}
                variant="outline"
                className="text-orange-600 hover:text-orange-700"
              >
                <Ban className="w-4 h-4 mr-1" />
                Disable
              </Button>
              <Button
                onClick={() => bulkUpdateExpiry(null)}
                disabled={isPerformingBulkAction}
                variant="outline"
                className="text-blue-600 hover:text-blue-700"
              >
                <Calendar className="w-4 h-4 mr-1" />
                Remove Expiry
              </Button>
              <Button
                onClick={bulkDeleteLinks}
                disabled={isPerformingBulkAction}
                variant="outline"
                className="text-red-600 hover:text-red-700"
              >
                <Trash2 className="w-4 h-4 mr-1" />
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Links Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading links...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left">
                    <button
                      onClick={toggleSelectAll}
                      className="flex items-center text-gray-500 hover:text-gray-700"
                    >
                      {selectedLinks.size === filteredLinks.length && filteredLinks.length > 0 ? (
                        <CheckSquare className="w-4 h-4" />
                      ) : (
                        <Square className="w-4 h-4" />
                      )}
                    </button>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Link
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Owner
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Stats
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredLinks.map((link) => (
                  <tr key={link.code} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => toggleLinkSelection(link.code)}
                        className="text-gray-500 hover:text-gray-700"
                      >
                        {selectedLinks.has(link.code) ? (
                          <CheckSquare className="w-4 h-4 text-blue-600" />
                        ) : (
                          <Square className="w-4 h-4" />
                        )}
                      </button>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0">
                          <LinkIcon className="h-5 w-5 text-gray-400" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="text-sm font-medium text-gray-900 flex items-center gap-2">
                            <span className="font-mono">{link.code}</span>
                            {link.is_custom_code && (
                              <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                                Custom
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-gray-500 truncate max-w-xs">
                            {link.base_domain}/{link.code}
                          </div>
                          <div className="text-xs text-gray-400 truncate max-w-md">
                            → {link.long_url}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {link.owner_info ? (
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-8 w-8">
                            <div className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center">
                              <User className="h-4 w-4 text-gray-600" />
                            </div>
                          </div>
                          <div className="ml-3">
                            <div className="text-sm font-medium text-gray-900">
                              {link.owner_info.display_name}
                            </div>
                            <div className="text-sm text-gray-500">
                              {link.owner_info.email}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">Anonymous</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center gap-1">
                        <Eye className="h-3 w-3 text-gray-400" />
                        {link.click_count} clicks
                      </div>
                      <div className="text-xs text-gray-500">
                        {link.plan_type} plan
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {link.disabled ? (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                          Disabled
                        </span>
                      ) : isLinkExpired(link.expires_at) ? (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                          Expired
                        </span>
                      ) : (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                          Active
                        </span>
                      )}
                      {link.expires_at && (
                        <div className="text-xs text-gray-500 mt-1">
                          Expires: {new Date(link.expires_at).toLocaleDateString()}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(link.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center gap-2">
                        <a
                          href={`https://${link.base_domain}/${link.code}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-900"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                        <button
                          onClick={() => toggleLinkSelection(link.code)}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          <AlertTriangle className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredLinks.length === 0 && !isLoading && (
              <div className="text-center py-12">
                <LinkIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No links found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {searchTerm || filterStatus !== 'all' 
                    ? 'Try adjusting your search or filter criteria.' 
                    : 'No links have been created yet.'}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Summary */}
      {!isLoading && links && links.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-900">{links?.length || 0}</div>
              <div className="text-sm text-gray-600">Total Links</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {(links || []).filter(l => !l.disabled && !isLinkExpired(l.expires_at)).length}
              </div>
              <div className="text-sm text-gray-600">Active Links</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">
                {(links || []).filter(l => l.disabled).length}
              </div>
              <div className="text-sm text-gray-600">Disabled Links</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {links.reduce((sum, l) => sum + l.click_count, 0)}
              </div>
              <div className="text-sm text-gray-600">Total Clicks</div>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}