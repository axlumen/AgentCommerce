/**
 * 状态管理
 *
 * 集中管理应用状态，支持订阅和通知。
 */

class Store {
  constructor() {
    this.state = {
      user: null,
      token: localStorage.getItem('token'),
      cart: [],
      products: [],
      currentPage: 'home',
      chatOpen: false,
      chatSessionId: null,
      theme: localStorage.getItem('theme') || 'light',
    };
    this.listeners = new Map();
  }

  /**
   * 获取状态
   */
  get(key) {
    return this.state[key];
  }

  /**
   * 设置状态并通知订阅者
   */
  set(key, value) {
    const oldValue = this.state[key];
    this.state[key] = value;

    // 通知订阅者
    if (this.listeners.has(key)) {
      this.listeners.get(key).forEach(callback => {
        callback(value, oldValue);
      });
    }

    // 通知全局订阅者
    if (this.listeners.has('*')) {
      this.listeners.get('*').forEach(callback => {
        callback(key, value, oldValue);
      });
    }
  }

  /**
   * 订阅状态变化
   */
  subscribe(key, callback) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set());
    }
    this.listeners.get(key).add(callback);

    // 返回取消订阅函数
    return () => {
      this.listeners.get(key)?.delete(callback);
    };
  }

  /**
   * 批量更新
   */
  update(updates) {
    Object.entries(updates).forEach(([key, value]) => {
      this.set(key, value);
    });
  }

  /**
   * 获取用户信息
   */
  getUser() {
    return this.state.user;
  }

  /**
   * 设置用户信息
   */
  setUser(user) {
    this.set('user', user);
    if (user) {
      localStorage.setItem('user', JSON.stringify(user));
    } else {
      localStorage.removeItem('user');
    }
  }

  /**
   * 设置 token
   */
  setToken(token) {
    this.set('token', token);
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  /**
   * 是否已登录
   */
  isLoggedIn() {
    return !!this.state.token;
  }

  /**
   * 登出
   */
  logout() {
    this.set('user', null);
    this.set('token', null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }
}

// 全局单例
export const store = new Store();
