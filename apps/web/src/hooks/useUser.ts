'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useApiClient } from '@/lib/api';

export interface UserProfile {
  email: string;
  display_name: string;
  plan_type: 'free' | 'paid';
  custom_codes_used: number;
  custom_codes_remaining: number;
  custom_codes_reset_date: string;
  created_at: string;
  is_admin: boolean;
}

export interface UsageStats {
  total_links: number;
  custom_code_links: number;
  total_clicks: number;
  plan_type: 'free' | 'paid';
  custom_codes_used: number;
  custom_codes_remaining: number;
  custom_codes_reset_date: string;
}

export interface PlanLimits {
  plans: {
    free: {
      custom_codes: number;
      features: string[];
    };
    paid: {
      custom_codes: number;
      features: string[];
    };
  };
}

export function useUser() {
  const { user } = useAuth();
  const api = useApiClient();
  
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [planLimits, setPlanLimits] = useState<PlanLimits | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    if (!user) {
      setProfile(null);
      return;
    }

    try {
      const profileData = await api.get<UserProfile>('/api/users/profile');
      setProfile(profileData);
      setError(null);
    } catch (err) {
      // Don't log authentication errors during sign-out
      if (err instanceof Error && !err.message.includes('No authentication token')) {
        console.error('Error fetching user profile:', err);
        setError(err.message);
      }
    }
  }, [user, api]);

  const fetchUsageStats = useCallback(async () => {
    if (!user) {
      setUsageStats(null);
      return;
    }

    try {
      const usageData = await api.get<UsageStats>('/api/users/usage');
      setUsageStats(usageData);
      setError(null);
    } catch (err) {
      // Don't log authentication errors during sign-out
      if (err instanceof Error && !err.message.includes('No authentication token')) {
        console.error('Error fetching usage stats:', err);
        setError(err.message);
      }
    }
  }, [user, api]);

  const fetchPlanLimits = useCallback(async () => {
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/users/limits`);
      if (response.ok) {
        const limitsData = await response.json();
        setPlanLimits(limitsData);
      }
    } catch (err) {
      console.error('Error fetching plan limits:', err);
    }
  }, []);

  const fetchAllData = useCallback(async () => {
    if (!user) {
      setProfile(null);
      setUsageStats(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Fetch profile
      try {
        const profileData = await api.get<UserProfile>('/api/users/profile');
        setProfile(profileData);
      } catch (err) {
        if (err instanceof Error && !err.message.includes('No authentication token')) {
          console.error('Error fetching user profile:', err);
        }
      }

      // Fetch usage stats
      try {
        const usageData = await api.get<UsageStats>('/api/users/usage');
        setUsageStats(usageData);
      } catch (err) {
        if (err instanceof Error && !err.message.includes('No authentication token')) {
          console.error('Error fetching usage stats:', err);
        }
      }

      // Fetch plan limits
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        const response = await fetch(`${API_BASE_URL}/api/users/limits`);
        if (response.ok) {
          const limitsData = await response.json();
          setPlanLimits(limitsData);
        }
      } catch (err) {
        console.error('Error fetching plan limits:', err);
      }

      setError(null);
    } catch (err) {
      // Don't log authentication errors during sign-out
      if (err instanceof Error && !err.message.includes('No authentication token')) {
        console.error('Error fetching user data:', err);
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, [user, api]);

  const updateProfile = async (displayName: string): Promise<boolean> => {
    if (!user) return false;

    try {
      await api.put('/api/users/profile', { display_name: displayName });
      await fetchProfile(); // Refresh profile data
      return true;
    } catch (err) {
      console.error('Error updating profile:', err);
      setError(err instanceof Error ? err.message : 'Failed to update profile');
      return false;
    }
  };

  const upgradePlan = async (): Promise<boolean> => {
    if (!user) return false;

    try {
      await api.post('/api/users/upgrade', { plan_type: 'paid' });
      await fetchAllData(); // Refresh all data
      return true;
    } catch (err) {
      console.error('Error upgrading plan:', err);
      setError(err instanceof Error ? err.message : 'Failed to upgrade plan');
      return false;
    }
  };

  const canCreateCustomCode = (): boolean => {
    return profile ? profile.custom_codes_remaining > 0 : false;
  };

  const getUsagePercentage = (): number => {
    if (!profile) return 0;
    const total = profile.custom_codes_used + profile.custom_codes_remaining;
    return total > 0 ? (profile.custom_codes_used / total) * 100 : 0;
  };

  const shouldShowUpgradePrompt = (): boolean => {
    return profile?.plan_type === 'free' && (
      profile.custom_codes_remaining <= 1 || 
      getUsagePercentage() >= 80
    );
  };

  const formatResetDate = (dateString?: string): string => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Fetch data when user changes
  useEffect(() => {
    if (user) {
      fetchAllData();
    } else {
      // Clear all data immediately when user signs out
      setProfile(null);
      setUsageStats(null);
      setError(null);
      setLoading(false);
    }
  }, [user]); // Remove fetchAllData from dependencies to prevent infinite loop

  return {
    // Data
    profile,
    usageStats,
    planLimits,
    loading,
    error,
    
    // Actions
    updateProfile,
    upgradePlan,
    refreshData: fetchAllData,
    
    // Computed values
    canCreateCustomCode,
    getUsagePercentage,
    shouldShowUpgradePrompt,
    formatResetDate,
    
    // User state
    isAuthenticated: !!user,
    isPaidUser: profile?.plan_type === 'paid',
  };
}