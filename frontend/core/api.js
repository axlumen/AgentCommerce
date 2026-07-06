/**
 * API 层
 *
 * 统一封装 HTTP 请求，处理认证、错误、loading。
 */

import { store } from './store.js';

const BASE_URL = '/api';

class Api {
  constructor() {
    this.interceptors = [];
  }

  /**
   * 添加拦截器
   */
  use(interceptor) {
    this.interceptors.push(interceptor);
  }

  /**
   * 发送请求
   */
  async request(method, path, data = null, options = {}) {
    const url = `${BASE_URL}${path}`;
    const token = store.get('token');

    const config = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    };

    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      config.body = JSON.stringify(data);
    }

    // 执行拦截器
    for (const interceptor of this.interceptors) {
      if (interceptor.request) {
        await interceptor.request(config);
      }
    }

    try {
      const response = await fetch(url, config);
      const json = await response.json();

      // 处理错误响应
      if (!response.ok) {
        const error = new Error(json.detail || json.message || '请求失败');
        error.status = response.status;
        error.data = json;

        // 401 未授权，自动登出
        if (response.status === 401) {
          store.logout();
          window.dispatchEvent(new CustomEvent('auth:expired'));
        }

        throw error;
      }

      // 执行响应拦截器
      for (const interceptor of this.interceptors) {
        if (interceptor.response) {
          await interceptor.response(json);
        }
      }

      return json;
    } catch (error) {
      // 网络错误
      if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
        error.message = '网络连接失败，请检查网络';
      }
      throw error;
    }
  }

  /**
   * GET 请求
   */
  get(path, params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `${path}?${query}` : path;
    return this.request('GET', url);
  }

  /**
   * POST 请求
   */
  post(path, data) {
    return this.request('POST', path, data);
  }

  /**
   * PUT 请求
   */
  put(path, data) {
    return this.request('PUT', path, data);
  }

  /**
   * DELETE 请求
   */
  delete(path) {
    return this.request('DELETE', path);
  }
}

// 全局单例
export const api = new Api();

// 业务 API 方法
export const authApi = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
};

export const productApi = {
  list: (params) => api.get('/products', params),
  detail: (id) => api.get(`/products/${id}`),
  create: (data) => api.post('/products', data),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`),
};

export const cartApi = {
  list: () => api.get('/cart'),
  add: (product_id, quantity) => api.post('/cart', { product_id, quantity }),
  update: (product_id, quantity) => api.put(`/cart/${product_id}`, { quantity }),
  remove: (product_id) => api.delete(`/cart/${product_id}`),
};

export const orderApi = {
  list: () => api.get('/orders'),
  create: (data) => api.post('/orders', data),
  pay: (id) => api.put(`/orders/${id}/pay`),
  cancel: (id) => api.put(`/orders/${id}/cancel`),
  confirm: (id) => api.put(`/orders/${id}/confirm`),
};

export const aiApi = {
  chat: (data) => api.post('/agent/chat', data),
  confirm: (data) => api.post('/agent/confirm', data),
  history: (session_id) => api.get(`/agent/history/${session_id}`),
  clearHistory: (session_id) => api.delete(`/agent/history/${session_id}`),
  status: () => api.get('/ai/status'),
  stats: () => api.get('/ai/stats'),
};

export const adminApi = {
  users: () => api.get('/admin/users'),
  orders: () => api.get('/admin/orders'),
  ship: (id) => api.put(`/admin/orders/${id}/ship`),
  refund: (id) => api.put(`/admin/orders/${id}/refund`),
  stats: () => api.get('/admin/stats/sales'),
};
