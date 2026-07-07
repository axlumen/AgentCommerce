/**
 * 购物车状态管理
 */

import { create } from 'zustand';
import { api, type CartItem, type AddCartData } from '@/lib/api';
import { toast } from 'sonner';

interface CartState {
  items: CartItem[];
  isLoading: boolean;
  totalAmount: number;
  totalItems: number;

  fetchCart: () => Promise<void>;
  addItem: (data: AddCartData) => Promise<void>;
  updateQuantity: (productId: number, quantity: number) => Promise<void>;
  removeItem: (productId: number) => Promise<void>;
  clearCart: () => Promise<void>;
  calculateTotals: () => void;
}

export const useCartStore = create<CartState>()((set, get) => ({
  items: [],
  isLoading: false,
  totalAmount: 0,
  totalItems: 0,

  fetchCart: async () => {
    set({ isLoading: true });
    try {
      const items = await api.cart.list();
      set({ items, isLoading: false });
      get().calculateTotals();
    } catch {
      set({ isLoading: false });
    }
  },

  addItem: async (data) => {
    try {
      await api.cart.add(data);
      toast.success('已添加到购物车');
      await get().fetchCart();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '添加失败');
      throw error;
    }
  },

  updateQuantity: async (productId, quantity) => {
    try {
      await api.cart.update(productId, quantity);
      await get().fetchCart();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '更新失败');
    }
  },

  removeItem: async (productId) => {
    try {
      await api.cart.remove(productId);
      toast.success('已移除');
      await get().fetchCart();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '移除失败');
    }
  },

  clearCart: async () => {
    try {
      await api.cart.clear();
      set({ items: [], totalAmount: 0, totalItems: 0 });
      toast.success('购物车已清空');
    } catch (error) {
      toast.error('清空失败');
    }
  },

  calculateTotals: () => {
    const { items } = get();
    const totalAmount = items.reduce(
      (sum, item) => sum + item.product_price * item.quantity,
      0
    );
    const totalItems = items.reduce((sum, item) => sum + item.quantity, 0);
    set({ totalAmount, totalItems });
  },
}));
