/**
 * Home 页面
 *
 * 首页，展示热销商品、推荐商品、分类导航。
 */

import { Component } from '../core/component.js';
import { productApi } from '../core/api.js';
import { ProductCard } from '../components/ProductCard.js';

export class Home extends Component {
  constructor(container) {
    super(container);
    this.state = {
      hotProducts: [],
      newProducts: [],
      loading: true,
      error: null,
    };
    this.productCards = [];
  }

  async onMount() {
    await this.loadData();
  }

  async loadData() {
    try {
      this.state.loading = true;
      this.render();

      const [hotData, newData] = await Promise.all([
        productApi.list({ page: 1, size: 8, sort_by: 'sales_count', sort_order: 'desc' }),
        productApi.list({ page: 1, size: 4, sort_by: 'created_at', sort_order: 'desc' }),
      ]);

      this.state.hotProducts = hotData.items || [];
      this.state.newProducts = newData.items || [];
    } catch (error) {
      this.state.error = error.message;
    } finally {
      this.state.loading = false;
      this.render();
      this.mountProductCards();
    }
  }

  render() {
    const { hotProducts, newProducts, loading, error } = this.state;

    this.html(`
      <div class="page page-home">
        <!-- Banner -->
        <section class="hero-section">
          <div class="hero-content">
            <h1 class="hero-title">智能导购，轻松购物</h1>
            <p class="hero-subtitle">AI 帮你找到最合适的商品</p>
            <div class="hero-actions">
              <a href="#/products" class="btn btn-primary btn-lg" data-link>
                浏览商品
              </a>
              <button class="btn btn-outline btn-lg" id="hero-chat-btn">
                🤖 咨询 AI
              </button>
            </div>
          </div>
        </section>

        <!-- 分类导航 -->
        <section class="section">
          <div class="container">
            <h2 class="section-title">商品分类</h2>
            <div class="category-grid">
              <a href="#/products?category=手机" class="category-card" data-link>
                <span class="category-icon">📱</span>
                <span class="category-name">手机</span>
              </a>
              <a href="#/products?category=电脑" class="category-card" data-link>
                <span class="category-icon">💻</span>
                <span class="category-name">电脑</span>
              </a>
              <a href="#/products?category=耳机" class="category-card" data-link>
                <span class="category-icon">🎧</span>
                <span class="category-name">耳机</span>
              </a>
              <a href="#/products?category=手表" class="category-card" data-link>
                <span class="category-icon">⌚</span>
                <span class="category-name">手表</span>
              </a>
              <a href="#/products?category=平板" class="category-card" data-link>
                <span class="category-icon">📋</span>
                <span class="category-name">平板</span>
              </a>
              <a href="#/products" class="category-card" data-link>
                <span class="category-icon">📦</span>
                <span class="category-name">全部</span>
              </a>
            </div>
          </div>
        </section>

        <!-- 热销商品 -->
        <section class="section">
          <div class="container">
            <div class="section-header">
              <h2 class="section-title">🔥 热销商品</h2>
              <a href="#/products?sort=sales" class="section-more" data-link>查看更多 →</a>
            </div>
            ${loading ? this.renderSkeleton() : `
              <div class="product-grid" id="hot-products">
                ${hotProducts.map((_, i) => `<div class="product-card-skeleton" data-index="${i}"></div>`).join('')}
              </div>
            `}
          </div>
        </section>

        <!-- 新品推荐 -->
        <section class="section">
          <div class="container">
            <div class="section-header">
              <h2 class="section-title">✨ 新品推荐</h2>
              <a href="#/products?sort=new" class="section-more" data-link>查看更多 →</a>
            </div>
            ${loading ? this.renderSkeleton() : `
              <div class="product-grid" id="new-products">
                ${newProducts.map((_, i) => `<div class="product-card-skeleton" data-index="${i}"></div>`).join('')}
              </div>
            `}
          </div>
        </section>

        <!-- AI 推荐 -->
        <section class="section ai-section">
          <div class="container">
            <div class="ai-promo">
              <div class="ai-promo-content">
                <h2>🤖 AI 智能导购</h2>
                <p>告诉 AI 你的需求，它会帮你找到最合适的商品</p>
                <div class="ai-promo-examples">
                  <span class="ai-example">"推荐一款 3000 元左右的手机"</span>
                  <span class="ai-example">"帮我比较 iPhone 和华为"</span>
                  <span class="ai-example">"有什么适合送礼的耳机？"</span>
                </div>
                <button class="btn btn-primary btn-lg" id="ai-promo-btn">
                  开始咨询
                </button>
              </div>
            </div>
          </div>
        </section>

        ${error ? `<div class="error-message">${error}</div>` : ''}
      </div>
    `);

    this.bindEvents();
  }

  renderSkeleton() {
    return `
      <div class="product-grid">
        ${Array(4).fill('').map(() => `
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
    // 挂载热销商品卡片
    const hotContainer = this.$('#hot-products');
    if (hotContainer) {
      hotContainer.innerHTML = '';
      this.state.hotProducts.forEach(product => {
        const card = document.createElement('div');
        hotContainer.appendChild(card);
        const component = new ProductCard(card, product);
        component.mount();
        this.productCards.push(component);
      });
    }

    // 挂载新品卡片
    const newContainer = this.$('#new-products');
    if (newContainer) {
      newContainer.innerHTML = '';
      this.state.newProducts.forEach(product => {
        const card = document.createElement('div');
        newContainer.appendChild(card);
        const component = new ProductCard(card, product);
        component.mount();
        this.productCards.push(component);
      });
    }
  }

  bindEvents() {
    // AI 咨询按钮
    this.on('click', '#hero-chat-btn, #ai-promo-btn', () => {
      window.dispatchEvent(new CustomEvent('chat:open'));
    });
  }

  onUnmount() {
    this.productCards.forEach(card => card.unmount());
    this.productCards = [];
  }
}
