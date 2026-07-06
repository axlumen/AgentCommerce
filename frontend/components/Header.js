/**
 * Header 组件
 *
 * 顶部导航栏，包含 logo、导航、用户菜单、主题切换。
 */

import { Component } from '../core/component.js';
import { store } from '../core/store.js';
import { router } from '../core/router.js';

export class Header extends Component {
  constructor(container) {
    super(container);
    this.state = {
      user: store.get('user'),
      theme: store.get('theme'),
      mobileMenuOpen: false,
    };

    // 订阅状态变化
    store.subscribe('user', (user) => this.setState({ user }));
    store.subscribe('theme', (theme) => this.setState({ theme }));
  }

  render() {
    const { user, theme, mobileMenuOpen } = this.state;

    this.html(`
      <header class="header">
        <div class="header-container">
          <!-- Logo -->
          <a href="#/" class="header-logo" data-link>
            <span class="logo-icon">🛒</span>
            <span class="logo-text">AgentCommerce</span>
          </a>

          <!-- 导航 -->
          <nav class="header-nav ${mobileMenuOpen ? 'active' : ''}">
            <a href="#/" class="nav-link ${this.isActive('/')}" data-link>
              <span class="nav-icon">🏠</span>
              <span>首页</span>
            </a>
            <a href="#/products" class="nav-link ${this.isActive('/products')}" data-link>
              <span class="nav-icon">📦</span>
              <span>商品</span>
            </a>
            ${user ? `
              <a href="#/cart" class="nav-link ${this.isActive('/cart')}" data-link>
                <span class="nav-icon">🛒</span>
                <span>购物车</span>
                <span class="cart-badge" id="cart-badge">0</span>
              </a>
              <a href="#/orders" class="nav-link ${this.isActive('/orders')}" data-link>
                <span class="nav-icon">📋</span>
                <span>订单</span>
              </a>
              ${user.role === 'admin' ? `
                <a href="#/admin" class="nav-link ${this.isActive('/admin')}" data-link>
                  <span class="nav-icon">⚙️</span>
                  <span>管理</span>
                </a>
              ` : ''}
            ` : ''}
          </nav>

          <!-- 右侧操作 -->
          <div class="header-actions">
            <!-- 主题切换 -->
            <button class="btn-icon" id="theme-toggle" title="切换主题">
              ${theme === 'dark' ? '☀️' : '🌙'}
            </button>

            <!-- 用户菜单 -->
            ${user ? `
              <div class="user-menu">
                <button class="user-menu-trigger" id="user-menu-trigger">
                  <span class="user-avatar">${user.username.charAt(0).toUpperCase()}</span>
                  <span class="user-name">${user.username}</span>
                </button>
                <div class="user-menu-dropdown" id="user-menu-dropdown">
                  <div class="menu-header">
                    <span class="menu-user-name">${user.username}</span>
                    <span class="menu-user-email">${user.email || ''}</span>
                  </div>
                  <div class="menu-divider"></div>
                  <a href="#/orders" class="menu-item" data-link>
                    <span>📋</span>
                    <span>我的订单</span>
                  </a>
                  <button class="menu-item" id="logout-btn">
                    <span>🚪</span>
                    <span>退出登录</span>
                  </button>
                </div>
              </div>
            ` : `
              <a href="#/login" class="btn btn-primary btn-sm" data-link>登录</a>
            `}

            <!-- 移动端菜单按钮 -->
            <button class="btn-icon mobile-menu-btn" id="mobile-menu-btn">
              <span class="menu-icon">☰</span>
            </button>
          </div>
        </div>
      </header>
    `);

    this.bindEvents();
  }

  bindEvents() {
    // 主题切换
    this.on('click', '#theme-toggle', () => {
      const newTheme = this.state.theme === 'dark' ? 'light' : 'dark';
      store.set('theme', newTheme);
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
    });

    // 用户菜单
    this.on('click', '#user-menu-trigger', (e) => {
      e.stopPropagation();
      const dropdown = this.$('#user-menu-dropdown');
      dropdown.classList.toggle('active');
    });

    // 登出
    this.on('click', '#logout-btn', () => {
      store.logout();
      router.navigate('/');
      window.dispatchEvent(new CustomEvent('toast:show', {
        detail: { message: '已退出登录', type: 'info' }
      }));
    });

    // 移动端菜单
    this.on('click', '#mobile-menu-btn', () => {
      this.setState({ mobileMenuOpen: !this.state.mobileMenuOpen });
    });

    // 点击外部关闭下拉菜单
    document.addEventListener('click', () => {
      const dropdown = this.$('#user-menu-dropdown');
      if (dropdown) {
        dropdown.classList.remove('active');
      }
    });

    // 路由链接点击
    this.on('click', '[data-link]', (e) => {
      this.setState({ mobileMenuOpen: false });
    });
  }

  isActive(path) {
    const currentPage = store.get('currentPage');
    if (path === '/') return currentPage === 'home' ? 'active' : '';
    return currentPage.startsWith(path.slice(1)) ? 'active' : '';
  }
}
