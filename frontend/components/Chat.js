/**
 * Chat 组件
 *
 * AI 智能导购聊天窗口，支持多轮对话、工具调用、确认操作。
 */

import { Component } from '../core/component.js';
import { store } from '../core/store.js';
import { aiApi } from '../core/api.js';
import { Toast } from './Toast.js';

export class Chat extends Component {
  constructor(container) {
    super(container);
    this.state = {
      open: false,
      messages: [],
      input: '',
      sending: false,
      sessionId: null,
      needsConfirm: false,
      confirmData: null,
    };

    // 监听事件
    window.addEventListener('chat:open', (e) => {
      this.open();
      if (e.detail?.question) {
        this.state.input = e.detail.question;
        this.render();
        this.sendMessage();
      }
    });

    window.addEventListener('chat:close', () => this.close());
  }

  render() {
    const { open, messages, input, sending, needsConfirm, confirmData } = this.state;

    this.html(`
      <!-- 聊天气泡 -->
      <div class="chat-bubble ${open ? 'hidden' : ''}" id="chat-bubble">
        <span class="chat-bubble-icon">🤖</span>
        <span class="chat-bubble-text">有什么可以帮您？</span>
      </div>

      <!-- 聊天窗口 -->
      <div class="chat-window ${open ? 'active' : ''}" id="chat-window">
        <!-- 头部 -->
        <div class="chat-header">
          <div class="chat-header-info">
            <span class="chat-avatar">🤖</span>
            <div>
              <span class="chat-title">AI 导购助手</span>
              <span class="chat-status">在线</span>
            </div>
          </div>
          <div class="chat-header-actions">
            <button class="btn-icon" id="chat-clear" title="清空对话">
              <span>🗑️</span>
            </button>
            <button class="btn-icon" id="chat-close" title="关闭">
              <span>✕</span>
            </button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div class="chat-messages" id="chat-messages">
          ${messages.length === 0 ? `
            <div class="chat-welcome">
              <div class="welcome-icon">🤖</div>
              <h3>你好！我是 AI 导购助手</h3>
              <p>可以帮你：</p>
              <div class="welcome-tags">
                <button class="welcome-tag" data-question="推荐一些热销商品">🔥 推荐热销</button>
                <button class="welcome-tag" data-question="帮我看一下有什么手机">📱 查找手机</button>
                <button class="welcome-tag" data-question="帮我比较一下价格">💰 比较价格</button>
              </div>
            </div>
          ` : messages.map(msg => this.renderMessage(msg)).join('')}

          ${needsConfirm && confirmData ? `
            <div class="chat-confirm">
              <div class="confirm-message">${confirmData.message || '确认执行此操作？'}</div>
              <div class="confirm-actions">
                <button class="btn btn-primary btn-sm" id="confirm-yes">✅ 确认</button>
                <button class="btn btn-outline btn-sm" id="confirm-no">❌ 取消</button>
              </div>
            </div>
          ` : ''}

          ${sending ? `
            <div class="chat-typing">
              <span class="typing-dot">.</span>
              <span class="typing-dot">.</span>
              <span class="typing-dot">.</span>
            </div>
          ` : ''}
        </div>

        <!-- 输入框 -->
        <div class="chat-input-area">
          <textarea
            class="chat-input"
            id="chat-input"
            placeholder="输入你的问题..."
            rows="1"
            ${sending ? 'disabled' : ''}
          >${input}</textarea>
          <button class="btn btn-primary" id="chat-send" ${sending ? 'disabled' : ''}>
            <span>发送</span>
          </button>
        </div>
      </div>
    `);

    this.bindEvents();
    this.scrollToBottom();
  }

  renderMessage(msg) {
    const isUser = msg.role === 'user';
    const time = new Date(msg.timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });

    return `
      <div class="chat-msg ${isUser ? 'user' : 'ai'}">
        <div class="chat-msg-avatar">${isUser ? '👤' : '🤖'}</div>
        <div class="chat-msg-content">
          <div class="chat-msg-bubble">
            ${this.formatMessage(msg.content)}
            ${msg.toolCalls ? this.renderToolCalls(msg.toolCalls) : ''}
          </div>
          <div class="chat-msg-time">${time}</div>
        </div>
      </div>
    `;
  }

  formatMessage(content) {
    if (!content) return '';
    // 简单的 Markdown 支持
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }

  renderToolCalls(toolCalls) {
    if (!toolCalls || toolCalls.length === 0) return '';
    return `
      <div class="tool-calls">
        ${toolCalls.map(tc => `
          <div class="tool-call">
            <span class="tool-icon">🔧</span>
            <span class="tool-name">${tc.name}</span>
            <span class="tool-status ${tc.success ? 'success' : 'error'}">
              ${tc.success ? '✓' : '✗'}
            </span>
          </div>
        `).join('')}
      </div>
    `;
  }

  bindEvents() {
    // 打开聊天
    this.on('click', '#chat-bubble', () => this.open());

    // 关闭聊天
    this.on('click', '#chat-close', () => this.close());

    // 清空对话
    this.on('click', '#chat-clear', () => {
      this.state.messages = [];
      this.state.sessionId = null;
      this.render();
    });

    // 发送消息
    this.on('click', '#chat-send', () => this.sendMessage());

    // Enter 发送
    this.on('keydown', '#chat-input', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // 自动调整输入框高度
    this.on('input', '#chat-input', (e) => {
      e.target.style.height = 'auto';
      e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
      this.state.input = e.target.value;
    });

    // 快捷问题
    this.on('click', '[data-question]', (e) => {
      this.state.input = e.target.dataset.question;
      this.sendMessage();
    });

    // 确认操作
    this.on('click', '#confirm-yes', () => this.sendConfirm(true));
    this.on('click', '#confirm-no', () => this.sendConfirm(false));
  }

  open() {
    this.state.open = true;
    this.render();
    setTimeout(() => {
      this.$('#chat-input')?.focus();
    }, 100);
  }

  close() {
    this.state.open = false;
    this.render();
  }

  async sendMessage() {
    const message = this.state.input.trim();
    if (!message || this.state.sending) return;

    if (!store.isLoggedIn()) {
      Toast.warning('请先登录后再咨询 AI');
      return;
    }

    // 添加用户消息
    this.state.messages.push({
      role: 'user',
      content: message,
      timestamp: Date.now(),
    });
    this.state.input = '';
    this.state.sending = true;
    this.render();

    try {
      const data = await aiApi.chat({
        message,
        session_id: this.state.sessionId,
      });

      this.state.sessionId = data.session_id;

      // 添加 AI 回复
      this.state.messages.push({
        role: 'ai',
        content: data.reply,
        timestamp: Date.now(),
        toolCalls: data.tool_calls,
      });

      // 检查是否需要确认
      if (data.needs_confirm) {
        this.state.needsConfirm = true;
        this.state.confirmData = {
          action: data.confirm_action,
          args: data.confirm_args,
          message: data.confirm_message,
        };
      }
    } catch (error) {
      this.state.messages.push({
        role: 'ai',
        content: `抱歉，出了点问题：${error.message}`,
        timestamp: Date.now(),
      });
    } finally {
      this.state.sending = false;
      this.render();
    }
  }

  async sendConfirm(approved) {
    if (!this.state.sessionId) return;

    this.state.needsConfirm = false;
    this.state.confirmData = null;
    this.state.sending = true;
    this.render();

    try {
      const data = await aiApi.confirm({
        session_id: this.state.sessionId,
        approved,
      });

      this.state.messages.push({
        role: 'ai',
        content: data.reply,
        timestamp: Date.now(),
        toolCalls: data.tool_calls,
      });
    } catch (error) {
      this.state.messages.push({
        role: 'ai',
        content: `操作失败：${error.message}`,
        timestamp: Date.now(),
      });
    } finally {
      this.state.sending = false;
      this.render();
    }
  }

  scrollToBottom() {
    const messages = this.$('#chat-messages');
    if (messages) {
      messages.scrollTop = messages.scrollHeight;
    }
  }
}
