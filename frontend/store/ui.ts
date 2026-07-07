/**
 * UI 状态管理
 *
 * Theme 仅存储状态，DOM 操作由 Providers.tsx 的 useEffect 处理。
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Theme = 'light' | 'dark' | 'system';

interface UIState {
  theme: Theme;
  sidebarOpen: boolean;
  chatOpen: boolean;

  setTheme: (theme: Theme) => void;
  toggleSidebar: () => void;
  toggleChat: () => void;
  setChatOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'light',
      sidebarOpen: false,
      chatOpen: false,

      setTheme: (theme) => set({ theme }),

      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      toggleChat: () => set((state) => ({ chatOpen: !state.chatOpen })),

      setChatOpen: (open) => set({ chatOpen: open }),
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({ theme: state.theme }),
    }
  )
);

/**
 * 计算是否应使用暗色模式
 */
export function resolveDarkMode(theme: Theme): boolean {
  if (theme === 'system') {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  }
  return theme === 'dark';
}
