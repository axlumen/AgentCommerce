/**
 * Toast 组件
 *
 * 全局提示框，支持 success、error、info、warning 类型。
 */

import { Component } from '../core/component.js';

export class Toast extends Component {
  constructor(container) {
    super(container);
    this.state = {
      message: '',
      type: 'info',
      visible: false,
    };
    this.timer = null;

    // 监听全局 toast 事件
    window.addEventListener('toast:show', (e) => {
      this.show(e.detail.message, e.detail.type || 'info');
    });
  }

  render() {
    const { message, type, visible } = this.state;

    this.html(`
      <div class="toast ${type} ${visible ? 'show' : ''}" id="toast">
        <span class="toast-icon">${this.getIcon(type)}</span>
        <span class="toast-message">${message}</span>
      </div>
    `);
  }

  getIcon(type) {
    const icons = {
      success: '✅',
      error: '❌',
      info: 'ℹ️',
      warning: '⚠️',
    };
    return icons[type] || icons.info;
  }

  show(message, type = 'info') {
    if (this.timer) {
      clearTimeout(this.timer);
    }

    this.setState({ message, type, visible: true });

    this.timer = setTimeout(() => {
      this.setState({ visible: false });
    }, 3000);
  }

  static success(message) {
    window.dispatchEvent(new CustomEvent('toast:show', {
      detail: { message, type: 'success' }
    }));
  }

  static error(message) {
    window.dispatchEvent(new CustomEvent('toast:show', {
      detail: { message, type: 'error' }
    }));
  }

  static info(message) {
    window.dispatchEvent(new CustomEvent('toast:show', {
      detail: { message, type: 'info' }
    }));
  }

  static warning(message) {
    window.dispatchEvent(new CustomEvent('toast:show', {
      detail: { message, type: 'warning' }
    }));
  }
}
