/**
 * 认证相关 Hooks
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';

/**
 * 认证 Hook
 */
export function useAuth() {
  const store = useAuthStore();

  useEffect(() => {
    // 首次加载时获取用户信息
    if (store.token && !store.user) {
      useAuthStore.getState().fetchUser();
    }
  }, [store.token, store.user]);

  return store;
}

/**
 * 需要登录的 Hook
 */
export function useRequireAuth() {
  const auth = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!auth.isLoading && !auth.isAuthenticated) {
      router.push('/login');
    }
  }, [auth.isLoading, auth.isAuthenticated]);

  return auth;
}
