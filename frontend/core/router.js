/**
 * 路由系统
 *
 * SPA 路由，支持浏览器前进后退。
 */

import { store } from './store.js';

class Router {
  constructor() {
    this.routes = new Map();
    this.currentRoute = null;
    this.currentComponent = null;

    // 监听浏览器前进后退
    window.addEventListener('popstate', () => {
      this.navigate(window.location.hash.slice(1) || '/', false);
    });
  }

  /**
   * 注册路由
   */
  register(path, componentFactory) {
    this.routes.set(path, componentFactory);
  }

  /**
   * 导航到指定路由
   */
  navigate(path, pushState = true) {
    // 解析路径和参数
    const [pathname, query] = path.split('?');
    const params = new URLSearchParams(query || '');

    // 查找匹配的路由
    const route = this.matchRoute(pathname);

    if (!route) {
      console.warn(`Route not found: ${pathname}`);
      return;
    }

    // 更新浏览器历史
    if (pushState) {
      window.history.pushState(null, '', `#${path}`);
    }

    // 更新状态
    store.set('currentPage', route.page);
    this.currentRoute = { path: pathname, params, ...route };

    // 卸载当前组件
    if (this.currentComponent) {
      this.currentComponent.unmount();
    }

    // 创建新组件
    const container = document.getElementById('page-content');
    if (container && route.componentFactory) {
      this.currentComponent = route.componentFactory(container, route.params);
      this.currentComponent.mount();
    }

    // 触发路由变化事件
    window.dispatchEvent(new CustomEvent('route:change', {
      detail: { path: pathname, params, route }
    }));
  }

  /**
   * 匹配路由
   */
  matchRoute(pathname) {
    // 精确匹配
    if (this.routes.has(pathname)) {
      return { page: pathname.slice(1) || 'home', componentFactory: this.routes.get(pathname) };
    }

    // 动态路由匹配（如 /products/:id）
    for (const [pattern, factory] of this.routes) {
      const regex = this.pathToRegex(pattern);
      const match = pathname.match(regex);
      if (match) {
        const params = this.extractParams(pattern, match);
        return { page: pattern.slice(1).split('/')[0], componentFactory: factory, params };
      }
    }

    // 默认路由
    if (this.routes.has('/')) {
      return { page: 'home', componentFactory: this.routes.get('/') };
    }

    return null;
  }

  /**
   * 路径转正则
   */
  pathToRegex(path) {
    const pattern = path
      .replace(/\//g, '\\/')
      .replace(/:(\w+)/g, '(?<$1>[^/]+)');
    return new RegExp(`^${pattern}$`);
  }

  /**
   * 提取参数
   */
  extractParams(pattern, match) {
    const params = {};
    const keys = pattern.match(/:(\w+)/g) || [];
    keys.forEach((key, index) => {
      params[key.slice(1)] = match[index + 1];
    });
    return params;
  }

  /**
   * 启动路由
   */
  start() {
    const path = window.location.hash.slice(1) || '/';
    this.navigate(path, false);
  }
}

// 全局单例
export const router = new Router();
