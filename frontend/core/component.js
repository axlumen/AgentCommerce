/**
 * 组件基类
 *
 * 所有组件继承此类，提供生命周期和 DOM 操作方法。
 */

export class Component {
  constructor(container) {
    this.container = container;
    this.state = {};
    this.mounted = false;
  }

  /**
   * 设置状态并重新渲染
   */
  setState(newState) {
    this.state = { ...this.state, ...newState };
    if (this.mounted) {
      this.render();
    }
  }

  /**
   * 渲染组件（子类重写）
   */
  render() {
    throw new Error('render() must be implemented');
  }

  /**
   * 挂载组件
   */
  mount() {
    this.mounted = true;
    this.render();
    this.onMount();
  }

  /**
   * 卸载组件
   */
  unmount() {
    this.mounted = false;
    this.onUnmount();
    if (this.container) {
      this.container.innerHTML = '';
    }
  }

  /**
   * 生命周期：挂载后
   */
  onMount() {}

  /**
   * 生命周期：卸载前
   */
  onUnmount() {}

  /**
   * 查询元素
   */
  $(selector) {
    return this.container.querySelector(selector);
  }

  /**
   * 查询所有元素
   */
  $$(selector) {
    return this.container.querySelectorAll(selector);
  }

  /**
   * 创建元素
   */
  createElement(tag, attrs = {}, children = []) {
    const el = document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => {
      if (key === 'className') {
        el.className = value;
      } else if (key === 'style' && typeof value === 'object') {
        Object.assign(el.style, value);
      } else if (key.startsWith('on')) {
        el.addEventListener(key.slice(2).toLowerCase(), value);
      } else if (key === 'innerHTML') {
        el.innerHTML = value;
      } else if (key === 'textContent') {
        el.textContent = value;
      } else {
        el.setAttribute(key, value);
      }
    });
    children.forEach(child => {
      if (typeof child === 'string') {
        el.appendChild(document.createTextNode(child));
      } else if (child instanceof Node) {
        el.appendChild(child);
      }
    });
    return el;
  }

  /**
   * 绑定事件
   */
  on(event, selector, handler) {
    if (typeof selector === 'function') {
      handler = selector;
      this.container.addEventListener(event, handler);
    } else {
      this.container.addEventListener(event, (e) => {
        const target = e.target.closest(selector);
        if (target && this.container.contains(target)) {
          handler.call(target, e, target);
        }
      });
    }
  }

  /**
   * HTML 模板
   */
  html(template) {
    this.container.innerHTML = template;
  }
}
