import { useCallback, useMemo } from 'react';
import { useConfig } from '@/contexts/ConfigContext';

/**
 * Hook to get domain configuration with formatted options for Select components
 */
export function useDomains() {
  const { domains, domainSuggestions, isLoading, error } = useConfig();

  const domainOptions = useMemo(() => domains.map(domain => ({
    value: domain,
    label: domain,
  })), [domains]);

  const suggestDomainForUrl = useCallback((url: string) => {
    if (!url || domains.length === 0) return domains[0] || 'go2.tools';

    try {
      const urlObj = new URL(url);
      const hostname = urlObj.hostname.toLowerCase();
      
      // Use server-provided domain suggestions if available
      for (const [pattern, suggestedDomain] of Object.entries(domainSuggestions)) {
        if (hostname.includes(pattern.toLowerCase())) {
          return suggestedDomain;
        }
      }
      
      // Fallback to hardcoded logic if no server suggestions match
      if (hostname.includes('youtube.com') || hostname.includes('youtu.be') || hostname.includes('vimeo.com')) {
        return domains.includes('go2.video') ? 'go2.video' : domains[0];
      } else if (hostname.includes('amazon.com') || hostname.includes('ebay.com') || hostname.includes('etsy.com') || hostname.includes('review')) {
        return domains.includes('go2.reviews') ? 'go2.reviews' : domains[0];
      } else {
        return domains.includes('go2.tools') ? 'go2.tools' : domains[0];
      }
    } catch {
      // Invalid URL, return default
      return domains[0] || 'go2.tools';
    }
  }, [domains, domainSuggestions]);

  return {
    domains,
    domainOptions,
    domainSuggestions,
    isLoading,
    error,
    suggestDomainForUrl,
  };
}