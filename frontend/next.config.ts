import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // 允许跨域访问开发资源（Next.js 16+）
  allowedDevOrigins: ['127.0.0.1'],

  // Docker 构建使用 standalone 模式
  output: 'standalone',

  // API 代理（开发环境）
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/docs',
        destination: 'http://localhost:8000/docs',
      },
      {
        source: '/openapi.json',
        destination: 'http://localhost:8000/openapi.json',
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
