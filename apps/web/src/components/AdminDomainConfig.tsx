'use client';

import React, { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { useApiClient } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from './ui/Toast';
import { useAdminStatus } from '@/hooks/useAdminStatus';
import { Plus, Trash2, Save, RefreshCw } from 'lucide-react';

const DomainConfigSchema = z.object({
  base_domains: z.array(z.enum(['go2.video', 'go2.reviews', 'go2.tools'])).min(1, 'At least one domain is required'),
  domain_suggestions: z.array(z.object({
    pattern: z.string().min(1, 'Pattern is required'),
    domain: z.enum(['go2.video', 'go2.reviews', 'go2.tools'])
  }))
});

type DomainConfigFormData = z.infer<typeof DomainConfigSchema>;

interface DomainConfig {
  base_domains: string[];
  domain_suggestions: Record<string, string>;
  last_updated?: string;
}

export function AdminDomainConfig() {
  const { user } = useAuth();
  const apiClient = useApiClient();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [config, setConfig] = useState<DomainConfig | null>(null);

  const {
    register,
    handleSubmit,
    control,
    setValue,
    watch,
    formState: { errors },
    reset
  } = useForm<DomainConfigFormData>({
    resolver: zodResolver(DomainConfigSchema),
    defaultValues: {
      base_domains: ['go2.video', 'go2.reviews', 'go2.tools'],
      domain_suggestions: []
    }
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'domain_suggestions'
  });

  const watchedDomains = watch('base_domains');

  // Use cached admin status
  const { isAdmin } = useAdminStatus();

  const loadConfig = async () => {
    if (!isAdmin) return;
    
    setIsLoading(true);
    try {
      const response = await apiClient.get('/api/config/admin/domains') as DomainConfig;
      const configData = response;
      setConfig(configData);
      
      // Convert domain_suggestions object to array for form
      const suggestionsArray = Object.entries(configData.domain_suggestions || {}).map(([pattern, domain]) => ({
        pattern,
        domain: domain as 'go2.video' | 'go2.reviews' | 'go2.tools'
      }));
      
      reset({
        base_domains: configData.base_domains as ('go2.video' | 'go2.reviews' | 'go2.tools')[],
        domain_suggestions: suggestionsArray
      });
    } catch (error) {
      console.error('Failed to load domain config:', error);
      toast.error('Failed to load configuration', 'Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const onSubmit = async (data: DomainConfigFormData) => {
    if (!isAdmin) return;
    
    setIsSaving(true);
    try {
      // Convert domain_suggestions array back to object
      const domainSuggestions = data.domain_suggestions.reduce((acc, item) => {
        acc[item.pattern] = item.domain;
        return acc;
      }, {} as Record<string, string>);
      
      const requestData = {
        base_domains: data.base_domains,
        domain_suggestions: domainSuggestions
      };
      
      await apiClient.put('/api/config/admin/domains', requestData);
      toast.success('Configuration updated', 'Domain configuration has been saved successfully.');
      
      // Reload config to get updated timestamp
      await loadConfig();
    } catch (error) {
      console.error('Failed to update domain config:', error);
      toast.error('Failed to update configuration', 'Please check your input and try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const addSuggestion = () => {
    append({ pattern: '', domain: 'go2.tools' });
  };

  useEffect(() => {
    loadConfig();
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
                  Domain Configuration
                </h2>
                <p className="text-gray-600 mt-1">Manage available domains and URL suggestions</p>
                {config?.last_updated && (
                  <p className="text-sm text-gray-500 mt-1">
                    Last updated: {new Date(config.last_updated).toLocaleString()}
                  </p>
                )}
              </div>
              <Button
                onClick={loadConfig}
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

      <div className="bg-white rounded-lg shadow-lg p-8">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading configuration...</span>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
            {/* Base Domains Section */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Available Base Domains</h2>
              <p className="text-gray-600 mb-4">Select which domains are available for creating short links.</p>
              
              <div className="space-y-3">
                {['go2.video', 'go2.reviews', 'go2.tools'].map((domain) => (
                  <label key={domain} className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      value={domain}
                      {...register('base_domains')}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <span className="text-gray-900 font-medium">{domain}</span>
                    <span className="text-gray-500 text-sm">
                      {domain === 'go2.video' && '- For video content (YouTube, Vimeo, etc.)'}
                      {domain === 'go2.reviews' && '- For review sites (Amazon, Yelp, etc.)'}
                      {domain === 'go2.tools' && '- For tools and utilities (GitHub, docs, etc.)'}
                    </span>
                  </label>
                ))}
              </div>
              
              {errors.base_domains && (
                <p className="text-red-600 text-sm mt-2">{errors.base_domains.message}</p>
              )}
            </div>

            {/* Domain Suggestions Section */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Domain Suggestions</h2>
                  <p className="text-gray-600 mt-1">Configure automatic domain suggestions based on URL patterns.</p>
                </div>
                <Button
                  type="button"
                  onClick={addSuggestion}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Suggestion
                </Button>
              </div>

              <div className="space-y-4">
                {fields.map((field, index) => (
                  <div key={field.id} className="flex items-center gap-4 p-4 border border-gray-200 rounded-lg">
                    <div className="flex-1">
                      <Input
                        {...register(`domain_suggestions.${index}.pattern`)}
                        placeholder="e.g., youtube.com"
                        label="URL Pattern"
                        error={errors.domain_suggestions?.[index]?.pattern?.message}
                      />
                    </div>
                    <div className="flex-1">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Suggested Domain
                      </label>
                      <select
                        {...register(`domain_suggestions.${index}.domain`)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        {watchedDomains.map((domain) => (
                          <option key={domain} value={domain}>
                            {domain}
                          </option>
                        ))}
                      </select>
                    </div>
                    <Button
                      type="button"
                      onClick={() => remove(index)}
                      variant="outline"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}

                {fields.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No domain suggestions configured. Click "Add Suggestion" to create one.
                  </div>
                )}
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end pt-6 border-t border-gray-200">
              <Button
                type="submit"
                disabled={isSaving}
                className="flex items-center gap-2"
              >
                {isSaving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Save Configuration
                  </>
                )}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
