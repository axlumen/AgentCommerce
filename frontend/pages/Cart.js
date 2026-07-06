/**
 * Cart 页面
 *
 * 购物车页面，展示购物车商品，支持修改数量、删除、结算。
 */

import { Component } from '../core/component.js';
import { cartApi, orderApi } from '../core/api.js';
import { store } from '../core/store.js';
import { Toast } from '../components/Toast.js';

export class Cart extends Component {
  constructor(container) {
    super(container);
    this.state = {
      items: [],
      loading: true,
      error: null,
      selectedItems: new Set(),
      submitting: false,
    };
  }

  async onMount() {
    await this.loadCart();
    window.addEventListener('cart:updated', () => this.loadCart());
  }

  async loadCart() {
    try {
      this.state.loading = true;
      this.render();

      const data = await cartApi.list();
      this.state.items = data.items || [];
    } catch (error) {
      this.state.error = error.message;
    } finally {
      this.state.loading = false;
      this.render();
    }
  }

  render() {
    const { items, loading, error, selectedItems, submitting } = this.state;

    // 计算选中商品的总价
    const price = (item) => Number(item.price || item.product_price);
    const selectedProducts = items.filter(item => selectedItems.has(item.product_id));
    const totalPrice = selectedProducts.reduce((sum, item) => sum + price(item) * item.quantity, 0);
    const totalCount = selectedProducts.reduce((sum, item) => sum + item.quantity, 0);

    this.html(`
      <div class="page page-cart">
        <div class="container">
          <h1 class="page-title">购物车</h1>

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
          ` : items.length === 0 ? `
            <div class="empty-state">
              <div class="empty-icon">🛒</div>
              <h3>购物车是空的</h3>
              <p>快去挑选心仪的商品吧</p>
              <a href="#/products" class="btn btn-primary" data-link>去购物</a>
            </div>
          ` : `
            <!-- 购物车列表 -->
            <div class="cart-layout">
              <div class="cart-items">
                <!-- 全选 -->
                <div class="cart-header">
                  <label class="checkbox-label">
                    <input type="checkbox" id="select-all" ${selectedItems.size === items.length ? 'checked' : ''}>
                    <span>全选</span>
                  </label>
                  <span class="cart-count">共 ${items.length} 件商品</span>
                </div>

                <!-- 商品列表 -->
                ${items.map(item => `
                  <div class="cart-item ${selectedItems.has(item.product_id) ? 'selected' : ''}" data-id="${item.product_id}">
                    <label class="checkbox-label">
                      <input type="checkbox" class="item-checkbox" data-id="${item.product_id}" ${selectedItems.has(item.product_id) ? 'checked' : ''}>
                    </label>

                    <div class="item-image">
                      <img src="${item.product_image || item.image_url || '/static/default-product.png'}"
                           alt="${item.product_name || item.name}"
                           onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect fill=%22%23f0f0f0%22 width=%22100%22 height=%22100%22/><text x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22 font-size=%2212%22>暂无</text></svg>'">
                    </div>

                    <div class="item-info">
                      <a href="#/products/${item.product_id}" class="item-name" data-link>${item.product_name || item.name}</a>
                      ${item.brand ? `<span class="item-brand">${item.brand}</span>` : ''}
                    </div>

                    <div class="item-price">
                      <span class="price-current">¥${Number(item.price || item.product_price).toFixed(2)}</span>
                    </div>

                    <div class="item-quantity">
                      <button class="btn btn-outline btn-sm quantity-btn" data-action="minus" data-id="${item.product_id}" ${item.quantity <= 1 ? 'disabled' : ''}>-</button>
                      <span class="quantity-value">${item.quantity}</span>
                      <button class="btn btn-outline btn-sm quantity-btn" data-action="plus" data-id="${item.product_id}" ${item.quantity >= item.stock ? 'disabled' : ''}>+</button>
                    </div>

                    <div class="item-subtotal">
                      <span>¥${(Number(item.price || item.product_price) * item.quantity).toFixed(2)}</span>
                    </div>

                    <button class="btn btn-icon" data-action="delete" data-id="${item.product_id}" title="删除">
                      <span>🗑️</span>
                    </button>
                  </div>
                `).join('')}
              </div>

              <!-- 结算栏 -->
              <div class="cart-summary">
                <div class="summary-row">
                  <span>已选商品：</span>
                  <span>${totalCount} 件</span>
                </div>
                <div class="summary-row total">
                  <span>合计：</span>
                  <span class="price-total">¥${totalPrice.toFixed(2)}</span>
                </div>
                <button class="btn btn-primary btn-lg btn-block" id="checkout-btn" ${selectedItems.size === 0 || submitting ? 'disabled' : ''}>
                  ${submitting ? '提交中...' : `结算 (${selectedItems.size})`}
                </button>
              </div>
            </div>
          `}
        </div>
      </div>
    `);

    this.bindEvents();
  }

  bindEvents() {
    // 全选
    this.on('change', '#select-all', (e) => {
      const checked = e.target.checked;
      if (checked) {
        this.state.selectedItems = new Set(this.state.items.map(item => item.product_id));
      } else {
        this.state.selectedItems = new Set();
      }
      this.render();
    });

    // 单选
    this.on('change', '.item-checkbox', (e) => {
      const id = parseInt(e.target.dataset.id);
      if (e.target.checked) {
        this.state.selectedItems.add(id);
      } else {
        this.state.selectedItems.delete(id);
      }
      this.render();
    });

    // 修改数量
    this.on('click', '.quantity-btn', async (e) => {
      const btn = e.target.closest('button');
      const id = parseInt(btn.dataset.id);
      const action = btn.dataset.action;
      const item = this.state.items.find(i => i.product_id === id);
      if (!item) return;

      const newQuantity = action === 'minus' ? item.quantity - 1 : item.quantity + 1;
      if (newQuantity < 1 || newQuantity > item.stock) return;

      try {
        await cartApi.update(id, newQuantity);
        item.quantity = newQuantity;
        this.render();
      } catch (error) {
        Toast.error(error.message || '修改失败');
      }
    });

    // 删除商品
    this.on('click', '[data-action="delete"]', async (e) => {
      const btn = e.target.closest('button');
      const id = parseInt(btn.dataset.id);

      try {
        await cartApi.remove(id);
        this.state.items = this.state.items.filter(i => i.product_id !== id);
        this.state.selectedItems.delete(id);
        Toast.success('已删除');
        window.dispatchEvent(new CustomEvent('cart:updated'));
        this.render();
      } catch (error) {
        Toast.error(error.message || '删除失败');
      }
    });

    // 结算
    this.on('click', '#checkout-btn', async () => {
      if (this.state.selectedItems.size === 0) return;

      this.state.submitting = true;
      this.render();

      try {
        const selectedProducts = this.state.items.filter(item =>
          this.state.selectedItems.has(item.product_id)
        );

        const orderData = {
          cart_item_ids: selectedProducts.map(item => item.product_id),
          address: { address: "默认地址", phone: "" },
        };

        const order = await orderApi.create(orderData);
        Toast.success('订单创建成功');

        // 从本地状态中移除已结算的商品
        this.state.items = this.state.items.filter(item =>
          !this.state.selectedItems.has(item.product_id)
        );
        this.state.selectedItems = new Set();

        // 跳转到订单页
        window.location.hash = '#/orders';
      } catch (error) {
        Toast.error(error.message || '结算失败');
      } finally {
        this.state.submitting = false;
        this.render();
      }
    });
  }

  onUnmount() {
    window.removeEventListener('cart:updated', this.loadCart);
  }
}
