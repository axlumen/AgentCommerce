/**
 * API 封装层
 *
 * 统一处理请求、认证、错误。
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiResponse<T> {
  data: T;
  error?: string;
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token =
    typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(response.status, error.detail || `API Error: ${response.status}`);
  }

  return response.json();
}

// ============================================================
// 类型定义
// ============================================================

export interface LoginData {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  phone?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  phone?: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface Product {
  id: number;
  name: string;
  description?: string;
  price: number;
  stock: number;
  category_id?: number;
  brand?: string;
  specs?: Record<string, unknown>;
  image_url?: string;
  sales_count: number;
  is_on_sale: boolean;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ProductParams {
  page?: number;
  size?: number;
  sort_by?: string;
  sort_order?: string;
  keyword?: string;
  category_id?: number;
  brand?: string;
  min_price?: number;
  max_price?: number;
}

export interface CartItem {
  product_id: number;
  product_name: string;
  product_price: number;
  product_image?: string;
  quantity: number;
}

export interface AddCartData {
  product_id: number;
  quantity: number;
}

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  product_price: number;
  product_image?: string;
  quantity: number;
  subtotal: number;
}

export interface Order {
  id: number;
  status: 'pending' | 'paid' | 'shipped' | 'completed' | 'cancelled';
  total_amount: number;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

export interface CreateOrderData {
  items: Array<{
    product_id: number;
    quantity: number;
  }>;
  address: string;
  phone: string;
  receiver_name: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  reply: string;
  session_id: string;
  tool_calls: Array<{
    tool: string;
    args: Record<string, unknown>;
    result?: unknown;
  }>;
  needs_confirm: boolean;
  confirm_action?: string;
  confirm_args?: Record<string, unknown>;
  confirm_message?: string;
}

export interface ConfirmRequest {
  session_id: string;
  approved: boolean;
  thread_id?: string;
}

// ============================================================
// API 方法
// ============================================================

export const api = {
  // 认证
  auth: {
    login: (data: LoginData) =>
      fetchApi<TokenResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    register: (data: RegisterData) =>
      fetchApi<User>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    me: () => fetchApi<User>('/api/auth/me'),
  },

  // 商品
  products: {
    list: (params?: ProductParams) => {
      const searchParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            searchParams.set(key, String(value));
          }
        });
      }
      return fetchApi<PaginatedResponse<Product>>(
        `/api/products?${searchParams.toString()}`
      );
    },
    detail: (id: number) => fetchApi<Product>(`/api/products/${id}`),
  },

  // 购物车
  cart: {
    list: () => fetchApi<CartItem[]>('/api/cart'),
    add: (data: AddCartData) =>
      fetchApi<CartItem>('/api/cart', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (productId: number, quantity: number) =>
      fetchApi<CartItem>(`/api/cart/${productId}`, {
        method: 'PUT',
        body: JSON.stringify({ quantity }),
      }),
    remove: (productId: number) =>
      fetchApi<void>(`/api/cart/${productId}`, { method: 'DELETE' }),
    clear: () => fetchApi<void>('/api/cart', { method: 'DELETE' }),
  },

  // 订单
  orders: {
    list: () => fetchApi<Order[]>('/api/orders'),
    create: (data: CreateOrderData) =>
      fetchApi<Order>('/api/orders', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    detail: (id: number) => fetchApi<Order>(`/api/orders/${id}`),
    pay: (id: number) =>
      fetchApi<Order>(`/api/orders/${id}/pay`, { method: 'PUT' }),
    cancel: (id: number) =>
      fetchApi<Order>(`/api/orders/${id}/cancel`, { method: 'PUT' }),
    confirm: (id: number) =>
      fetchApi<Order>(`/api/orders/${id}/confirm`, { method: 'PUT' }),
  },

  // Agent
  agent: {
    chat: (data: ChatRequest) =>
      fetchApi<ChatResponse>('/api/agent/chat', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    confirm: (data: ConfirmRequest) =>
      fetchApi<ChatResponse>('/api/agent/confirm', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    history: (sessionId: string) =>
      fetchApi<{ session_id: string; messages: Array<{ role: string; content: string }>; count: number }>(
        `/api/agent/history/${sessionId}`
      ),
    clearHistory: (sessionId: string) =>
      fetchApi<void>(`/api/agent/history/${sessionId}`, { method: 'DELETE' }),
    preferences: () =>
      fetchApi<{ user_id: number; preferences: Record<string, unknown> }>(
        '/api/agent/preferences'
      ),
    stats: () =>
      fetchApi<{
        ai_stats: Record<string, unknown>;
        cache: Record<string, unknown>;
        circuit_breaker: Record<string, unknown>;
      }>('/api/agent/stats'),
  },
};

export { ApiError };
