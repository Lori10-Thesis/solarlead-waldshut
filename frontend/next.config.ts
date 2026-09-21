import type { NextConfig } from 'next';

const backendInternal = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';

const nextConfig: NextConfig = {
  output: 'standalone',
  poweredByHeader: false,
  async rewrites() {
    // Same-origin API proxy for local/public previews. In production Caddy normally
    // handles these routes before they reach Next.js, but this remains a safe fallback.
    return [
      { source: '/api/:path*', destination: `${backendInternal}/api/:path*` },
      { source: '/health', destination: `${backendInternal}/health` },
      { source: '/ready', destination: `${backendInternal}/ready` },
    ];
  },
};
export default nextConfig;
