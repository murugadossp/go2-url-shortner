'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useUser } from '@/hooks/useUser';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Toast } from '@/components/ui/Toast';
import { AdminNavButton } from '@/components/AdminNavButton';
import { 
  Link as LinkIcon, 
  MousePointer, 
  Code, 
  Calendar,
  Crown,
  Zap,
  TrendingUp,
  Shield,
  Sparkles,
  BarChart3,
  Clock,
  CheckCircle
} from 'lucide-react';

export function UserDashboard() {
  const { user } = useAuth();
  const {
    profile,
    usageStats,
    planLimits,
    loading,
    upgradePlan,
    getUsagePercentage,
    shouldShowUpgradePrompt,
    formatResetDate
  } = useUser();
  const [upgrading, setUpgrading] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const handleUpgrade = async () => {
    setUpgrading(true);
    try {
      const success = await upgradePlan();
      if (success) {
        setToast({ message: 'Plan upgraded successfully!', type: 'success' });
      }
    } catch (error) {
      setToast({ message: 'Failed to upgrade plan', type: 'error' });
    } finally {
      setUpgrading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-8">
        {toast && (
          <Toast
            id="user-dashboard-toast"
            title={toast.type === 'success' ? 'Success' : 'Error'}
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}

        {/* Compact Welcome Section */}
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-cyan-500/10 rounded-2xl blur-xl"></div>
          <div className="relative backdrop-blur-xl bg-white/70 border border-white/20 rounded-2xl shadow-xl p-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent">
                    Welcome{profile ? `, ${profile.display_name.split(' ')[0]}` : ''}!
                  </h1>
                  <p className="text-sm text-gray-600">
                    {user ? 'Your dashboard overview' : 'Sign in to access your dashboard'}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                {/* Admin button */}
                <AdminNavButton />
                
                {profile?.plan_type && (
                  <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl border border-blue-200/30">
                    <Crown className={`h-4 w-4 ${profile.plan_type === 'paid' ? 'text-purple-600' : 'text-blue-600'}`} />
                    <div className="text-right">
                      <div className="text-xs text-gray-500">Plan</div>
                      <div className={`text-sm font-bold capitalize ${profile.plan_type === 'paid' ? 'text-purple-700' : 'text-blue-700'}`}>
                        {profile.plan_type}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {user && profile && usageStats && (
          <>
            {/* Stats Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Total Links Card */}
              <div className="group relative">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-500"></div>
                <div className="relative backdrop-blur-xl bg-white/70 border border-white/20 rounded-2xl shadow-xl p-6 group-hover:scale-105 transition-all duration-300">
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                      <LinkIcon className="h-6 w-6 text-white" />
                    </div>
                    <TrendingUp className="h-5 w-5 text-blue-500" />
                  </div>
                  <div className="text-3xl font-bold text-gray-900 mb-1">{usageStats.total_links}</div>
                  <div className="text-gray-600 font-medium">Total Links</div>
                  <div className="text-xs text-gray-500 mt-2">All time</div>
                </div>
              </div>

              {/* Total Clicks Card */}
              <div className="group relative">
                <div className="absolute inset-0 bg-gradient-to-r from-green-500/10 to-emerald-500/10 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-500"></div>
                <div className="relative backdrop-blur-xl bg-white/70 border border-white/20 rounded-2xl shadow-xl p-6 group-hover:scale-105 transition-all duration-300">
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                      <MousePointer className="h-6 w-6 text-white" />
                    </div>
                    <BarChart3 className="h-5 w-5 text-green-500" />
                  </div>
                  <div className="text-3xl font-bold text-gray-900 mb-1">{usageStats.total_clicks}</div>
                  <div className="text-gray-600 font-medium">Total Clicks</div>
                  <div className="text-xs text-gray-500 mt-2">All time</div>
                </div>
              </div>

              {/* Custom Codes Used Card */}
              <div className="group relative">
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-500"></div>
                <div className="relative backdrop-blur-xl bg-white/70 border border-white/20 rounded-2xl shadow-xl p-6 group-hover:scale-105 transition-all duration-300">
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                      <Code className="h-6 w-6 text-white" />
                    </div>
                    <Zap className="h-5 w-5 text-purple-500" />
                  </div>
                  <div className="text-3xl font-bold text-gray-900 mb-1">{usageStats.custom_code_links}</div>
                  <div className="text-gray-600 font-medium">Custom Codes</div>
                  <div className="text-xs text-gray-500 mt-2">This month</div>
                </div>
              </div>

              {/* Remaining Codes Card */}
              <div className="group relative">
                <div className="absolute inset-0 bg-gradient-to-r from-orange-500/10 to-red-500/10 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-500"></div>
                <div className="relative backdrop-blur-xl bg-white/70 border border-white/20 rounded-2xl shadow-xl p-6 group-hover:scale-105 transition-all duration-300">
                  <div className="flex items-center justify-between mb-4">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-orange-500 to-red-600 shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                      <Calendar className="h-6 w-6 text-white" />
                    </div>
                    <Clock className="h-5 w-5 text-orange-500" />
                  </div>
                  <div className="text-3xl font-bold text-gray-900 mb-1">{profile.custom_codes_remaining}</div>
                  <div className="text-gray-600 font-medium">Codes Left</div>
                  <div className="text-xs text-gray-500 mt-2">This month</div>
                </div>
              </div>
            </div>

            {/* Usage Progress Section */}
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 rounded-3xl blur-xl"></div>
              <div className="relative backdrop-blur-xl bg-white/70 border border-white/20 rounded-3xl shadow-2xl p-8">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
                      <BarChart3 className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">Custom Code Usage</h2>
                      <p className="text-gray-600">Track your monthly custom code consumption</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-gray-900">
                      {profile.custom_codes_used}<span className="text-lg text-gray-500">/{profile.custom_codes_used + profile.custom_codes_remaining}</span>
                    </div>
                    <div className="text-sm text-gray-500">codes used</div>
                  </div>
                </div>
                
                {/* Progress Bar */}
                <div className="relative mb-6">
                  <div className="w-full bg-gray-200 rounded-full h-4 shadow-inner">
                    <div
                      className={`h-4 rounded-full transition-all duration-1000 ease-out shadow-lg ${
                        getUsagePercentage() >= 90 
                          ? 'bg-gradient-to-r from-red-500 to-red-600'
                          : getUsagePercentage() >= 80
                          ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                          : 'bg-gradient-to-r from-blue-500 to-purple-600'
                      }`}
                      style={{ width: `${getUsagePercentage()}%` }}
                    >
                      <div className="h-full w-full bg-white/20 rounded-full animate-pulse"></div>
                    </div>
                  </div>
                  <div className="absolute -top-8 right-0 text-sm font-medium text-gray-700">
                    {Math.round(getUsagePercentage())}%
                  </div>
                </div>
                
                {/* Usage Details */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white/50 rounded-xl p-4 border border-white/30">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span className="text-sm font-medium text-gray-700">Used</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{profile.custom_codes_used}</div>
                  </div>
                  
                  <div className="bg-white/50 rounded-xl p-4 border border-white/30">
                    <div className="flex items-center gap-2 mb-2">
                      <Clock className="h-4 w-4 text-blue-500" />
                      <span className="text-sm font-medium text-gray-700">Remaining</span>
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{profile.custom_codes_remaining}</div>
                  </div>
                  
                  <div className="bg-white/50 rounded-xl p-4 border border-white/30">
                    <div className="flex items-center gap-2 mb-2">
                      <Calendar className="h-4 w-4 text-purple-500" />
                      <span className="text-sm font-medium text-gray-700">Resets</span>
                    </div>
                    <div className="text-sm font-bold text-gray-900">{formatResetDate(profile.custom_codes_reset_date)}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Upgrade Prompt */}
            {shouldShowUpgradePrompt() && (
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 via-pink-500/20 to-purple-500/20 rounded-3xl blur-xl animate-pulse"></div>
                <div className="relative backdrop-blur-xl bg-gradient-to-r from-purple-500/10 via-pink-500/10 to-purple-500/10 border border-purple-500/30 rounded-3xl shadow-2xl p-8">
                  <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 shadow-lg animate-bounce">
                          <Crown className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <h3 className="text-2xl font-bold text-gray-900 mb-1">
                            {profile.custom_codes_remaining === 0 ? 'Limit Reached!' : 'Almost There!'}
                          </h3>
                          <p className="text-gray-700">
                            {profile.custom_codes_remaining === 0 
                              ? 'Unlock 100 custom codes per month with our paid plan.'
                              : `Only ${profile.custom_codes_remaining} codes left. Upgrade for unlimited creativity!`
                            }
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex flex-wrap gap-2 text-sm text-gray-600">
                        <span className="flex items-center gap-1 bg-white/50 px-3 py-1 rounded-full">
                          <Zap className="h-3 w-3" />
                          100 codes/month
                        </span>
                        <span className="flex items-center gap-1 bg-white/50 px-3 py-1 rounded-full">
                          <Shield className="h-3 w-3" />
                          Priority support
                        </span>
                        <span className="flex items-center gap-1 bg-white/50 px-3 py-1 rounded-full">
                          <BarChart3 className="h-3 w-3" />
                          Advanced analytics
                        </span>
                      </div>
                    </div>
                    
                    <Button
                      onClick={handleUpgrade}
                      disabled={upgrading}
                      size="lg"
                      className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300"
                    >
                      {upgrading ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <>
                          <Crown className="h-5 w-5 mr-2" />
                          Upgrade Now
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            )}
        </>
      )}

          {/* Plan Comparison */}
          {planLimits && (
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 rounded-3xl blur-xl"></div>
              <div className="relative backdrop-blur-xl bg-white/70 border border-white/20 rounded-3xl shadow-2xl p-8">
                <div className="text-center mb-8">
                  <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-2">
                    Choose Your Plan
                  </h2>
                  <p className="text-gray-600">Select the perfect plan for your URL shortening needs</p>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Free Plan */}
                  <div className={`relative group ${
                    profile?.plan_type === 'free' ? 'ring-2 ring-blue-500' : ''
                  }`}>
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-2xl blur-lg group-hover:blur-xl transition-all duration-300"></div>
                    <div className="relative backdrop-blur-sm bg-white/60 border border-white/30 rounded-2xl p-6 group-hover:scale-105 transition-all duration-300">
                      <div className="flex justify-between items-start mb-6">
                        <div className="flex items-center gap-3">
                          <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 shadow-lg">
                            <Shield className="h-6 w-6 text-white" />
                          </div>
                          <div>
                            <h3 className="text-xl font-bold text-gray-900">Free Plan</h3>
                            <p className="text-gray-600">Perfect for getting started</p>
                          </div>
                        </div>
                        {profile?.plan_type === 'free' && (
                          <span className="px-3 py-1 bg-blue-500/20 text-blue-700 rounded-full text-sm font-medium">
                            Current Plan
                          </span>
                        )}
                      </div>
                      
                      <div className="mb-6">
                        <div className="text-4xl font-bold text-gray-900 mb-2">
                          {planLimits.plans.free.custom_codes}
                          <span className="text-lg text-gray-600 font-normal"> codes/month</span>
                        </div>
                        <div className="text-2xl font-bold text-green-600">Free</div>
                      </div>
                      
                      <ul className="space-y-3 mb-6">
                        {planLimits.plans.free.features.map((feature, index) => (
                          <li key={index} className="flex items-center gap-3">
                            <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                            <span className="text-gray-700">{feature}</span>
                          </li>
                        ))}
                      </ul>
                      
                      {profile?.plan_type !== 'free' && (
                        <Button 
                          variant="outline" 
                          className="w-full"
                          disabled
                        >
                          Current Plan
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Paid Plan */}
                  <div className={`relative group ${
                    profile?.plan_type === 'paid' ? 'ring-2 ring-purple-500' : ''
                  }`}>
                    <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-2xl blur-lg group-hover:blur-xl transition-all duration-300"></div>
                    <div className="relative backdrop-blur-sm bg-white/60 border border-purple-200/50 rounded-2xl p-6 group-hover:scale-105 transition-all duration-300">
                      <div className="flex justify-between items-start mb-6">
                        <div className="flex items-center gap-3">
                          <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 shadow-lg">
                            <Crown className="h-6 w-6 text-white" />
                          </div>
                          <div>
                            <h3 className="text-xl font-bold text-gray-900">Pro Plan</h3>
                            <p className="text-gray-600">For power users</p>
                          </div>
                        </div>
                        {profile?.plan_type === 'paid' ? (
                          <span className="px-3 py-1 bg-purple-500/20 text-purple-700 rounded-full text-sm font-medium">
                            Current Plan
                          </span>
                        ) : (
                          <span className="px-3 py-1 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full text-sm font-medium animate-pulse">
                            Popular
                          </span>
                        )}
                      </div>
                      
                      <div className="mb-6">
                        <div className="text-4xl font-bold text-gray-900 mb-2">
                          {planLimits.plans.paid.custom_codes}
                          <span className="text-lg text-gray-600 font-normal"> codes/month</span>
                        </div>
                        <div className="text-2xl font-bold text-purple-600">$9.99/month</div>
                      </div>
                      
                      <ul className="space-y-3 mb-6">
                        {planLimits.plans.paid.features.map((feature, index) => (
                          <li key={index} className="flex items-center gap-3">
                            <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
                            <span className="text-gray-700">{feature}</span>
                          </li>
                        ))}
                      </ul>
                      
                      {profile?.plan_type === 'paid' ? (
                        <Button 
                          variant="outline" 
                          className="w-full border-purple-200 text-purple-700"
                          disabled
                        >
                          Current Plan
                        </Button>
                      ) : (
                        <Button
                          onClick={handleUpgrade}
                          disabled={upgrading}
                          className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300"
                        >
                          {upgrading ? (
                            <LoadingSpinner size="sm" />
                          ) : (
                            <>
                              <Zap className="h-4 w-4 mr-2" />
                              Upgrade to Pro
                            </>
                          )}
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

        {/* Anonymous User Prompt */}
        {!user && (
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-cyan-500/10 rounded-3xl blur-xl"></div>
            <div className="relative backdrop-blur-xl bg-white/70 border border-white/20 rounded-3xl shadow-2xl p-12 text-center">
              <div className="max-w-2xl mx-auto">
                <div className="p-4 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg inline-block mb-6">
                  <Sparkles className="h-12 w-12 text-white" />
                </div>
                
                <h2 className="text-4xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-4">
                  Sign In to Access Your Dashboard
                </h2>
                
                <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                  Create an account to track your links, view detailed analytics, and unlock advanced features.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                  <div className="bg-white/50 rounded-xl p-4 border border-white/30">
                    <BarChart3 className="h-8 w-8 text-blue-500 mx-auto mb-3" />
                    <div className="font-semibold text-gray-900">Analytics</div>
                    <div className="text-sm text-gray-600">Track clicks and performance</div>
                  </div>
                  
                  <div className="bg-white/50 rounded-xl p-4 border border-white/30">
                    <Code className="h-8 w-8 text-purple-500 mx-auto mb-3" />
                    <div className="font-semibold text-gray-900">Custom Codes</div>
                    <div className="text-sm text-gray-600">Create memorable links</div>
                  </div>
                  
                  <div className="bg-white/50 rounded-xl p-4 border border-white/30">
                    <Shield className="h-8 w-8 text-green-500 mx-auto mb-3" />
                    <div className="font-semibold text-gray-900">Link Management</div>
                    <div className="text-sm text-gray-600">Organize and control your links</div>
                  </div>
                </div>
                
                <div className="text-gray-500">
                  You can still create links anonymously, but signing in unlocks the full experience.
                </div>
              </div>
            </div>
          </div>
        )}
    </div>
  );
}