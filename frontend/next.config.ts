import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // API 代理（开发环境）
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },

  // 图片域名白名单
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
      },
    ],
  },

  // 输出模式（可选，用于 FastAPI 托管）
  // output: 'export',
};

export default nextConfig;
