'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation'; // Import useRouter
import { Menu, Home, BarChart3, User, Settings, Link as LinkIcon } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useAdminStatus } from '@/hooks/useAdminStatus';

interface NavigationProps {
  currentPage?: 'home' | 'dashboard' | 'analytics' | 'profile' | 'admin';
  onNavigate?: (page: string) => void;
}

export function Navigation({ currentPage = 'home', onNavigate }: NavigationProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { user } = useAuth();
  const { isAdmin } = useAdminStatus();
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter(); // Initialize useRouter

  // Handle hydration
  useEffect(() => {
    setMounted(true);
  }, []);

  const menuItems = [
    {
      id: 'home',
      label: 'Home',
      icon: Home,
      description: 'Create new short links'
    },
    ...(mounted && user ? [
      {
        id: 'dashboard',
        label: 'My Links',
        icon: LinkIcon,
        description: 'View and manage your links'
      },
      {
        id: 'profile',
        label: 'Profile',
        icon: User,
        description: 'Account settings and usage'
      }
    ] : []),
    ...(mounted && isAdmin ? [
      {
        id: 'admin',
        label: 'Admin',
        icon: Settings,
        description: 'System administration'
      }
    ] : [])
  ];

  const handleNavigate = (pageId: string) => {
    try {
      console.log('Navigating to:', pageId);
      setIsOpen(false);
      
      if (onNavigate) {
        onNavigate(pageId);
      } else {
        // Default navigation behavior using Next.js router
        switch (pageId) {
          case 'home':
            router.push('/');
            break;
          case 'dashboard':
            router.push('/dashboard');
            break;
          case 'profile':
            router.push('/profile');
            break;
          case 'admin':
            router.push('/admin');
            break;
          default:
            console.warn('Unknown page:', pageId);
        }
      }
    } catch (error) {
      console.error('Navigation error:', error);
    }
  };

  // Close dropdown when clicking outside - only on client side
  useEffect(() => {
    if (typeof document === 'undefined') return;
    
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Hamburger Menu Button - Integrated into header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-2 rounded-lg hover:bg-white/10 transition-colors text-white"
        aria-label="Navigation menu"
      >
        <Menu className="h-5 w-5" />
        <span className="hidden sm:inline text-sm font-medium">Menu</span>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
          <div className="px-3 py-2 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900 text-sm">Navigation</h3>
          </div>
          
          <div className="py-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavigate(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                    isActive 
                      ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-500' 
                      : 'hover:bg-gray-50 text-gray-700'
                  }`}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{item.label}</div>
                    <div className="text-xs text-gray-500 truncate">{item.description}</div>
                  </div>
                </button>
              );
            })}
          </div>
          
          {mounted && !user && (
            <div className="px-4 py-3 border-t border-gray-100">
              <p className="text-xs text-gray-500">Sign in to access Dashboard and Profile</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
