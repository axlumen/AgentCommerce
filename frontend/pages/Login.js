/**
 * Login 页面
 *
 * 登录/注册页面。
 */

import { Component } from '../core/component.js';
import { authApi } from '../core/api.js';
import { store } from '../core/store.js';
import { Toast } from '../components/Toast.js';

export class Login extends Component {
  constructor(container) {
    super(container);
    this.state = {
      mode: 'login', // login 或 register
      loading: false,
    };
  }

  render() {
    const { mode, loading } = this.state;

    this.html(`
      <div class="page page-login">
        <div class="container">
          <div class="auth-card">
            <div class="auth-header">
              <h1 class="auth-title">${mode === 'login' ? '登录' : '注册'}</h1>
              <p class="auth-subtitle">${mode === 'login' ? '欢迎回来' : '创建新账号'}</p>
            </div>

            <!-- 登录表单 -->
            <form id="login-form" class="auth-form ${mode === 'login' ? 'active' : ''}">
              <div class="form-group">
                <label class="form-label" for="login-username">用户名</label>
                <input type="text" class="form-input" id="login-username" placeholder="请输入用户名" required>
              </div>
              <div class="form-group">
                <label class="form-label" for="login-password">密码</label>
                <input type="password" class="form-input" id="login-password" placeholder="请输入密码" required>
              </div>
              <button type="submit" class="btn btn-primary btn-block" disabled=${loading}>
                ${loading ? '登录中...' : '登录'}
              </button>
            </form>

            <!-- 注册表单 -->
            <form id="register-form" class="auth-form ${mode === 'register' ? 'active' : ''}">
              <div class="form-group">
                <label class="form-label" for="reg-username">用户名</label>
                <input type="text" class="form-input" id="reg-username" placeholder="请输入用户名" required>
              </div>
              <div class="form-group">
                <label class="form-label" for="reg-email">邮箱</label>
                <input type="email" class="form-input" id="reg-email" placeholder="请输入邮箱" required>
              </div>
              <div class="form-group">
                <label class="form-label" for="reg-password">密码</label>
                <input type="password" class="form-input" id="reg-password" placeholder="请输入密码" required minlength="6">
              </div>
              <div class="form-group">
                <label class="form-label" for="reg-phone">手机号（可选）</label>
                <input type="tel" class="form-input" id="reg-phone" placeholder="请输入手机号">
              </div>
              <button type="submit" class="btn btn-primary btn-block" disabled=${loading}>
                ${loading ? '注册中...' : '注册'}
              </button>
            </form>

            <!-- 切换登录/注册 -->
            <div class="auth-footer">
              ${mode === 'login' ? `
                <p>还没有账号？<button class="btn-link" id="switch-to-register">立即注册</button></p>
              ` : `
                <p>已有账号？<button class="btn-link" id="switch-to-login">立即登录</button></p>
              `}
            </div>

            <!-- 演示账号 -->
            <div class="auth-demo">
              <p class="demo-title">演示账号</p>
              <div class="demo-accounts">
                <button class="demo-btn" data-username="admin" data-password="admin123">
                  <span class="demo-role">管理员</span>
                  <span class="demo-info">admin / admin123</span>
                </button>
                <button class="demo-btn" data-username="user1" data-password="user123">
                  <span class="demo-role">普通用户</span>
                  <span class="demo-info">user1 / user123</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `);

    this.bindEvents();
  }

  bindEvents() {
    // 切换到注册
    this.on('click', '#switch-to-register', () => {
      this.state.mode = 'register';
      this.render();
    });

    // 切换到登录
    this.on('click', '#switch-to-login', () => {
      this.state.mode = 'login';
      this.render();
    });

    // 登录表单提交
    this.on('submit', '#login-form', async (e) => {
      e.preventDefault();
      await this.handleLogin();
    });

    // 注册表单提交
    this.on('submit', '#register-form', async (e) => {
      e.preventDefault();
      await this.handleRegister();
    });

    // 演示账号
    this.on('click', '.demo-btn', (e) => {
      const btn = e.target.closest('.demo-btn');
      const username = btn.dataset.username;
      const password = btn.dataset.password;

      this.$('#login-username').value = username;
      this.$('#login-password').value = password;
      this.state.mode = 'login';
      this.render();

      // 自动登录
      setTimeout(() => this.handleLogin(), 100);
    });
  }

  async handleLogin() {
    const username = this.$('#login-username')?.value.trim();
    const password = this.$('#login-password')?.value;

    if (!username || !password) {
      Toast.error('请输入用户名和密码');
      return;
    }

    this.state.loading = true;
    this.render();

    try {
      const data = await authApi.login(username, password);
      store.setToken(data.access_token);

      // 获取用户信息
      const user = await authApi.me();
      store.setUser(user);

      Toast.success(`欢迎回来，${user.username}`);

      // 跳转到首页
      window.location.hash = '#/';
      window.dispatchEvent(new CustomEvent('auth:login'));
    } catch (error) {
      Toast.error(error.message || '登录失败');
    } finally {
      this.state.loading = false;
      this.render();
    }
  }

  async handleRegister() {
    const username = this.$('#reg-username')?.value.trim();
    const email = this.$('#reg-email')?.value.trim();
    const password = this.$('#reg-password')?.value;
    const phone = this.$('#reg-phone')?.value.trim();

    if (!username || !email || !password) {
      Toast.error('请填写必填字段');
      return;
    }

    this.state.loading = true;
    this.render();

    try {
      await authApi.register({ username, email, password, phone });
      Toast.success('注册成功，请登录');
      this.state.mode = 'login';
      this.render();
    } catch (error) {
      Toast.error(error.message || '注册失败');
    } finally {
      this.state.loading = false;
      this.render();
    }
  }
}
