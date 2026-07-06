/**
 * ProductDetail 页面
 *
 * 商品详情页，展示商品信息、图片、价格、库存，支持加购。
 */

import { Component } from '../core/component.js';
import { productApi, cartApi, aiApi } from '../core/api.js';
import { store } from '../core/store.js';
import { Toast } from '../components/Toast.js';

export class ProductDetail extends Component {
  constructor(container, params) {
    super(container);
    this.productId = params.id;
    this.state = {
      product: null,
      loading: true,
      error: null,
      quantity: 1,
      relatedProducts: [],
    };
  }

  async onMount() {
    await this.loadProduct();
  }

  async loadProduct() {
    try {
      this.state.loading = true;
      this.render();

      const product = await productApi.detail(this.productId);
      this.state.product = product;

      // 加载相关商品（简单实现：同分类）
      if (product.category_id) {
        const related = await productApi.list({
          category_id: product.category_id,
          size: 4,
        });
        this.state.relatedProducts = (related.items || []).filter(p => p.id !== product.id).slice(0, 3);
      }
    } catch (error) {
      this.state.error = error.message;
    } finally {
      this.state.loading = false;
      this.render();
    }
  }

  render() {
    const { product, loading, error, quantity, relatedProducts } = this.state;

    if (loading) {
      this.html(`
        <div class="page page-detail">
          <div class="container">
            <div class="detail-skeleton">
              <div class="skeleton-image large"></div>
              <div class="skeleton-content">
                <div class="skeleton-text"></div>
                <div class="skeleton-text"></div>
                <div class="skeleton-text short"></div>
              </div>
            </div>
          </div>
        </div>
      `);
      return;
    }

    if (error || !product) {
      this.html(`
        <div class="page page-detail">
          <div class="container">
            <div class="error-state">
              <div class="error-icon">😕</div>
              <h3>商品不存在</h3>
              <p>${error || '未找到该商品'}</p>
              <a href="#/products" class="btn btn-primary" data-link>返回商品列表</a>
            </div>
          </div>
        </div>
      `);
      return;
    }

    const p = product;
    const price = Number(p.price);
    const originalPrice = p.original_price ? Number(p.original_price) : null;
    const discount = originalPrice && originalPrice > price
      ? Math.round((price / originalPrice) * 10)
      : null;

    // 确保 stock 是整数
    const stock = parseInt(p.stock, 10) || 0;

    this.html(`
      <div class="page page-detail">
        <div class="container">
          <!-- 面包屑 -->
          <nav class="breadcrumb">
            <a href="#/" data-link>首页</a>
            <span>/</span>
            <a href="#/products" data-link>商品</a>
            <span>/</span>
            <span>${p.name}</span>
          </nav>

          <!-- 商品详情 -->
          <div class="detail-main">
            <!-- 商品图片 -->
            <div class="detail-images">
              <div class="main-image">
                <img src="${p.image_url || '/static/default-product.png'}"
                     alt="${p.name}"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 400 400%22><rect fill=%22%23f0f0f0%22 width=%22400%22 height=%22400%22/><text x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22 font-size=%2224%22>暂无图片</text></svg>'">
              </div>
            </div>

            <!-- 商品信息 -->
            <div class="detail-info">
              <!-- 品牌 -->
              ${p.brand ? `<div class="detail-brand">${p.brand}</div>` : ''}

              <!-- 名称 -->
              <h1 class="detail-name">${p.name}</h1>

              <!-- 价格 -->
              <div class="detail-price">
                <span class="price-current">¥${price.toFixed(2)}</span>
                ${originalPrice && originalPrice > price ? `
                  <span class="price-original">¥${originalPrice.toFixed(2)}</span>
                  <span class="price-discount">${discount}折</span>
                ` : ''}
              </div>

              <!-- 销量 -->
              <div class="detail-sales">
                <span>累计销量：${p.sales_count || 0}</span>
                <span>好评率：99%</span>
              </div>

              <!-- 库存 -->
              <div class="detail-stock">
                <span class="stock-label">库存：</span>
                <span class="stock-value ${stock > 0 ? 'in-stock' : 'out-of-stock'}">
                  ${stock > 0 ? `${stock} 件` : '暂时缺货'}
                </span>
              </div>

              <!-- 规格 -->
              ${p.specs && Object.keys(p.specs).length > 0 ? `
                <div class="detail-specs">
                  <h3>规格参数</h3>
                  <div class="specs-grid">
                    ${Object.entries(p.specs).map(([key, value]) => `
                      <div class="spec-item">
                        <span class="spec-label">${key}</span>
                        <span class="spec-value">${value}</span>
                      </div>
                    `).join('')}
                  </div>
                </div>
              ` : ''}

              <!-- 数量选择 -->
              <div class="detail-quantity">
                <span class="quantity-label">数量：</span>
                <div class="quantity-control">
                  <button class="btn btn-outline btn-sm" id="quantity-minus" ${quantity <= 1 ? 'disabled' : ''}>-</button>
                  <input type="number" class="quantity-input" id="quantity-input" value="${quantity}" min="1" max="${p.stock}">
                  <button class="btn btn-outline btn-sm" id="quantity-plus" ${quantity >= stock ? 'disabled' : ''}>+</button>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="detail-actions">
                <button class="btn btn-primary btn-lg" id="add-to-cart" ${stock <= 0 ? 'disabled' : ''}>
                  <span>🛒</span>
                  <span>${stock > 0 ? '加入购物车' : '暂时缺货'}</span>
                </button>
                <button class="btn btn-outline btn-lg" id="ask-ai">
                  <span>🤖</span>
                  <span>问 AI</span>
                </button>
              </div>

              <!-- 描述 -->
              <div class="detail-description">
                <h3>商品描述</h3>
                <div class="description-content">
                  ${p.description || '暂无描述'}
                </div>
              </div>
            </div>
          </div>

          <!-- 相关商品 -->
          ${relatedProducts.length > 0 ? `
            <section class="section">
              <h2 class="section-title">相关商品</h2>
              <div class="product-grid" id="related-products">
                ${relatedProducts.map(p => `
                  <div class="product-card-mini">
                    <a href="#/products/${p.id}" data-link>
                      <img src="${p.image_url || '/static/default-product.png'}" alt="${p.name}">
                      <div class="product-info">
                        <span class="product-name">${p.name}</span>
                        <span class="product-price">¥${p.price.toFixed(2)}</span>
                      </div>
                    </a>
                  </div>
                `).join('')}
              </div>
            </section>
          ` : ''}
        </div>
      </div>
    `);

    this.bindEvents();
  }

  bindEvents() {
    // 数量减少
    this.on('click', '#quantity-minus', () => {
      if (this.state.quantity > 1) {
        this.state.quantity--;
        this.$('#quantity-input').value = this.state.quantity;
        this.$('#quantity-minus').disabled = this.state.quantity <= 1;
        this.$('#quantity-plus').disabled = false;
      }
    });

    // 数量增加
    this.on('click', '#quantity-plus', () => {
      const stock = parseInt(this.state.product.stock, 10) || 0;
      if (this.state.quantity < stock) {
        this.state.quantity++;
        this.$('#quantity-input').value = this.state.quantity;
        this.$('#quantity-plus').disabled = this.state.quantity >= stock;
        this.$('#quantity-minus').disabled = false;
      }
    });

    // 数量输入
    this.on('change', '#quantity-input', (e) => {
      const stock = parseInt(this.state.product.stock, 10) || 0;
      let value = parseInt(e.target.value);
      if (isNaN(value) || value < 1) value = 1;
      if (value > stock) value = stock;
      this.state.quantity = value;
      e.target.value = value;
    });

    // 加入购物车
    this.on('click', '#add-to-cart', async () => {
      if (!store.isLoggedIn()) {
        Toast.warning('请先登录');
        return;
      }

      const btn = this.$('#add-to-cart');
      btn.disabled = true;
      btn.innerHTML = '<span>添加中...</span>';

      try {
        await cartApi.add(this.productId, this.state.quantity);
        Toast.success('已加入购物车');
        window.dispatchEvent(new CustomEvent('cart:updated'));
      } catch (error) {
        Toast.error(error.message || '添加失败');
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>🛒</span><span>加入购物车</span>';
      }
    });

    // 问 AI
    this.on('click', '#ask-ai', () => {
      window.dispatchEvent(new CustomEvent('chat:open', {
        detail: { question: `帮我介绍一下 ${this.state.product.name}` }
      }));
    });
  }
}
