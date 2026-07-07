/**
 * 全局 Provider 组件
 */

'use client';

import { useEffect } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { getQueryClient } from '@/lib/query-client';
import { ChatWidget } from '@/components/chat/ChatWidget';
import { Toaster } from '@/components/ui/sonner';
import { useUIStore, resolveDarkMode, type Theme } from '@/store/ui';


function applyTheme(theme: Theme) {
  const isDark = resolveDarkMode(theme);
  document.documentElement.classList.toggle('dark', isDark);
}


export function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient();
  const theme = useUIStore((s) => s.theme);

  // 同步主题到 DOM，响应 system 主题变化
  useEffect(() => {
    applyTheme(theme);

    if (theme === 'system') {
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      const handler = () => applyTheme('system');
      mq.addEventListener('change', handler);
      return () => mq.removeEventListener('change', handler);
    }
  }, [theme]);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ChatWidget />
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  );
}
