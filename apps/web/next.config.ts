import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Output configuration for static export
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  
  // Turbopack configuration
  turbopack: {
    root: path.resolve(__dirname, '../../')
  },
  
  experimental: {
    externalDir: true,
  },
  
  // Production optimizations
  compress: true,
  poweredByHeader: false,
  generateEtags: true,
  
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
      {
        source: '/static/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },
  
  // Environment variable validation
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_FIREBASE_PROJECT_ID: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  },
  
  eslint: {
    // Only ignore during builds in development
    ignoreDuringBuilds: process.env.NODE_ENV !== 'production',
  },
  
  typescript: {
    // Only ignore build errors in development
    ignoreBuildErrors: process.env.NODE_ENV !== 'production',
  },
  
  webpack: (config, { isServer, dev }) => {
    // Handle shared package imports
    config.resolve.alias = {
      ...config.resolve.alias,
      '@shared': path.resolve(__dirname, '../../packages/shared/src'),
    };
    
    // Production optimizations
    if (!dev) {
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendors',
              chunks: 'all',
            },
          },
        },
      };
    }
    
    return config;
  },
};

export default nextConfig;
