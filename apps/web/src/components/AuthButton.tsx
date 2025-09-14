'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Toast } from '@/components/ui/Toast';
import { ChevronDown, User, LogOut, Settings } from 'lucide-react';

interface AuthButtonProps {
  className?: string;
  showProfile?: boolean;
}

export function AuthButton({ className = '', showProfile = false }: AuthButtonProps) {
  const { user, loading, signInWithGoogle, signOut } = useAuth();
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, right: 0 });
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [isClient, setIsClient] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Ensure we're on the client side to prevent hydration mismatches
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleSignIn = async () => {
    setIsSigningIn(true);
    try {
      await signInWithGoogle();
      setToast({ message: 'Successfully signed in!', type: 'success' });
    } catch (error) {
      console.error('Sign in error:', error);
      setToast({ message: 'Failed to sign in. Please try again.', type: 'error' });
    } finally {
      setIsSigningIn(false);
    }
  };

  const handleSignOut = async () => {
    setIsSigningOut(true);
    setShowDropdown(false);
    try {
      await signOut();
      setToast({ message: 'Successfully signed out!', type: 'success' });
    } catch (error) {
      console.error('Sign out error:', error);
      setToast({ message: 'Failed to sign out. Please try again.', type: 'error' });
    } finally {
      setIsSigningOut(false);
    }
  };

  const toggleDropdown = () => {
    if (!showDropdown && buttonRef.current && typeof window !== 'undefined') {
      const rect = buttonRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + 8,
        right: window.innerWidth - rect.right,
      });
    }
    setShowDropdown(!showDropdown);
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const handleImageError = () => {
    setImageError(true);
  };

  // Reset all state when user changes
  useEffect(() => {
    setImageError(false);
    setShowDropdown(false);
    setIsSigningIn(false);
    setIsSigningOut(false);
  }, [user]);

  // Debug logging
  useEffect(() => {
    console.log('AuthButton: user state changed', { user: !!user, loading });
  }, [user, loading]);

  if (loading) {
    return (
      <div className={`flex items-center ${className}`}>
        <LoadingSpinner size="sm" />
      </div>
    );
  }

  return (
    <>
      {toast && (
        <Toast
          id="auth-toast"
          title={toast.type === 'success' ? 'Success' : 'Error'}
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
      
      <div className={`flex items-center ${className}`} key={user?.uid || 'anonymous'}>
        {user ? (
          <div className="relative" ref={dropdownRef}>
            {/* User Avatar Button */}
            <button
              ref={buttonRef}
              onClick={toggleDropdown}
              className="flex items-center gap-2 p-2 rounded-xl bg-white/10 backdrop-blur-md border border-white/20 hover:bg-white/20 transition-all duration-200 group"
              title={`${user.displayName || 'User'} (${user.email})`}
            >
              {/* Avatar */}
              <div className="relative">
                {user.photoURL && !imageError ? (
                  <img
                    src={user.photoURL}
                    alt={user.displayName || 'User'}
                    className="w-8 h-8 rounded-full border border-white/30 object-cover"
                    onError={handleImageError}
                    crossOrigin="anonymous"
                  />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-medium">
                    {getInitials(user.displayName || user.email || 'U')}
                  </div>
                )}
                {/* Online indicator */}
                <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>
              </div>

              {/* User info (only show if showProfile is true) */}
              {showProfile && (
                <div className="text-left">
                  <div className="text-white font-medium text-sm">
                    {user.displayName || 'User'}
                  </div>
                  <div className="text-gray-300 text-xs">
                    {user.email}
                  </div>
                </div>
              )}

              {/* Dropdown arrow */}
              <ChevronDown 
                className={`w-4 h-4 text-gray-300 transition-transform duration-200 ${
                  showDropdown ? 'rotate-180' : ''
                }`} 
              />
            </button>

            {/* Dropdown Menu */}
            {showDropdown && isClient && (
              <div 
                className="fixed w-64 bg-white/95 backdrop-blur-md rounded-xl shadow-2xl border border-white/20 py-2 dropdown-menu"
                style={{
                  top: `${dropdownPosition.top}px`,
                  right: `${dropdownPosition.right}px`,
                  zIndex: 9999
                }}
              >
                {/* User Info Header */}
                <div className="px-4 py-3 border-b border-gray-200/50">
                  <div className="flex items-center gap-3">
                    {user.photoURL && !imageError ? (
                      <img
                        src={user.photoURL}
                        alt={user.displayName || 'User'}
                        className="w-10 h-10 rounded-full object-cover"
                        onError={handleImageError}
                        crossOrigin="anonymous"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium">
                        {getInitials(user.displayName || user.email || 'U')}
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="text-gray-900 font-medium truncate">
                        {user.displayName || 'User'}
                      </div>
                      <div className="text-gray-600 text-sm truncate">
                        {user.email}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Menu Items */}
                <div className="py-1">
                  <button
                    onClick={() => {
                      setShowDropdown(false);
                      if (typeof window !== 'undefined') {
                        window.location.href = '/dashboard';
                      }
                    }}
                    className="w-full flex items-center gap-3 px-4 py-2 text-left text-gray-700 hover:bg-gray-100/50 transition-colors duration-150"
                  >
                    <User className="w-4 h-4" />
                    <span>Dashboard</span>
                  </button>
                  <button
                    onClick={handleSignOut}
                    disabled={isSigningOut}
                    className="w-full flex items-center gap-3 px-4 py-2 text-left text-gray-700 hover:bg-gray-100/50 transition-colors duration-150 disabled:opacity-50"
                  >
                    {isSigningOut ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <LogOut className="w-4 h-4" />
                    )}
                    <span>{isSigningOut ? 'Signing out...' : 'Sign out'}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <Button
            onClick={handleSignIn}
            disabled={isSigningIn}
            variant="secondary"
            className="bg-white text-gray-900 hover:bg-gray-100 font-medium shadow-lg min-w-[180px]"
          >
            {isSigningIn ? (
              <LoadingSpinner size="sm" />
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="currentColor"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Sign in with Google
              </>
            )}
          </Button>
        )}
      </div>
    </>
  );
}