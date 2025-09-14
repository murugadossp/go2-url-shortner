'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useApiClient } from '@/lib/api';
import { useToast } from './ui/Toast';
import { useAdminStatus } from '@/hooks/useAdminStatus';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { 
  Users, 
  Search, 
  Crown, 
  UserMinus,
  TrendingUp,
  Calendar,
  Mail,
  User,
  Shield,
  RefreshCw
} from 'lucide-react';

interface UserProfile {
  email: string;
  display_name: string;
  plan_type: 'free' | 'paid';
  custom_codes_used: number;
  custom_codes_remaining: number;
  custom_codes_reset_date: string;
  created_at: string;
  is_admin: boolean;
}

export function AdminUserManagement() {
  const { user } = useAuth();
  const apiClient = useApiClient();
  const { toast } = useToast();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const [isUpdating, setIsUpdating] = useState<Set<string>>(new Set());

  // Use cached admin status
  const { isAdmin } = useAdminStatus();

  const loadUsers = async () => {
    if (!isAdmin) return;
    
    setIsLoading(true);
    try {
      const response = await apiClient.get('/api/users/admin/all?limit=100') as UserProfile[];
      setUsers(response);
    } catch (error) {
      console.error('Failed to load users:', error);
      toast.error('Failed to load users', 'Please try again later.');
      setUsers([]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleAdminStatus = async (userEmail: string, currentStatus: boolean) => {
    setIsUpdating(prev => new Set(prev).add(userEmail));
    
    try {
      // Find user by email to get UID (in real implementation, we'd have UID in the response)
      const targetUser = users.find(u => u.email === userEmail);
      if (!targetUser) {
        throw new Error('User not found');
      }

      // For demo purposes, we'll use email as identifier
      // In production, you'd use the actual UID
      await apiClient.put(`/api/users/admin/${userEmail}/admin-status`, {
        is_admin: !currentStatus
      });

      // Update local state
      setUsers(prev => prev.map(u => 
        u.email === userEmail 
          ? { ...u, is_admin: !currentStatus }
          : u
      ));

      toast.success(
        `Admin status ${!currentStatus ? 'granted' : 'revoked'}`,
        `${targetUser.display_name} is ${!currentStatus ? 'now' : 'no longer'} an administrator.`
      );
    } catch (error) {
      console.error('Failed to toggle admin status:', error);
      toast.error('Failed to update admin status', 'Please try again.');
    } finally {
      setIsUpdating(prev => {
        const newSet = new Set(prev);
        newSet.delete(userEmail);
        return newSet;
      });
    }
  };

  const updateUserPlan = async (userEmail: string, newPlan: 'free' | 'paid') => {
    setIsUpdating(prev => new Set(prev).add(userEmail));
    
    try {
      const targetUser = users.find(u => u.email === userEmail);
      if (!targetUser) {
        throw new Error('User not found');
      }

      await apiClient.put(`/api/users/admin/${userEmail}/plan`, {
        plan_type: newPlan
      });

      // Update local state
      setUsers(prev => prev.map(u => 
        u.email === userEmail 
          ? { ...u, plan_type: newPlan }
          : u
      ));

      toast.success(
        'Plan updated',
        `${targetUser.display_name}'s plan has been updated to ${newPlan}.`
      );
    } catch (error) {
      console.error('Failed to update user plan:', error);
      toast.error('Failed to update plan', 'Please try again.');
    } finally {
      setIsUpdating(prev => {
        const newSet = new Set(prev);
        newSet.delete(userEmail);
        return newSet;
      });
    }
  };

  const filteredUsers = (users || []).filter(user =>
    user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.display_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  useEffect(() => {
    loadUsers();
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
                  User Management
                </h2>
                <p className="text-gray-600 mt-1">Manage user accounts and permissions</p>
              </div>
              <Button
                onClick={loadUsers}
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

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
        <Input
          type="text"
          placeholder="Search users by email or name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading users...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Plan
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usage
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Joined
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredUsers.map((userProfile) => (
                  <tr key={userProfile.email} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10">
                          <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                            <User className="h-5 w-5 text-gray-600" />
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900 flex items-center gap-2">
                            {userProfile.display_name}
                            {userProfile.is_admin && (
                              <Shield className="h-4 w-4 text-blue-600" aria-label="Administrator" />
                            )}
                          </div>
                          <div className="text-sm text-gray-500 flex items-center gap-1">
                            <Mail className="h-3 w-3" />
                            {userProfile.email}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        userProfile.plan_type === 'paid'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {userProfile.plan_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center gap-1">
                        <TrendingUp className="h-3 w-3 text-gray-400" />
                        {userProfile.custom_codes_used} / {userProfile.custom_codes_used + userProfile.custom_codes_remaining}
                      </div>
                      <div className="text-xs text-gray-500">
                        custom codes
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(userProfile.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                        Active
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      {/* Plan Toggle */}
                      <Button
                        onClick={() => updateUserPlan(
                          userProfile.email, 
                          userProfile.plan_type === 'free' ? 'paid' : 'free'
                        )}
                        disabled={isUpdating.has(userProfile.email)}
                        variant="outline"
                        className="text-xs"
                      >
                        {isUpdating.has(userProfile.email) ? (
                          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current"></div>
                        ) : (
                          `Make ${userProfile.plan_type === 'free' ? 'Paid' : 'Free'}`
                        )}
                      </Button>

                      {/* Admin Toggle */}
                      <Button
                        onClick={() => toggleAdminStatus(userProfile.email, userProfile.is_admin)}
                        disabled={isUpdating.has(userProfile.email) || userProfile.email === user?.email}
                        variant={userProfile.is_admin ? "outline" : "primary"}
                        className={`text-xs ${
                          userProfile.is_admin 
                            ? 'text-red-600 hover:text-red-700' 
                            : 'text-blue-600 hover:text-blue-700'
                        }`}
                      >
                        {isUpdating.has(userProfile.email) ? (
                          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current"></div>
                        ) : userProfile.is_admin ? (
                          <>
                            <UserMinus className="h-3 w-3 mr-1" />
                            Revoke Admin
                          </>
                        ) : (
                          <>
                            <Crown className="h-3 w-3 mr-1" />
                            Make Admin
                          </>
                        )}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredUsers.length === 0 && !isLoading && (
              <div className="text-center py-12">
                <Users className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No users found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {searchTerm ? 'Try adjusting your search terms.' : 'No users have signed up yet.'}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Summary */}
      {!isLoading && users && users.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-900">{users?.length || 0}</div>
              <div className="text-sm text-gray-600">Total Users</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {(users || []).filter(u => u.plan_type === 'paid').length}
              </div>
              <div className="text-sm text-gray-600">Paid Users</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {(users || []).filter(u => u.is_admin).length}
              </div>
              <div className="text-sm text-gray-600">Administrators</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-600">
                {(users || []).reduce((sum, u) => sum + u.custom_codes_used, 0)}
              </div>
              <div className="text-sm text-gray-600">Custom Codes Used</div>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
