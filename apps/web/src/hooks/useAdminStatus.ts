'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useApiClient } from '@/lib/api';

const ADMIN_CACHE_KEY = 'admin_status_cache';
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

interface AdminCache {
  isAdmin: boolean;
  userId: string;
  timestamp: number;
}

export function useAdminStatus() {
  const { user } = useAuth();
  const apiClient = useApiClient();
  const [isAdmin, setIsAdmin] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [lastChecked, setLastChecked] = useState<number | null>(null);
  const hasCheckedRef = useRef(false);

  // Get cached admin status
  const getCachedAdminStatus = (userId: string): boolean | null => {
    try {
      const cached = localStorage.getItem(ADMIN_CACHE_KEY);
      if (!cached) return null;

      const adminCache: AdminCache = JSON.parse(cached);
      
      // Check if cache is for the same user and still valid
      if (
        adminCache.userId === userId &&
        Date.now() - adminCache.timestamp < CACHE_DURATION
      ) {
        console.log('Using cached admin status:', adminCache.isAdmin);
        return adminCache.isAdmin;
      }
      
      // Cache is stale or for different user
      localStorage.removeItem(ADMIN_CACHE_KEY);
      return null;
    } catch (error) {
      console.error('Error reading admin cache:', error);
      localStorage.removeItem(ADMIN_CACHE_KEY);
      return null;
    }
  };

  // Cache admin status
  const cacheAdminStatus = (userId: string, adminStatus: boolean) => {
    try {
      const adminCache: AdminCache = {
        isAdmin: adminStatus,
        userId,
        timestamp: Date.now()
      };
      localStorage.setItem(ADMIN_CACHE_KEY, JSON.stringify(adminCache));
      console.log('Cached admin status:', adminStatus, 'for user:', userId);
    } catch (error) {
      console.error('Error caching admin status:', error);
    }
  };

  // Clear admin cache
  const clearAdminCache = () => {
    localStorage.removeItem(ADMIN_CACHE_KEY);
    console.log('Admin cache cleared');
  };

  // Check admin status (with caching)
  const checkAdminStatus = async (forceRefresh = false) => {
    if (!user?.uid) {
      setIsAdmin(false);
      clearAdminCache();
      return false;
    }

    // Check cache first (unless force refresh)
    if (!forceRefresh) {
      const cachedStatus = getCachedAdminStatus(user.uid);
      if (cachedStatus !== null) {
        setIsAdmin(cachedStatus);
        setLastChecked(Date.now());
        return cachedStatus;
      }
    }

    setIsChecking(true);
    try {
      console.log('Checking admin status for user:', user.uid);
      const response = await apiClient.get('/api/users/admin/check');
      console.log('Admin check response:', response);
      
      const adminStatus = true; // If API call succeeds, user is admin
      setIsAdmin(adminStatus);
      setLastChecked(Date.now());
      
      // Cache the result
      cacheAdminStatus(user.uid, adminStatus);
      
      return adminStatus;
    } catch (error) {
      console.error('Admin check failed:', error);
      const adminStatus = false;
      setIsAdmin(adminStatus);
      setLastChecked(Date.now());
      
      // Cache the negative result too (to avoid repeated failed calls)
      cacheAdminStatus(user.uid, adminStatus);
      
      return adminStatus;
    } finally {
      setIsChecking(false);
    }
  };

  // Initial check when user changes
  useEffect(() => {
    if (user?.uid && !hasCheckedRef.current) {
      hasCheckedRef.current = true;
      checkAdminStatus();
    } else if (!user?.uid) {
      hasCheckedRef.current = false;
      setIsAdmin(false);
      clearAdminCache();
      setLastChecked(null);
    }
  }, [user?.uid]);

  // Reset check flag when user changes
  useEffect(() => {
    hasCheckedRef.current = false;
  }, [user?.uid]);

  return {
    isAdmin,
    isChecking,
    lastChecked,
    checkAdminStatus,
    clearAdminCache,
    refreshAdminStatus: () => checkAdminStatus(true)
  };
}