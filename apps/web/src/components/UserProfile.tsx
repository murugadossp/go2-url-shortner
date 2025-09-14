'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Toast } from '@/components/ui/Toast';

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

interface UsageStats {
  total_links: number;
  custom_code_links: number;
  total_clicks: number;
  plan_type: 'free' | 'paid';
  custom_codes_used: number;
  custom_codes_remaining: number;
  custom_codes_reset_date: string;
}

export function UserProfile() {
  const { user, signOut, getIdToken } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [upgrading, setUpgrading] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    if (user) {
      fetchUserData();
    }
  }, [user]);

  const fetchUserData = async () => {
    try {
      const token = await getIdToken();
      if (!token) return;

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };

      // Fetch profile and usage stats in parallel
      const [profileResponse, usageResponse] = await Promise.all([
        fetch('/api/users/profile', { headers }),
        fetch('/api/users/usage', { headers })
      ]);

      if (profileResponse.ok) {
        const profileData = await profileResponse.json();
        setProfile(profileData);
        setDisplayName(profileData.display_name);
      }

      if (usageResponse.ok) {
        const usageData = await usageResponse.json();
        setUsageStats(usageData);
      }
    } catch (error) {
      console.error('Error fetching user data:', error);
      setToast({ message: 'Failed to load user data', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async () => {
    if (!displayName.trim()) return;

    setUpdating(true);
    try {
      const token = await getIdToken();
      if (!token) return;

      const response = await fetch('/api/users/profile', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ display_name: displayName.trim() }),
      });

      if (response.ok) {
        setToast({ message: 'Profile updated successfully', type: 'success' });
        await fetchUserData(); // Refresh data
      } else {
        throw new Error('Failed to update profile');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      setToast({ message: 'Failed to update profile', type: 'error' });
    } finally {
      setUpdating(false);
    }
  };

  const upgradePlan = async () => {
    setUpgrading(true);
    try {
      const token = await getIdToken();
      if (!token) return;

      const response = await fetch('/api/users/upgrade', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ plan_type: 'paid' }),
      });

      if (response.ok) {
        const result = await response.json();
        setToast({ message: result.message, type: 'success' });
        await fetchUserData(); // Refresh data
      } else {
        throw new Error('Failed to upgrade plan');
      }
    } catch (error) {
      console.error('Error upgrading plan:', error);
      setToast({ message: 'Failed to upgrade plan', type: 'error' });
    } finally {
      setUpgrading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getProgressPercentage = () => {
    if (!profile) return 0;
    const total = profile.custom_codes_used + profile.custom_codes_remaining;
    return total > 0 ? (profile.custom_codes_used / total) * 100 : 0;
  };

  if (!user) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600 mb-4">Please sign in to view your profile</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Profile Section */}
      <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
        <h2 className="text-2xl font-bold text-white mb-6">Profile</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Email
            </label>
            <Input
              type="email"
              value={profile?.email || ''}
              disabled
              className="bg-gray-800/50"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Display Name
            </label>
            <div className="flex gap-2">
              <Input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter display name"
              />
              <Button
                onClick={updateProfile}
                disabled={updating || !displayName.trim() || displayName === profile?.display_name}
                className="whitespace-nowrap"
              >
                {updating ? <LoadingSpinner size="sm" /> : 'Update'}
              </Button>
            </div>
          </div>
        </div>

        <div className="mt-4 text-sm text-gray-400">
          Member since {profile && formatDate(profile.created_at)}
        </div>
      </div>

      {/* Plan & Usage Section */}
      <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">Plan & Usage</h2>
          {profile?.plan_type === 'free' && (
            <Button
              onClick={upgradePlan}
              disabled={upgrading}
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
            >
              {upgrading ? <LoadingSpinner size="sm" /> : 'Upgrade to Paid'}
            </Button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <div className="bg-white/5 rounded-xl p-4">
            <div className="text-2xl font-bold text-white">{usageStats?.total_links || 0}</div>
            <div className="text-sm text-gray-400">Total Links</div>
          </div>
          
          <div className="bg-white/5 rounded-xl p-4">
            <div className="text-2xl font-bold text-white">{usageStats?.total_clicks || 0}</div>
            <div className="text-sm text-gray-400">Total Clicks</div>
          </div>
          
          <div className="bg-white/5 rounded-xl p-4">
            <div className="text-2xl font-bold text-white">{usageStats?.custom_code_links || 0}</div>
            <div className="text-sm text-gray-400">Custom Codes</div>
          </div>
          
          <div className="bg-white/5 rounded-xl p-4">
            <div className="text-2xl font-bold text-white capitalize">{profile?.plan_type}</div>
            <div className="text-sm text-gray-400">Plan Type</div>
          </div>
        </div>

        {/* Custom Code Usage */}
        <div className="bg-white/5 rounded-xl p-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-white font-medium">Custom Code Usage</span>
            <span className="text-sm text-gray-400">
              {profile?.custom_codes_used || 0} / {(profile?.custom_codes_used || 0) + (profile?.custom_codes_remaining || 0)} used
            </span>
          </div>
          
          <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
            <div
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${getProgressPercentage()}%` }}
            />
          </div>
          
          <div className="text-xs text-gray-400">
            Resets on {profile && formatDate(profile.custom_codes_reset_date)}
          </div>
          
          {profile?.custom_codes_remaining === 0 && profile?.plan_type === 'free' && (
            <div className="mt-3 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
              <p className="text-yellow-400 text-sm">
                You've reached your custom code limit. Upgrade to paid plan for 100 custom codes per month.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Plan Features */}
      <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
        <h2 className="text-2xl font-bold text-white mb-6">Plan Features</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white/5 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">Free Plan</h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li>• Basic URL shortening</li>
              <li>• QR code generation</li>
              <li>• Basic analytics</li>
              <li>• 5 custom codes per month</li>
            </ul>
          </div>
          
          <div className="bg-white/5 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-white mb-3">Paid Plan</h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li>• All free features</li>
              <li>• 100 custom codes per month</li>
              <li>• Advanced analytics</li>
              <li>• Priority support</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Account Actions */}
      <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
        <h2 className="text-2xl font-bold text-white mb-6">Account Actions</h2>
        
        <Button
          onClick={signOut}
          variant="outline"
          className="border-red-500/50 text-red-400 hover:bg-red-500/10"
        >
          Sign Out
        </Button>
      </div>
    </div>
  );
}