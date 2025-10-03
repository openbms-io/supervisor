import type { NextConfig } from 'next'
import path from 'path'

// Use relative path to workspace root to avoid hardcoded machine-specific paths
// This ensures the config works across all machines and CI environments
const nextConfig: NextConfig = {
  turbopack: {
    root: path.join(__dirname, '../..'),
  },
  webpack: (config, { isServer, webpack }) => {
    // Only add Buffer polyfill for client-side bundles
    // Server-side uses native Node.js Buffer
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        buffer: require.resolve('buffer/'),
      }

      config.plugins.push(
        new webpack.ProvidePlugin({
          Buffer: ['buffer', 'Buffer'],
        })
      )
    }

    return config
  },
}

export default nextConfig
