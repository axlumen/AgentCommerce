/**
 * ProductCard 组件
 *
 * 商品卡片，展示商品图片、名称、价格、销量。
 */

import { Component } from '../core/component.js';
import { store } from '../core/store.js';
import { cartApi } from '../core/api.js';
import { Toast } from './Toast.js';

export class ProductCard extends Component {
  constructor(container, product) {
    super(container);
    this.product = product;
  }

  render() {
    const p = this.product;
    const discount = p.original_price && p.original_price > p.price
      ? Math.round((p.price / p.original_price) * 10)
      : null;

    this.html(`
      <div class="product-card" data-id="${p.id}">
        <!-- 商品图片 -->
        <div class="product-image">
          <img src="${p.image_url || '/static/default-product.png'}"
               alt="${p.name}"
               loading="lazy"
               onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 200 200%22><rect fill=%22%23f0f0f0%22 width=%22200%22 height=%22200%22/><text x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22 font-size=%2220%22>暂无图片</text></svg>'">

          <!-- 标签 -->
          <div class="product-tags">
            ${discount ? `<span class="tag tag-discount">${discount}折</span>` : ''}
            ${p.is_new ? '<span class="tag tag-new">新品</span>' : ''}
            ${p.sales_count > 100 ? '<span class="tag tag-hot">热销</span>' : ''}
          </div>

          <!-- 快捷操作 -->
          <div class="product-actions-overlay">
            <button class="btn-icon" title="收藏" data-action="favorite">
              <span>♡</span>
            </button>
            <button class="btn-icon" title="问 AI" data-action="ask-ai">
              <span>🤖</span>
            </button>
          </div>
        </div>

        <!-- 商品信息 -->
        <div class="product-info">
          <!-- 品牌 -->
          ${p.brand ? `<span class="product-brand">${p.brand}</span>` : ''}

          <!-- 名称 -->
          <a href="#/products/${p.id}" class="product-name" data-link title="${p.name}">
            ${p.name}
          </a>

          <!-- 价格 -->
          <div class="product-price">
            <span class="price-current">¥${p.price.toFixed(2)}</span>
            ${p.original_price && p.original_price > p.price ? `
              <span class="price-original">¥${p.original_price.toFixed(2)}</span>
            ` : ''}
          </div>

          <!-- 底部信息 -->
          <div class="product-footer">
            <span class="product-sales">已售 ${p.sales_count || 0}</span>
            <button class="btn btn-primary btn-sm" data-action="add-to-cart">
              加入购物车
            </button>
          </div>
        </div>
      </div>
    `);

    this.bindEvents();
  }

  bindEvents() {
    // 加入购物车
    this.on('click', '[data-action="add-to-cart"]', async (e) => {
      e.preventDefault();
      e.stopPropagation();

      if (!store.isLoggedIn()) {
        Toast.warning('请先登录');
        window.dispatchEvent(new CustomEvent('auth:required'));
        return;
      }

      const btn = e.target.closest('button');
      btn.disabled = true;
      btn.textContent = '添加中...';

      try {
        await cartApi.add(this.product.id, 1);
        Toast.success(`已将 ${this.product.name} 加入购物车`);
        window.dispatchEvent(new CustomEvent('cart:updated'));
      } catch (error) {
        Toast.error(error.message || '添加失败');
      } finally {
        btn.disabled = false;
        btn.textContent = '加入购物车';
      }
    });

    // 问 AI
    this.on('click', '[data-action="ask-ai"]', (e) => {
      e.preventDefault();
      e.stopPropagation();
      window.dispatchEvent(new CustomEvent('chat:open', {
        detail: { question: `帮我介绍一下 ${this.product.name}` }
      }));
    });

    // 点击卡片跳转详情
    this.on('click', '.product-card', (e) => {
      if (e.target.closest('[data-action]') || e.target.closest('a')) return;
      window.location.hash = `#/products/${this.product.id}`;
    });
  }
}
