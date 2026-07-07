/**
 * TanStack Query 配置
 *
 * SSR 安全：server 端每次创建新实例避免请求间状态泄漏，
 * client 端保持单例。
 */

import { QueryClient } from '@tanstack/react-query';

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 分钟
        gcTime: 5 * 60 * 1000, // 5 分钟
        retry: 1,
        refetchOnWindowFocus: false,
      },
    },
  });
}

let browserQueryClient: QueryClient | null = null;

export function getQueryClient() {
  if (typeof window === 'undefined') {
    // Server: 每次创建新实例
    return makeQueryClient();
  }
  // Browser: 单例
  if (!browserQueryClient) {
    browserQueryClient = makeQueryClient();
  }
  return browserQueryClient;
}
