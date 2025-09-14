'use client';

import React, { useState } from 'react';
import { type CreateLinkResponse } from '@shared/types/link';
import { Button } from './ui/Button';
import { copyToClipboard, formatDateTime } from '@/lib/utils';
import { 
  Copy, 
  Check, 
  QrCode, 
  ExternalLink, 
  BarChart3, 
  Calendar,
  Lock,
  Eye,
  EyeOff
} from 'lucide-react';

interface LinkDisplayProps {
  link: CreateLinkResponse;
  showAnalytics?: boolean;
  onViewAnalytics?: (code: string) => void;
}

export function LinkDisplay({ link, showAnalytics = true, onViewAnalytics }: LinkDisplayProps) {
  const [copied, setCopied] = useState(false);
  const [showQR, setShowQR] = useState(false);
  const [qrLoading, setQrLoading] = useState(false);

  const handleCopy = async () => {
    try {
      await copyToClipboard(link.short_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const handleQRToggle = () => {
    if (!showQR) {
      setQrLoading(true);
      // QR will load via img onLoad
    }
    setShowQR(!showQR);
  };

  const handleQRLoad = () => {
    setQrLoading(false);
  };

  const handleQRError = () => {
    setQrLoading(false);
    console.error('Failed to load QR code');
  };

  return (
    <div className="w-full max-w-3xl mx-auto relative">
      {/* Glassmorphic background effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-green-500/10 via-blue-500/10 to-purple-500/10 rounded-3xl blur-xl"></div>
      
      <div className="relative backdrop-blur-xl bg-white/70 border border-white/20 rounded-3xl shadow-2xl p-8 md:p-10">
        <div className="mb-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl shadow-lg mb-4">
            <Check className="h-8 w-8 text-white" />
          </div>
          <h3 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent mb-3">
            Your Short Link is Ready!
          </h3>
          <p className="text-gray-600 text-lg">
            Share your new short link or view its analytics
          </p>
        </div>

        {/* Short URL Display */}
        <div className="mb-8">
          <label className="block text-sm font-semibold text-gray-800 mb-3">
            Short URL
          </label>
          <div className="flex items-center space-x-3">
            <div className="flex-1 p-4 backdrop-blur-sm bg-gradient-to-r from-blue-50/50 to-purple-50/50 border border-white/30 rounded-2xl shadow-lg">
              <a
                href={link.short_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 font-mono text-lg break-all transition-colors duration-200"
              >
                {link.short_url}
              </a>
            </div>
            <Button
              variant="outline"
              size="md"
              onClick={handleCopy}
              className="flex-shrink-0 px-6"
              aria-label={copied ? 'Copied!' : 'Copy to clipboard'}
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Original URL */}
        <div className="mb-8">
          <label className="block text-sm font-semibold text-gray-800 mb-3">
            Original URL
          </label>
          <div className="p-4 backdrop-blur-sm bg-white/40 border border-white/30 rounded-2xl shadow-lg">
            <a
              href={link.long_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-700 hover:text-blue-600 break-all flex items-center transition-colors duration-200"
            >
              <span className="flex-1">{link.long_url}</span>
              <ExternalLink className="h-4 w-4 ml-2 flex-shrink-0" />
            </a>
          </div>
        </div>

        {/* Link Details */}
        <div className="mb-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 backdrop-blur-sm bg-white/40 border border-white/30 rounded-2xl shadow-lg">
            <label className="block text-sm font-semibold text-gray-800 mb-2">
              Domain
            </label>
            <p className="text-gray-900 font-mono text-lg">{link.base_domain}</p>
          </div>
          <div className="p-4 backdrop-blur-sm bg-white/40 border border-white/30 rounded-2xl shadow-lg">
            <label className="block text-sm font-semibold text-gray-800 mb-2">
              Code
            </label>
            <p className="text-gray-900 font-mono text-lg">{link.code}</p>
          </div>
          {link.expires_at && (
            <div className="md:col-span-2 p-4 backdrop-blur-sm bg-gradient-to-r from-amber-50/50 to-orange-50/50 border border-white/30 rounded-2xl shadow-lg">
              <label className="block text-sm font-semibold text-gray-800 mb-2 flex items-center">
                <Calendar className="h-4 w-4 mr-2" />
                Expires
              </label>
              <p className="text-gray-900 text-lg">
                {formatDateTime(new Date(link.expires_at))}
              </p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap justify-center gap-4">
          {/* QR Code Toggle */}
          <Button
            variant="outline"
            onClick={handleQRToggle}
            loading={qrLoading}
            size="lg"
          >
            <QrCode className="h-5 w-5 mr-2" />
            {showQR ? 'Hide QR Code' : 'Show QR Code'}
          </Button>

          {/* Analytics Button */}
          {showAnalytics && (
            <Button
              variant="outline"
              onClick={() => onViewAnalytics?.(link.code)}
              size="lg"
            >
              <BarChart3 className="h-5 w-5 mr-2" />
              View Analytics
            </Button>
          )}

          {/* Visit Link */}
          <Button
            variant="secondary"
            onClick={() => window.open(link.short_url, '_blank')}
            size="lg"
          >
            <ExternalLink className="h-5 w-5 mr-2" />
            Visit Link
          </Button>
        </div>

        {/* QR Code Display */}
        {showQR && (
          <div className="mt-8 p-6 backdrop-blur-sm bg-white/40 border border-white/30 rounded-2xl shadow-lg">
            <div className="text-center">
              <h4 className="text-lg font-semibold text-gray-800 mb-4">
                QR Code
              </h4>
              <div className="inline-block p-6 bg-white rounded-2xl shadow-xl">
                {qrLoading && (
                  <div className="w-48 h-48 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                )}
                <img
                  src={link.qr_url}
                  alt={`QR code for ${link.short_url}`}
                  className={`w-48 h-48 ${qrLoading ? 'hidden' : 'block'}`}
                  onLoad={handleQRLoad}
                  onError={handleQRError}
                />
              </div>
              <p className="text-sm text-gray-600 mt-4">
                Scan with your phone to open the link
              </p>
            </div>
          </div>
        )}

        {/* Success Message */}
        <div className="mt-8 p-6 backdrop-blur-sm bg-gradient-to-r from-green-50/60 to-emerald-50/60 border border-green-200/50 rounded-2xl shadow-lg">
          <div className="flex items-center">
            <div className="p-2 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl shadow-lg mr-4">
              <Check className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="text-lg font-semibold text-green-800">
                Link created successfully!
              </p>
              <p className="text-green-700">
                Your short link is ready to share. Click analytics to track its performance.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}