/**
 * Products 页面
 *
 * 商品列表页，支持搜索、筛选、排序、分页。
 */

import { Component } from '../core/component.js';
import { productApi } from '../core/api.js';
import { ProductCard } from '../components/ProductCard.js';

export class Products extends Component {
  constructor(container, params = {}) {
    super(container);
    this.state = {
      products: [],
      loading: true,
      error: null,
      keyword: params.keyword || '',
      category: params.category || '',
      sort: params.sort || 'default',
      page: 1,
      totalPages: 1,
      total: 0,
    };
    this.productCards = [];
  }

  async onMount() {
    await this.loadProducts();
  }

  async loadProducts() {
    try {
      this.state.loading = true;
      this.render();

      const params = {
        page: this.state.page,
        size: 12,
      };

      if (this.state.keyword) params.keyword = this.state.keyword;
      if (this.state.category) params.category = this.state.category;
      if (this.state.sort !== 'default') params.sort = this.state.sort;

      const data = await productApi.list(params);

      this.state.products = data.items || [];
      this.state.total = data.total || 0;
      this.state.totalPages = Math.ceil(data.total / 12);
    } catch (error) {
      this.state.error = error.message;
    } finally {
      this.state.loading = false;
      this.render();
      this.mountProductCards();
    }
  }

  render() {
    const { products, loading, error, keyword, category, sort, page, totalPages, total } = this.state;

    this.html(`
      <div class="page page-products">
        <div class="container">
          <!-- 页面标题 -->
          <div class="page-header">
            <h1 class="page-title">${category || '全部商品'}</h1>
            <span class="page-count">共 ${total} 件商品</span>
          </div>

          <!-- 筛选栏 -->
          <div class="filter-bar">
            <!-- 搜索框 -->
            <div class="search-box">
              <input
                type="text"
                class="search-input"
                id="search-input"
                placeholder="搜索商品..."
                value="${keyword}"
              />
              <button class="btn btn-primary" id="search-btn">搜索</button>
            </div>

            <!-- 分类筛选 -->
            <div class="filter-group">
              <label>分类：</label>
              <select class="filter-select" id="category-filter">
                <option value="">全部</option>
                <option value="手机" ${category === '手机' ? 'selected' : ''}>手机</option>
                <option value="电脑" ${category === '电脑' ? 'selected' : ''}>电脑</option>
                <option value="耳机" ${category === '耳机' ? 'selected' : ''}>耳机</option>
                <option value="手表" ${category === '手表' ? 'selected' : ''}>手表</option>
                <option value="平板" ${category === '平板' ? 'selected' : ''}>平板</option>
              </select>
            </div>

            <!-- 排序 -->
            <div class="filter-group">
              <label>排序：</label>
              <select class="filter-select" id="sort-filter">
                <option value="default" ${sort === 'default' ? 'selected' : ''}>默认</option>
                <option value="price_asc" ${sort === 'price_asc' ? 'selected' : ''}>价格从低到高</option>
                <option value="price_desc" ${sort === 'price_desc' ? 'selected' : ''}>价格从高到低</option>
                <option value="sales" ${sort === 'sales' ? 'selected' : ''}>销量优先</option>
                <option value="new" ${sort === 'new' ? 'selected' : ''}>最新上架</option>
              </select>
            </div>
          </div>

          <!-- 商品列表 -->
          ${loading ? this.renderSkeleton() : error ? `
            <div class="error-message">${error}</div>
          ` : products.length === 0 ? `
            <div class="empty-state">
              <div class="empty-icon">📦</div>
              <h3>暂无商品</h3>
              <p>换个关键词试试</p>
            </div>
          ` : `
            <div class="product-grid" id="product-list">
              ${products.map((_, i) => `<div class="product-card-skeleton" data-index="${i}"></div>`).join('')}
            </div>
          `}

          <!-- 分页 -->
          ${totalPages > 1 ? `
            <div class="pagination">
              <button class="btn btn-outline" id="prev-page" ${page <= 1 ? 'disabled' : ''}>
                上一页
              </button>
              <span class="page-info">${page} / ${totalPages}</span>
              <button class="btn btn-outline" id="next-page" ${page >= totalPages ? 'disabled' : ''}>
                下一页
              </button>
            </div>
          ` : ''}
        </div>
      </div>
    `);

    this.bindEvents();
  }

  renderSkeleton() {
    return `
      <div class="product-grid">
        ${Array(12).fill('').map(() => `
          <div class="product-card-skeleton">
            <div class="skeleton-image"></div>
            <div class="skeleton-text"></div>
            <div class="skeleton-text short"></div>
          </div>
        `).join('')}
      </div>
    `;
  }

  mountProductCards() {
    const container = this.$('#product-list');
    if (!container) return;

    container.innerHTML = '';
    this.productCards.forEach(card => card.unmount());
    this.productCards = [];

    this.state.products.forEach(product => {
      const card = document.createElement('div');
      container.appendChild(card);
      const component = new ProductCard(card, product);
      component.mount();
      this.productCards.push(component);
    });
  }

  bindEvents() {
    // 搜索
    this.on('click', '#search-btn', () => {
      this.state.keyword = this.$('#search-input').value;
      this.state.page = 1;
      this.loadProducts();
    });

    this.on('keydown', '#search-input', (e) => {
      if (e.key === 'Enter') {
        this.state.keyword = e.target.value;
        this.state.page = 1;
        this.loadProducts();
      }
    });

    // 分类筛选
    this.on('change', '#category-filter', (e) => {
      this.state.category = e.target.value;
      this.state.page = 1;
      this.loadProducts();
    });

    // 排序
    this.on('change', '#sort-filter', (e) => {
      this.state.sort = e.target.value;
      this.state.page = 1;
      this.loadProducts();
    });

    // 分页
    this.on('click', '#prev-page', () => {
      if (this.state.page > 1) {
        this.state.page--;
        this.loadProducts();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });

    this.on('click', '#next-page', () => {
      if (this.state.page < this.state.totalPages) {
        this.state.page++;
        this.loadProducts();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  }

  onUnmount() {
    this.productCards.forEach(card => card.unmount());
    this.productCards = [];
  }
}
