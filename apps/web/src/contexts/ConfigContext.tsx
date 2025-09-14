'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { type BaseDomain } from '@shared/types/link';
import { apiClient } from '@/lib/api';

interface DomainConfig {
  base_domains: BaseDomain[];
  domain_suggestions: Record<string, BaseDomain>;
}

interface ConfigContextType {
  domains: BaseDomain[];
  domainSuggestions: Record<string, BaseDomain>;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

// Cache configuration in memory
let cachedConfig: DomainConfig | null = null;
let cacheTimestamp: number | null = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

interface ConfigProviderProps {
  children: React.ReactNode;
}

export function ConfigProvider({ children }: ConfigProviderProps) {
  const [domains, setDomains] = useState<BaseDomain[]>(['go2.video', 'go2.reviews', 'go2.tools']);
  const [domainSuggestions, setDomainSuggestions] = useState<Record<string, BaseDomain>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConfig = async () => {
    // Check if we have valid cached data
    const now = Date.now();
    if (cachedConfig && cacheTimestamp && (now - cacheTimestamp) < CACHE_DURATION) {
      setDomains(cachedConfig.base_domains);
      setDomainSuggestions(cachedConfig.domain_suggestions || {});
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const config = await apiClient.get('/api/config/base-domains') as DomainConfig;
      
      if (config?.base_domains && Array.isArray(config.base_domains)) {
        // Update cache
        cachedConfig = config;
        cacheTimestamp = now;
        
        // Update state
        setDomains(config.base_domains);
        setDomainSuggestions(config.domain_suggestions || {});
      } else {
        // Fallback to default domains
        setDomains(['go2.video', 'go2.reviews', 'go2.tools']);
        setDomainSuggestions({});
      }
    } catch (err) {
      console.error('Failed to load domain configuration:', err);
      setError(err instanceof Error ? err.message : 'Failed to load configuration');
      
      // Use default domains on error
      setDomains(['go2.video', 'go2.reviews', 'go2.tools']);
      setDomainSuggestions({});
    } finally {
      setIsLoading(false);
    }
  };

  const refetch = async () => {
    // Clear cache and reload
    cachedConfig = null;
    cacheTimestamp = null;
    await loadConfig();
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const value: ConfigContextType = {
    domains,
    domainSuggestions,
    isLoading,
    error,
    refetch,
  };

  return (
    <ConfigContext.Provider value={value}>
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig() {
  const context = useContext(ConfigContext);
  if (context === undefined) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
}