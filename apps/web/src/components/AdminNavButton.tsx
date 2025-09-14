'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useAdminStatus } from '@/hooks/useAdminStatus';
import { Button } from './ui/Button';
import { Shield } from 'lucide-react';
import Link from 'next/link';

export function AdminNavButton() {
  const { user } = useAuth();
  const { isAdmin, isChecking } = useAdminStatus();

  // Don't show anything if user is not logged in or not admin
  if (!user || !isAdmin) {
    return null;
  }

  return (
    <Link href="/admin">
      <Button
        variant="outline"
        className="flex items-center gap-2 bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100"
        disabled={isChecking}
      >
        <Shield className="w-4 h-4" />
        Admin Panel
      </Button>
    </Link>
  );
}