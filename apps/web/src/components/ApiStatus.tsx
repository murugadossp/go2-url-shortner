'use client';

import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Loader } from 'lucide-react';

export function ApiStatus() {
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [details, setDetails] = useState<string>('');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    
    const checkApiStatus = async () => {
      try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        const response = await fetch(`${apiBaseUrl}/health`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          setStatus('online');
          setDetails(`API is running (${data.status})`);
        } else {
          setStatus('offline');
          setDetails(`API returned ${response.status}: ${response.statusText}`);
        }
      } catch (error) {
        setStatus('offline');
        setDetails(`Cannot connect to API: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    };

    checkApiStatus();
    
    // Check every 30 seconds
    const interval = setInterval(checkApiStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  // Don't render anything until mounted to avoid hydration mismatch
  if (!mounted) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-md border border-blue-200 bg-blue-50 text-sm">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        <span className="font-medium">API Status: Checking...</span>
      </div>
    );
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'checking':
        return <Loader className="h-4 w-4 animate-spin text-blue-500" />;
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'offline':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'checking':
        return 'border-blue-200 bg-blue-50';
      case 'online':
        return 'border-green-200 bg-green-50';
      case 'offline':
        return 'border-red-200 bg-red-50';
    }
  };

  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-md border text-sm ${getStatusColor()}`}>
      {getStatusIcon()}
      <span className="font-medium">
        API Status: {status === 'checking' ? 'Checking...' : status === 'online' ? 'Online' : 'Offline'}
      </span>
      {details && (
        <span className="text-xs opacity-75">
          - {details}
        </span>
      )}
    </div>
  );
}