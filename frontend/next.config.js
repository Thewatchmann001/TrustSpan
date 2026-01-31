/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ["localhost"],
  },
  webpack: (config, { isServer }) => {
    // Fix for @solana/buffer-layout-utils nested dependency issue
    // It tries to import from a nested path that doesn't exist
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
    };

    // Add a module rule to handle the missing nested import
    config.resolve.modules = [
      ...(config.resolve.modules || []),
      "node_modules",
    ];

    // Ensure all @solana/web3.js imports resolve to the top-level package
    if (!config.resolve.alias["@solana/web3.js"]) {
      config.resolve.alias["@solana/web3.js"] = require.resolve("@solana/web3.js");
    }

    return config;
  },
  // PWA Configuration
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-XSS-Protection",
            value: "1; mode=block",
          },
        ],
      },
      {
        source: "/sw.js",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=0, must-revalidate",
          },
          {
            key: "Service-Worker-Allowed",
            value: "/",
          },
        ],
      },
      {
        source: "/manifest.json",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=3600",
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
