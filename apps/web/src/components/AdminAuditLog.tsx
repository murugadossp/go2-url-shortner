'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useApiClient } from '@/lib/api';
import { useToast } from './ui/Toast';
import { useAdminStatus } from '@/hooks/useAdminStatus';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { 
  Shield, 
  Search, 
  Calendar,
  User,
  Activity,
  RefreshCw,
  Clock,
  AlertCircle,
  CheckCircle,
  Info
} from 'lucide-react';

interface AuditLogEntry {
  id: string;
  admin_uid: string;
  action: string;
  target_uid?: string;
  details: Record<string, any>;
  timestamp: string;
  ip_address?: string;
  admin_info?: {
    uid: string;
    email: string;
    display_name: string;
  };
  target_info?: {
    uid: string;
    email: string;
    display_name: string;
  };
}

const actionLabels: Record<string, string> = {
  'update_user_plan': 'Updated User Plan',
  'toggle_admin_status': 'Changed Admin Status',
  'bulk_disable_links': 'Bulk Disabled Links',
  'bulk_delete_links': 'Bulk Deleted Links',
  'bulk_update_expiry': 'Bulk Updated Expiry',
  'update_domain_config': 'Updated Domain Config',
  'disable_link': 'Disabled Link',
  'delete_link': 'Deleted Link',
  'update_link': 'Updated Link'
};

const actionIcons: Record<string, React.ComponentType<any>> = {
  'update_user_plan': User,
  'toggle_admin_status': Shield,
  'bulk_disable_links': AlertCircle,
  'bulk_delete_links': AlertCircle,
  'bulk_update_expiry': Calendar,
  'update_domain_config': Activity,
  'disable_link': AlertCircle,
  'delete_link': AlertCircle,
  'update_link': CheckCircle
};

const actionColors: Record<string, string> = {
  'update_user_plan': 'text-blue-600 bg-blue-100',
  'toggle_admin_status': 'text-purple-600 bg-purple-100',
  'bulk_disable_links': 'text-orange-600 bg-orange-100',
  'bulk_delete_links': 'text-red-600 bg-red-100',
  'bulk_update_expiry': 'text-green-600 bg-green-100',
  'update_domain_config': 'text-indigo-600 bg-indigo-100',
  'disable_link': 'text-orange-600 bg-orange-100',
  'delete_link': 'text-red-600 bg-red-100',
  'update_link': 'text-green-600 bg-green-100'
};

export function AdminAuditLog() {
  const { user } = useAuth();
  const apiClient = useApiClient();
  const { toast } = useToast();
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAction, setFilterAction] = useState<string>('all');

  // Use cached admin status
  const { isAdmin } = useAdminStatus();

  const loadAuditLog = async () => {
    if (!isAdmin) return;
    
    setIsLoading(true);
    try {
      const response = await apiClient.get('/api/users/admin/audit-log?limit=100') as AuditLogEntry[];
      setAuditLog(response);
    } catch (error) {
      console.error('Failed to load audit log:', error);
      toast.error('Failed to load audit log', 'Please try again later.');
      setAuditLog([]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatActionDetails = (action: string, details: Record<string, any>) => {
    switch (action) {
      case 'update_user_plan':
        return `Changed plan to ${details.new_plan}`;
      case 'toggle_admin_status':
        return details.is_admin ? 'Granted admin privileges' : 'Revoked admin privileges';
      case 'bulk_disable_links':
        return `Disabled ${details.disabled_count} links${details.errors?.length ? ` (${details.errors.length} errors)` : ''}`;
      case 'bulk_delete_links':
        return `Deleted ${details.deleted_count} links${details.errors?.length ? ` (${details.errors.length} errors)` : ''}`;
      case 'bulk_update_expiry':
        return `Updated expiry for ${details.updated_count} links${details.errors?.length ? ` (${details.errors.length} errors)` : ''}`;
      case 'update_domain_config':
        return 'Updated domain configuration';
      default:
        return JSON.stringify(details);
    }
  };

  const filteredLog = (auditLog || []).filter(entry => {
    const matchesSearch = 
      entry.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.admin_uid.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (entry.target_uid && entry.target_uid.toLowerCase().includes(searchTerm.toLowerCase())) ||
      formatActionDetails(entry.action, entry.details).toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterAction === 'all' || entry.action === filterAction;
    
    return matchesSearch && matchesFilter;
  });

  const uniqueActions = Array.from(new Set((auditLog || []).map(entry => entry.action)));

  useEffect(() => {
    loadAuditLog();
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
                  Audit Log
                </h2>
                <p className="text-gray-600 mt-1">Track administrative actions and system changes</p>
              </div>
              <Button
                onClick={loadAuditLog}
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

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            type="text"
            placeholder="Search audit log..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <select
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">All Actions</option>
          {uniqueActions.map(action => (
            <option key={action} value={action}>
              {actionLabels[action] || action}
            </option>
          ))}
        </select>
      </div>

      {/* Audit Log */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading audit log...</span>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredLog.map((entry) => {
              const ActionIcon = actionIcons[entry.action] || Info;
              const actionColor = actionColors[entry.action] || 'text-gray-600 bg-gray-100';
              
              return (
                <div key={entry.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start space-x-4">
                    <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${actionColor}`}>
                      <ActionIcon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-sm font-medium text-gray-900">
                            {actionLabels[entry.action] || entry.action}
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">
                            {formatActionDetails(entry.action, entry.details)}
                          </p>
                        </div>
                        <div className="flex items-center text-sm text-gray-500">
                          <Clock className="w-4 h-4 mr-1" />
                          {new Date(entry.timestamp).toLocaleString()}
                        </div>
                      </div>
                      
                      <div className="mt-3 flex items-center space-x-6 text-sm text-gray-500">
                        <div className="flex items-center">
                          <User className="w-4 h-4 mr-1" />
                          <span>
                            Admin: {entry.admin_info ? 
                              `${entry.admin_info.display_name} (${entry.admin_info.email})` : 
                              entry.admin_uid}
                          </span>
                        </div>
                        {entry.target_uid && (
                          <div className="flex items-center">
                            <User className="w-4 h-4 mr-1" />
                            <span>
                              Target: {entry.target_info ? 
                                `${entry.target_info.display_name} (${entry.target_info.email})` : 
                                entry.target_uid}
                            </span>
                          </div>
                        )}
                        {entry.ip_address && (
                          <div className="flex items-center">
                            <Activity className="w-4 h-4 mr-1" />
                            <span>IP: {entry.ip_address}</span>
                          </div>
                        )}
                      </div>
                      
                      {/* Additional Details */}
                      {Object.keys(entry.details).length > 0 && (
                        <details className="mt-3">
                          <summary className="cursor-pointer text-sm text-blue-600 hover:text-blue-800">
                            View Details
                          </summary>
                          <div className="mt-2 p-3 bg-gray-50 rounded-md">
                            <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                              {JSON.stringify(entry.details, null, 2)}
                            </pre>
                          </div>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {filteredLog.length === 0 && !isLoading && (
              <div className="text-center py-12">
                <Shield className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No audit entries found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {searchTerm || filterAction !== 'all' 
                    ? 'Try adjusting your search or filter criteria.' 
                    : 'No administrative actions have been logged yet.'}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Summary */}
      {!isLoading && auditLog && auditLog.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-900">{auditLog?.length || 0}</div>
              <div className="text-sm text-gray-600">Total Entries</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {new Set(auditLog.map(e => e.admin_uid)).size}
              </div>
              <div className="text-sm text-gray-600">Active Admins</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {(auditLog || []).filter(e => e.timestamp > new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()).length}
              </div>
              <div className="text-sm text-gray-600">Last 24 Hours</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {uniqueActions?.length || 0}
              </div>
              <div className="text-sm text-gray-600">Action Types</div>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
