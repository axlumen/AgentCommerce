/**
 * 应用入口
 *
 * 初始化路由、组件、状态管理。
 */

import { store } from './core/store.js';
import { router } from './core/router.js';
import { Header } from './components/Header.js';
import { Toast } from './components/Toast.js';
import { Chat } from './components/Chat.js';
import { Home } from './pages/Home.js';
import { Products } from './pages/Products.js';
import { ProductDetail } from './pages/ProductDetail.js';
import { Cart } from './pages/Cart.js';
import { Orders } from './pages/Orders.js';
import { Login } from './pages/Login.js';
import { authApi } from './core/api.js';

class App {
  constructor() {
    this.components = {};
  }

  async init() {
    // 初始化主题
    this.initTheme();

    // 初始化组件
    this.initComponents();

    // 注册路由
    this.registerRoutes();

    // 检查登录状态
    await this.checkAuth();

    // 启动路由
    router.start();

    console.log('App initialized');
  }

  initTheme() {
    const theme = store.get('theme');
    document.documentElement.setAttribute('data-theme', theme);

    // 监听主题变化
    store.subscribe('theme', (theme) => {
      document.documentElement.setAttribute('data-theme', theme);
    });
  }

  initComponents() {
    // Header
    const headerContainer = document.getElementById('header');
    if (headerContainer) {
      this.components.header = new Header(headerContainer);
      this.components.header.mount();
    }

    // Toast
    const toastContainer = document.getElementById('toast-container');
    if (toastContainer) {
      this.components.toast = new Toast(toastContainer);
      this.components.toast.mount();
    }

    // Chat
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
      this.components.chat = new Chat(chatContainer);
      this.components.chat.mount();
    }
  }

  registerRoutes() {
    router.register('/', (container) => new Home(container));
    router.register('/products', (container, params) => new Products(container, params));
    router.register('/products/:id', (container, params) => new ProductDetail(container, params));
    router.register('/cart', (container) => new Cart(container));
    router.register('/orders', (container) => new Orders(container));
    router.register('/login', (container) => new Login(container));
  }

  async checkAuth() {
    const token = store.get('token');
    if (!token) return;

    try {
      const user = await authApi.me();
      store.setUser(user);
    } catch (error) {
      // Token 无效，清除登录状态
      store.logout();
    }
  }
}

// 启动应用
const app = new App();
app.init().catch(console.error);
