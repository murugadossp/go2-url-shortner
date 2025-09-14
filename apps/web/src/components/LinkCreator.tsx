'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { LinkCreationFormSchema, type LinkCreationFormData } from '@shared/validation/forms';
import { type CreateLinkResponse } from '@shared/types/link';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Select } from './ui/Select';
import { useApiClient } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useUser } from '@/hooks/useUser';
import { useDomains } from '@/hooks/useDomains';
import { debounce } from '@/lib/utils';
import { AlertCircle, Check, Loader2, ChevronDown, ChevronUp, Settings, Lock, Calendar, Crown, Zap } from 'lucide-react';
import { useToast } from './ui/Toast';
import { formatErrorForDisplay, logError } from '@/utils/errorHandling';

interface LinkCreatorProps {
  onLinkCreated?: (link: CreateLinkResponse) => void;
}



export function LinkCreator({ onLinkCreated }: LinkCreatorProps) {
  const { user } = useAuth();
  const { 
    profile, 
    canCreateCustomCode, 
    shouldShowUpgradePrompt, 
    getUsagePercentage,
    upgradePlan,
    refreshData 
  } = useUser();
  const apiClient = useApiClient();
  const { toast } = useToast();
  const { domainOptions, suggestDomainForUrl } = useDomains();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isUpgrading, setIsUpgrading] = useState(false);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const previousUrlRef = useRef<string>('');
  const [customCodeAvailability, setCustomCodeAvailability] = useState<{
    checking: boolean;
    available: boolean | null;
    suggestions: string[];
  }>({
    checking: false,
    available: null,
    suggestions: [],
  });

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
    reset,
  } = useForm<LinkCreationFormData>({
    resolver: zodResolver(LinkCreationFormSchema),
    defaultValues: {
      base_domain: 'go2.tools',
    },
  });

  const watchedUrl = watch('long_url');
  const watchedCustomCode = watch('custom_code');

  // Domain configuration is now provided by ConfigContext - no API call needed!

  // Auto-suggest domain based on URL
  useEffect(() => {
    if (watchedUrl && watchedUrl !== previousUrlRef.current) {
      previousUrlRef.current = watchedUrl;
      const suggestedDomain = suggestDomainForUrl(watchedUrl);
      setValue('base_domain', suggestedDomain);
    }
  }, [watchedUrl, setValue, suggestDomainForUrl]);

  // Check custom code availability
  const checkCustomCodeAvailability = debounce(async (code: string) => {
    if (!code || code.length < 3) {
      setCustomCodeAvailability({ checking: false, available: null, suggestions: [] });
      return;
    }

    setCustomCodeAvailability(prev => ({ ...prev, checking: true }));

    try {
      const response = await apiClient.get(`/api/links/check-availability/${encodeURIComponent(code)}`) as { available: boolean; suggestions?: string[] };
      setCustomCodeAvailability({
        checking: false,
        available: response.available,
        suggestions: response.suggestions || [],
      });
    } catch (error) {
      logError(error, 'custom code availability check');
      setCustomCodeAvailability({
        checking: false,
        available: false,
        suggestions: [],
      });
    }
  }, 500);

  useEffect(() => {
    if (watchedCustomCode) {
      checkCustomCodeAvailability(watchedCustomCode);
    } else {
      setCustomCodeAvailability({ checking: false, available: null, suggestions: [] });
    }
  }, [watchedCustomCode]);

  const handleUpgrade = async () => {
    setIsUpgrading(true);
    try {
      const success = await upgradePlan();
      if (success) {
        toast.success('Plan upgraded!', 'You now have access to 100 custom codes per month.');
      }
    } catch (error) {
      logError(error, 'plan upgrade');
      const errorInfo = formatErrorForDisplay(error);
      toast.error('Upgrade failed', errorInfo.message);
    } finally {
      setIsUpgrading(false);
    }
  };

  const onSubmit = async (data: LinkCreationFormData) => {
    // Check custom code limits before submission
    if (data.custom_code && data.custom_code.trim() !== '' && user && !canCreateCustomCode()) {
      toast.error('Custom code limit reached', 'Upgrade to paid plan for more custom codes.');
      return;
    }

    setIsSubmitting(true);
    
    try {
      // Prepare data for API - start with minimal required fields
      const apiData: any = {
        long_url: data.long_url,
        base_domain: data.base_domain,
      };
      
      // Only include optional fields if they have actual values
      if (data.custom_code && data.custom_code.trim() !== '') {
        apiData.custom_code = data.custom_code.trim();
      }
      
      if (data.password && data.password.trim() !== '') {
        apiData.password = data.password.trim();
      }
      
      if (data.expires_at && data.expires_at instanceof Date && !isNaN(data.expires_at.getTime())) {
        apiData.expires_at = data.expires_at.toISOString();
      }
      
      const response: CreateLinkResponse = await apiClient.post('/api/links/shorten', apiData);
      toast.success('Link created successfully!', 'Your short link is ready to share.');
      onLinkCreated?.(response);
      reset();
      setCustomCodeAvailability({ checking: false, available: null, suggestions: [] });
      
      // Refresh user data to update usage stats
      if (user && data.custom_code) {
        refreshData();
      }
    } catch (error) {
      logError(error, 'link creation');
      
      const errorInfo = formatErrorForDisplay(error);
      
      // Handle specific error cases with custom messages
      if (errorInfo.fieldErrors.custom_code) {
        toast.error('Custom code issue', errorInfo.fieldErrors.custom_code);
        return;
      }
      
      if (errorInfo.fieldErrors.long_url) {
        toast.error('URL issue', errorInfo.fieldErrors.long_url);
        return;
      }
      
      // Show general error message
      toast.error('Failed to create link', errorInfo.message);
    } finally {
      setIsSubmitting(false);
    }
  };



  return (
    <div className="w-full max-w-3xl mx-auto relative">
      {/* Glassmorphic background effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-cyan-500/10 rounded-3xl blur-xl"></div>
      
      <div className="relative backdrop-blur-xl bg-white/70 border border-white/20 rounded-3xl shadow-2xl p-8 md:p-10">
        {/* Header Section */}
        <div className="mb-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-6">
            Create Smart Short Links
          </h2>
          <p className="text-lg text-gray-700 max-w-2xl mx-auto leading-relaxed">
            Create memorable short links with contextual domains. 
            Track analytics and generate QR codes.
          </p>
        </div>

        {/* Plan Limit Notifications */}
        {user && profile && shouldShowUpgradePrompt() && (
          <div className="mb-6 p-4 bg-gradient-to-r from-purple-500/10 via-pink-500/10 to-purple-500/10 border border-purple-500/20 rounded-2xl backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 shadow-lg">
                  <Crown className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {profile.custom_codes_remaining === 0 ? 'Custom Code Limit Reached!' : 'Almost at your limit!'}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {profile.custom_codes_remaining === 0 
                      ? 'Upgrade to paid plan for 100 custom codes per month.'
                      : `${profile.custom_codes_remaining} custom codes remaining. Upgrade for more!`
                    }
                  </p>
                </div>
              </div>
              <Button
                type="button"
                onClick={handleUpgrade}
                disabled={isUpgrading}
                className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium px-4 py-2"
              >
                {isUpgrading ? <Loader2 className="h-4 w-4 animate-spin" /> : (
                  <>
                    <Zap className="h-4 w-4 mr-1" />
                    Upgrade
                  </>
                )}
              </Button>
            </div>
            
            {/* Usage Progress Bar */}
            <div className="mt-3">
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Custom Code Usage</span>
                <span>{Math.round(getUsagePercentage())}% used</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    getUsagePercentage() >= 90 
                      ? 'bg-gradient-to-r from-red-500 to-red-600'
                      : getUsagePercentage() >= 80
                      ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                      : 'bg-gradient-to-r from-blue-500 to-purple-500'
                  }`}
                  style={{ width: `${getUsagePercentage()}%` }}
                />
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Essential Fields */}
          <div className="space-y-6">
            {/* URL Input */}
            <div className="group">
              <Input
                {...register('long_url')}
                label="Long URL"
                placeholder="https://example.com/very/long/url"
                error={errors.long_url?.message}
                aria-describedby="url-help"
                className="transition-all duration-300 group-hover:shadow-lg"
              />
              <p id="url-help" className="mt-2 text-sm text-gray-500">
                Enter the URL you want to shorten (must include http:// or https://)
              </p>
            </div>

            {/* Domain and Custom Code Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Domain Selection */}
              <div className="group">
                <Select
                  {...register('base_domain')}
                  label="Domain"
                  options={domainOptions}
                  error={errors.base_domain?.message}
                  aria-describedby="domain-help"
                  className="transition-all duration-300 group-hover:shadow-lg"
                />
                <p id="domain-help" className="mt-2 text-sm text-gray-500">
                  Choose a contextual domain
                </p>
              </div>

              {/* Custom Code */}
              <div className="group">
                <div className="relative">
                  <Input
                    {...register('custom_code')}
                    label="Custom Code (Optional)"
                    placeholder="my-custom-link"
                    error={errors.custom_code?.message}
                    aria-describedby="custom-code-help"
                    className="transition-all duration-300 group-hover:shadow-lg"
                  />
                  {watchedCustomCode && (
                    <div className="absolute right-3 top-8 flex items-center">
                      {customCodeAvailability.checking && (
                        <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                      )}
                      {!customCodeAvailability.checking && customCodeAvailability.available === true && (
                        <Check className="h-4 w-4 text-green-500" />
                      )}
                      {!customCodeAvailability.checking && customCodeAvailability.available === false && (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      )}
                    </div>
                  )}
                </div>
                <p id="custom-code-help" className="mt-2 text-sm text-gray-500">
                  Create memorable custom code
                  {user && profile && (
                    <span className={`font-medium ${profile.custom_codes_remaining <= 1 ? 'text-red-600' : 'text-blue-600'}`}>
                      • {profile.custom_codes_remaining} remaining
                    </span>
                  )}
                  {!user && (
                    <span className="text-amber-600 font-medium"> • Sign in for limits</span>
                  )}
                </p>
              </div>
            </div>

            {/* URL Preview */}
            {(watch('base_domain') || watchedCustomCode) && (
              <div className="p-4 bg-gradient-to-r from-blue-50/60 to-purple-50/60 border border-blue-200/30 rounded-xl backdrop-blur-sm">
                <p className="text-sm font-medium text-gray-700 mb-2">Your short link will be:</p>
                <div className="font-mono text-lg text-blue-600 break-all">
                  {watch('base_domain') || 'go2.tools'}/{watchedCustomCode || 'random-code'}
                </div>
              </div>
            )}

            {/* Submit Button - Always visible */}
            <div className="flex justify-center pt-4">
              <Button
                type="submit"
                size="lg"
                loading={isSubmitting}
                disabled={
                  isSubmitting || 
                  Boolean(watchedCustomCode && customCodeAvailability.available === false && !customCodeAvailability.checking) ||
                  Boolean(watchedCustomCode && user && !canCreateCustomCode())
                }
                className="w-full lg:w-auto h-14 px-12 py-4 text-xl font-bold shadow-2xl hover:shadow-3xl hover:scale-105"
              >
                {isSubmitting ? 'Creating...' : 'Create Link'}
              </Button>
            </div>
            
            {/* Custom Code Limit Warning */}
            {watchedCustomCode && user && !canCreateCustomCode() && (
              <div className="p-4 bg-gradient-to-r from-red-50/80 to-pink-50/80 border border-red-200/50 rounded-xl backdrop-blur-sm">
                <p className="text-sm text-red-800 font-medium">
                  Custom code limit reached. Remove the custom code or upgrade to paid plan.
                </p>
              </div>
            )}
            
            {/* Custom Code Suggestions */}
            {customCodeAvailability.available === false && customCodeAvailability.suggestions.length > 0 && (
              <div className="p-4 bg-gradient-to-r from-amber-50/80 to-yellow-50/80 border border-amber-200/50 rounded-xl backdrop-blur-sm">
                <p className="text-sm text-amber-800 mb-3 font-medium">
                  This code is already taken. Try these suggestions:
                </p>
                <div className="flex flex-wrap gap-2">
                  {customCodeAvailability.suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => {
                        setValue('custom_code', suggestion);
                        // Reset availability state to trigger fresh check
                        setCustomCodeAvailability({ checking: false, available: null, suggestions: [] });
                      }}
                      className="px-3 py-1.5 text-sm bg-gradient-to-r from-amber-100 to-yellow-100 text-amber-800 rounded-lg hover:from-amber-200 hover:to-yellow-200 transition-all duration-200 border border-amber-200/50"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>



          {/* Advanced Options Toggle */}
          <div className="border-t border-gray-200/50 pt-2">
            <button
              type="button"
              onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
              className="flex items-center justify-between w-full p-3 rounded-xl bg-gradient-to-r from-gray-50/50 to-white/50 border border-gray-200/30 hover:from-gray-100/50 hover:to-white/70 transition-all duration-300 group"
            >
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                  <Settings className="h-5 w-5 text-white" />
                </div>
                <div className="text-left">
                  <h3 className="font-semibold text-gray-900">Advanced Options</h3>
                  <p className="text-sm text-gray-500">Password protection, expiration date</p>
                </div>
              </div>
              {showAdvancedOptions ? (
                <ChevronUp className="h-5 w-5 text-gray-400 transition-transform duration-300" />
              ) : (
                <ChevronDown className="h-5 w-5 text-gray-400 transition-transform duration-300" />
              )}
            </button>

            {/* Collapsible Advanced Options */}
            <div className={`overflow-hidden transition-all duration-500 ease-in-out ${
              showAdvancedOptions ? 'max-h-96 opacity-100 mt-4' : 'max-h-0 opacity-0'
            }`}>
              <div className="p-4 rounded-xl bg-gradient-to-br from-white/40 to-gray-50/40 border border-white/30 backdrop-blur-sm">
                {/* Password and Expiration Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Password Protection */}
                  <div className="group">
                    <div className="flex items-center space-x-2 mb-3">
                      <Lock className="h-4 w-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-700">Password Protection</span>
                    </div>
                    <Input
                      {...register('password')}
                      type="password"
                      placeholder="Enter password"
                      error={errors.password?.message}
                      aria-describedby="password-help"
                      maxLength={15}
                      className="transition-all duration-300 group-hover:shadow-lg"
                    />
                    <p id="password-help" className="mt-2 text-sm text-gray-500">
                      Password (4-15 characters)
                    </p>
                  </div>

                  {/* Expiration Date */}
                  <div className="group">
                    <div className="flex items-center space-x-2 mb-3">
                      <Calendar className="h-4 w-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-700">Expiration Date</span>
                    </div>
                    <Input
                      {...register('expires_at', {
                        setValueAs: (value: string) => {
                          // Convert empty string to undefined for optional field
                          if (!value || value === '' || value.trim() === '') {
                            return undefined;
                          }
                          // Convert valid datetime-local string to Date object
                          const date = new Date(value);
                          // Check if the date is valid
                          if (isNaN(date.getTime())) {
                            return undefined;
                          }
                          return date;
                        },
                      })}
                      type="datetime-local"
                      error={errors.expires_at?.message}
                      aria-describedby="expiry-help"
                      min={new Date().toISOString().slice(0, 16)}
                      className="transition-all duration-300 group-hover:shadow-lg"
                    />
                    <p id="expiry-help" className="mt-2 text-sm text-gray-500">
                      When link expires
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>


        </form>
      </div>
    </div>
  );
}