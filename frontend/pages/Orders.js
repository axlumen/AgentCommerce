/**
 * Orders 页面
 *
 * 订单列表页面，展示用户订单，支持支付、取消、确认收货。
 */

import { Component } from '../core/component.js';
import { orderApi } from '../core/api.js';
import { Toast } from '../components/Toast.js';

export class Orders extends Component {
  constructor(container) {
    super(container);
    this.state = {
      orders: [],
      loading: true,
      error: null,
      activeTab: 'all', // all, pending, paid, shipped, completed
    };
  }

  async onMount() {
    await this.loadOrders();
  }

  async loadOrders() {
    try {
      this.state.loading = true;
      this.render();

      const data = await orderApi.list();
      this.state.orders = data.items || [];
    } catch (error) {
      this.state.error = error.message;
    } finally {
      this.state.loading = false;
      this.render();
    }
  }

  render() {
    const { orders, loading, error, activeTab } = this.state;

    // 按状态筛选
    const filteredOrders = activeTab === 'all'
      ? orders
      : orders.filter(order => order.status === activeTab);

    // 状态统计
    const stats = {
      all: orders.length,
      pending: orders.filter(o => o.status === 'pending').length,
      paid: orders.filter(o => o.status === 'paid').length,
      shipped: orders.filter(o => o.status === 'shipped').length,
      completed: orders.filter(o => o.status === 'completed').length,
    };

    this.html(`
      <div class="page page-orders">
        <div class="container">
          <h1 class="page-title">我的订单</h1>

          <!-- 状态标签 -->
          <div class="order-tabs">
            <button class="tab-btn ${activeTab === 'all' ? 'active' : ''}" data-tab="all">
              全部 (${stats.all})
            </button>
            <button class="tab-btn ${activeTab === 'pending' ? 'active' : ''}" data-tab="pending">
              待付款 (${stats.pending})
            </button>
            <button class="tab-btn ${activeTab === 'paid' ? 'active' : ''}" data-tab="paid">
              待发货 (${stats.paid})
            </button>
            <button class="tab-btn ${activeTab === 'shipped' ? 'active' : ''}" data-tab="shipped">
              待收货 (${stats.shipped})
            </button>
            <button class="tab-btn ${activeTab === 'completed' ? 'active' : ''}" data-tab="completed">
              已完成 (${stats.completed})
            </button>
          </div>

          ${loading ? `
            <div class="loading-state">
              <div class="loading-spinner"></div>
              <p>加载中...</p>
            </div>
          ` : error ? `
            <div class="error-state">
              <div class="error-icon">😕</div>
              <h3>加载失败</h3>
              <p>${error}</p>
              <button class="btn btn-primary" onclick="location.reload()">重试</button>
            </div>
          ` : filteredOrders.length === 0 ? `
            <div class="empty-state">
              <div class="empty-icon">📋</div>
              <h3>暂无订单</h3>
              <p>快去挑选心仪的商品吧</p>
              <a href="#/products" class="btn btn-primary" data-link>去购物</a>
            </div>
          ` : `
            <!-- 订单列表 -->
            <div class="order-list">
              ${filteredOrders.map(order => this.renderOrder(order)).join('')}
            </div>
          `}
        </div>
      </div>
    `);

    this.bindEvents();
  }

  renderOrder(order) {
    const statusMap = {
      pending: { label: '待付款', class: 'status-pending' },
      paid: { label: '待发货', class: 'status-paid' },
      shipped: { label: '待收货', class: 'status-shipped' },
      completed: { label: '已完成', class: 'status-completed' },
      cancelled: { label: '已取消', class: 'status-cancelled' },
    };

    const status = statusMap[order.status] || { label: order.status, class: '' };
    const createdTime = new Date(order.created_at).toLocaleString('zh-CN');
    const items = order.items || [];

    return `
      <div class="order-card" data-id="${order.id}">
        <!-- 订单头部 -->
        <div class="order-header">
          <div class="order-info">
            <span class="order-number">订单号：${order.order_no || order.id}</span>
            <span class="order-time">${createdTime}</span>
          </div>
          <span class="order-status ${status.class}">${status.label}</span>
        </div>

        <!-- 订单商品 -->
        <div class="order-items">
          ${items.map(item => `
            <div class="order-item">
              <div class="item-image">
                <img src="${item.product_image || '/static/default-product.png'}"
                     alt="${item.product_name}"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 60 60%22><rect fill=%22%23f0f0f0%22 width=%2260%22 height=%2260%22/><text x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22 font-size=%2210%22>暂无</text></svg>'">
              </div>
              <div class="item-info">
                <span class="item-name">${item.product_name}</span>
                <span class="item-quantity">x${item.quantity}</span>
              </div>
              <span class="item-price">¥${Number(item.subtotal || item.product_price * item.quantity).toFixed(2)}</span>
            </div>
          `).join('')}
        </div>

        <!-- 订单底部 -->
        <div class="order-footer">
          <div class="order-total">
            <span>共 ${items.reduce((sum, item) => sum + item.quantity, 0)} 件商品</span>
            <span class="total-label">合计：</span>
            <span class="total-price">¥${Number(order.total_amount).toFixed(2)}</span>
          </div>

          <div class="order-actions">
            ${order.status === 'pending' ? `
              <button class="btn btn-outline btn-sm" data-action="cancel" data-id="${order.id}">取消订单</button>
              <button class="btn btn-primary btn-sm" data-action="pay" data-id="${order.id}">立即支付</button>
            ` : ''}
            ${order.status === 'shipped' ? `
              <button class="btn btn-primary btn-sm" data-action="confirm" data-id="${order.id}">确认收货</button>
            ` : ''}
            ${order.status === 'completed' ? `
              <button class="btn btn-outline btn-sm" data-action="review" data-id="${order.id}">评价</button>
            ` : ''}
            <a href="#/orders/${order.id}" class="btn btn-outline btn-sm" data-link>查看详情</a>
          </div>
        </div>
      </div>
    `;
  }

  bindEvents() {
    // 切换标签
    this.on('click', '.tab-btn', (e) => {
      this.state.activeTab = e.target.dataset.tab;
      this.render();
    });

    // 取消订单
    this.on('click', '[data-action="cancel"]', async (e) => {
      const id = e.target.dataset.id;
      if (!confirm('确定要取消这个订单吗？')) return;

      try {
        await orderApi.cancel(id);
        Toast.success('订单已取消');
        await this.loadOrders();
      } catch (error) {
        Toast.error(error.message || '取消失败');
      }
    });

    // 支付订单
    this.on('click', '[data-action="pay"]', async (e) => {
      const id = e.target.dataset.id;

      try {
        await orderApi.pay(id);
        Toast.success('支付成功');
        await this.loadOrders();
      } catch (error) {
        Toast.error(error.message || '支付失败');
      }
    });

    // 确认收货
    this.on('click', '[data-action="confirm"]', async (e) => {
      const id = e.target.dataset.id;
      if (!confirm('确认已经收到商品吗？')) return;

      try {
        await orderApi.confirm(id);
        Toast.success('已确认收货');
        await this.loadOrders();
      } catch (error) {
        Toast.error(error.message || '确认失败');
      }
    });
  }
}
