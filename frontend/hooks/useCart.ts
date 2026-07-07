/**
 * 购物车相关 Hooks
 */

'use client';

import { useEffect } from 'react';
import { useCartStore } from '@/store/cart';
import { useAuthStore } from '@/store/auth';

/**
 * 购物车 Hook
 */
export function useCart() {
  const cart = useCartStore();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      cart.fetchCart();
    }
  }, [isAuthenticated]);

  return cart;
}
