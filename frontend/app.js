// ==================== 配置 ====================
const API_BASE = 'http://localhost:8000/api';
let token = localStorage.getItem('token');
let currentUser = null;
let currentPage = 'home';
let productsPage = 1;

// ==================== API 请求 ====================
async function api(method, path, data = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (token) options.headers['Authorization'] = `Bearer ${token}`;
    if (data) options.body = JSON.stringify(data);

    const resp = await fetch(API_BASE + path, options);
    const json = await resp.json();
    if (!resp.ok) throw new Error(json.detail || '请求失败');
    return json;
}

// ==================== 页面切换 ====================
function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const target = document.getElementById(`page-${page}`);
    if (target) target.classList.add('active');
    currentPage = page;

    switch (page) {
        case 'products': loadProducts(); break;
        case 'cart': loadCart(); break;
        case 'orders': loadOrders(); break;
        case 'admin': loadAdminStats(); break;
        case 'home': loadHotProducts(); break;
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ==================== Toast 提示 ====================
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.className = 'toast', 3000);
}

// ==================== 深色模式 ====================
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    document.getElementById('theme-icon').textContent = next === 'dark' ? '☀️' : '🌙';
}

function initTheme() {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    document.getElementById('theme-icon').textContent = saved === 'dark' ? '☀️' : '🌙';
}

// ==================== 用户认证 ====================
async function handleLogin(e) {
    e.preventDefault();
    try {
        const data = await api('POST', '/auth/login', {
            username: document.getElementById('login-username').value,
            password: document.getElementById('login-password').value
        });
        token = data.access_token;
        localStorage.setItem('token', token);
        await loadUserInfo();
        showToast('登录成功', 'success');
        showPage('home');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    try {
        await api('POST', '/auth/register', {
            username: document.getElementById('reg-username').value,
            email: document.getElementById('reg-email').value,
            password: document.getElementById('reg-password').value,
            phone: document.getElementById('reg-phone').value || undefined
        });
        showToast('注册成功，请登录', 'success');
        showPage('login');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function loadUserInfo() {
    if (!token) return;
    try {
        currentUser = await api('GET', '/auth/me');
        document.getElementById('nav-auth').classList.add('hidden');
        document.getElementById('nav-user').classList.remove('hidden');
        document.getElementById('username-display').textContent = currentUser.username;
        document.getElementById('nav-orders').classList.remove('hidden');
        if (currentUser.is_admin) document.getElementById('nav-admin').classList.remove('hidden');
    } catch {
        logout();
    }
}

function logout() {
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    document.getElementById('nav-auth').classList.remove('hidden');
    document.getElementById('nav-user').classList.add('hidden');
    document.getElementById('nav-orders').classList.add('hidden');
    document.getElementById('nav-admin').classList.add('hidden');
    showToast('已退出登录');
    showPage('home');
}

// ==================== 商品 ====================
async function loadProducts(page = 1) {
    const keyword = document.getElementById('search-keyword')?.value || '';
    try {
        const data = await api('GET', `/products?page=${page}&size=12&keyword=${encodeURIComponent(keyword)}`);
        productsPage = page;
        renderProducts(data, 'products-list', 'products-pagination');
    } catch {
        showToast('加载商品失败', 'error');
    }
}

async function loadHotProducts() {
    try {
        const data = await api('GET', '/products?page=1&size=4&sort_by=sales_count&sort_order=desc');
        renderProducts(data, 'hot-products', null);
    } catch { /* 静默失败 */ }
}

function renderProducts(data, gridId, paginationId) {
    const grid = document.getElementById(gridId);
    if (!grid) return;

    if (!data.items || data.items.length === 0) {
        grid.innerHTML = '<p class="empty-msg">暂无商品</p>';
        return;
    }

    grid.innerHTML = data.items.map(p => `
        <div class="product-card" onclick="showProductDetail(${p.id})">
            <div class="product-image">
                ${getProductEmoji(p.name)}
                ${p.brand ? `<span class="product-brand-tag">${p.brand}</span>` : ''}
                ${p.sales_count > 0 ? `<span class="product-sales-tag">已售 ${p.sales_count}</span>` : ''}
            </div>
            <div class="product-info">
                <div class="product-name">${p.name}</div>
                <div class="product-price-row">
                    <span class="product-price">¥${p.price}</span>
                    ${p.original_price && p.original_price > p.price ?
                        `<span class="product-original-price">¥${p.original_price}</span>` : ''}
                </div>
                <div class="product-meta">
                    <span>库存 ${p.stock}</span>
                    ${p.brand ? `<span>${p.brand}</span>` : ''}
                </div>
            </div>
        </div>
    `).join('');

    if (paginationId && data.pages > 1) {
        const pagination = document.getElementById(paginationId);
        let html = '';
        for (let i = 1; i <= data.pages; i++) {
            html += `<button class="${i === data.page ? 'active' : ''}" onclick="loadProducts(${i})">${i}</button>`;
        }
        pagination.innerHTML = html;
    }
}

function getProductEmoji(name) {
    const map = {
        '手机': '📱', 'phone': '📱', 'iPhone': '📱', '华为': '📱', '小米': '📱', '三星': '📱',
        '电脑': '💻', '笔记本': '💻', 'laptop': '💻', 'MacBook': '💻', '联想': '💻',
        '耳机': '🎧', 'AirPods': '🎧', '索尼': '🎧', '蓝牙': '🎧',
        '手表': '⌚', 'Watch': '⌚', 'watch': '⌚',
        '平板': '📱', 'iPad': '📱', 'MatePad': '📱',
        '相机': '📷', '电视': '📺', '冰箱': '🧊', '空调': '❄️',
        '鞋': '👟', '衣服': '👕', '包': '👜', '化妆': '💄',
    };
    for (const [key, emoji] of Object.entries(map)) {
        if (name.includes(key)) return emoji;
    }
    const emojis = ['📦', '🎁', '🛍️', '✨'];
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
    return emojis[Math.abs(hash) % emojis.length];
}

function searchProducts(e) {
    if (e.key === 'Enter') loadProducts();
}

async function showProductDetail(id) {
    try {
        const p = await api('GET', `/products/${id}`);
        const specsHtml = p.specs ? Object.entries(p.specs).map(([k, v]) =>
            `<div class="spec-item"><span class="spec-key">${k}</span><span>${v}</span></div>`
        ).join('') : '';

        document.getElementById('product-detail-content').innerHTML = `
            <div style="background:var(--bg-card);padding:30px;border-radius:var(--radius);border:1px solid var(--border);">
                <button class="btn btn-outline btn-sm" onclick="showPage('products')" style="margin-bottom:24px">← 返回列表</button>
                <div style="display:flex;gap:40px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:300px;">
                        <div class="product-image" style="height:350px;font-size:5rem;border-radius:var(--radius)">
                            ${getProductEmoji(p.name)}
                            ${p.brand ? `<span class="product-brand-tag">${p.brand}</span>` : ''}
                        </div>
                    </div>
                    <div style="flex:1;min-width:300px;">
                        <h1 style="margin-bottom:8px;font-size:1.6rem">${p.name}</h1>
                        ${p.brand ? `<p style="color:var(--text-secondary);margin-bottom:16px">品牌：${p.brand}</p>` : ''}
                        <p style="color:var(--text-secondary);margin-bottom:20px;line-height:1.8">${p.description || '暂无描述'}</p>
                        <div style="display:flex;align-items:baseline;gap:12px;margin-bottom:20px">
                            <span style="font-size:2rem;font-weight:700;color:var(--danger)">¥${p.price}</span>
                            ${p.original_price && p.original_price > p.price ?
                                `<span style="font-size:1.1rem;color:var(--text-secondary);text-decoration:line-through">¥${p.original_price}</span>
                                 <span style="background:var(--danger);color:white;padding:2px 8px;border-radius:4px;font-size:0.8rem">-${Math.round((1-p.price/p.original_price)*100)}%</span>` : ''}
                        </div>
                        <p style="margin-bottom:12px;color:var(--text-secondary)">库存: ${p.stock} | 销量: ${p.sales_count}</p>
                        ${specsHtml ? `<div style="margin-bottom:20px;background:var(--bg);padding:16px;border-radius:var(--radius-sm);">${specsHtml}</div>` : ''}
                        ${p.stock > 0 ? `
                            <div style="display:flex;gap:12px;align-items:center;margin-bottom:20px">
                                <label style="color:var(--text-secondary)">数量:</label>
                                <input type="number" id="detail-quantity" value="1" min="1" max="${p.stock}"
                                    style="width:80px;padding:10px;border:1.5px solid var(--border);border-radius:var(--radius-sm);background:var(--bg-input);color:var(--text);text-align:center">
                            </div>
                            <div style="display:flex;gap:10px">
                                <button class="btn btn-primary btn-lg" onclick="addToCartFromDetail(${p.id})">🛒 加入购物车</button>
                                <button class="btn btn-outline btn-lg" onclick="quickAsk('帮我查一下 ${p.name} 的库存')">🤖 问 AI</button>
                            </div>
                        ` : '<p style="color:var(--danger);font-size:1.1rem">已售罄</p>'}
                    </div>
                </div>
            </div>
        `;
        showPage('product-detail');
    } catch {
        showToast('商品不存在', 'error');
    }
}

async function addToCartFromDetail(productId) {
    const quantity = parseInt(document.getElementById('detail-quantity').value);
    await addToCart(productId, quantity);
}

async function addToCart(productId, quantity = 1) {
    if (!token) { showToast('请先登录', 'error'); showPage('login'); return; }
    try {
        await api('POST', '/cart', { product_id: productId, quantity });
        showToast('已加入购物车', 'success');
        updateCartCount();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==================== 购物车 ====================
async function loadCart() {
    if (!token) { showToast('请先登录', 'error'); showPage('login'); return; }
    try {
        const data = await api('GET', '/cart');
        renderCart(data);
    } catch {
        showToast('加载购物车失败', 'error');
    }
}

function renderCart(data) {
    const content = document.getElementById('cart-content');
    if (!data.items || data.items.length === 0) {
        content.innerHTML = '<p class="empty-msg">购物车为空，<a href="#" onclick="showPage(\'products\')">去逛逛</a></p>';
        return;
    }
    content.innerHTML = `
        ${data.items.map(item => `
            <div class="cart-item">
                <div class="cart-item-image">${getProductEmoji(item.product_name)}</div>
                <div class="cart-item-info">
                    <div class="cart-item-name">${item.product_name}</div>
                    <div class="cart-item-price">¥${item.product_price}</div>
                </div>
                <div class="cart-item-quantity">
                    <button onclick="updateCartItem(${item.product_id}, ${item.quantity - 1})">-</button>
                    <span>${item.quantity}</span>
                    <button onclick="updateCartItem(${item.product_id}, ${item.quantity + 1})">+</button>
                </div>
                <div class="cart-item-subtotal">¥${item.subtotal}</div>
                <span class="cart-item-remove" onclick="removeCartItem(${item.product_id})">✕</span>
            </div>
        `).join('')}
        <div class="cart-summary">
            <div class="cart-total">总计: <span>¥${data.total_amount}</span></div>
            <button class="btn btn-primary btn-lg" onclick="checkout()">去结算 (${data.selected_count} 件)</button>
        </div>
    `;
}

async function updateCartItem(productId, quantity) {
    try {
        await api('PUT', `/cart/${productId}`, { quantity });
        loadCart();
        updateCartCount();
    } catch (err) { showToast(err.message, 'error'); }
}

async function removeCartItem(productId) {
    try {
        await api('DELETE', `/cart/${productId}`);
        loadCart();
        updateCartCount();
        showToast('已删除');
    } catch (err) { showToast(err.message, 'error'); }
}

async function updateCartCount() {
    if (!token) return;
    try {
        const data = await api('GET', '/cart');
        document.getElementById('cart-count').textContent = data.selected_count || 0;
    } catch { /* 静默 */ }
}

async function checkout() {
    try {
        const cart = await api('GET', '/cart');
        const productIds = cart.items.map(i => i.product_id);
        await api('POST', '/orders', {
            address: { receiver: '默认收货人', phone: '13800138000', address: '默认地址' },
            cart_item_ids: productIds
        });
        showToast('订单创建成功', 'success');
        showPage('orders');
    } catch (err) { showToast(err.message, 'error'); }
}

// ==================== 订单 ====================
async function loadOrders() {
    if (!token) { showToast('请先登录', 'error'); showPage('login'); return; }
    try {
        const data = await api('GET', '/orders');
        renderOrders(data);
    } catch { showToast('加载订单失败', 'error'); }
}

function renderOrders(data) {
    const list = document.getElementById('orders-list');
    if (!data.items || data.items.length === 0) {
        list.innerHTML = '<p class="empty-msg">暂无订单</p>';
        return;
    }
    list.innerHTML = data.items.map(order => `
        <div class="order-card">
            <div class="order-header">
                <span class="order-no">订单号: ${order.order_no}</span>
                <span class="order-status status-${order.status}">${getStatusText(order.status)}</span>
            </div>
            <div class="order-items">
                ${order.items.map(item => `
                    <div class="order-item">
                        <span>${item.product_name} × ${item.quantity}</span>
                        <span>¥${item.subtotal}</span>
                    </div>
                `).join('')}
            </div>
            <div class="order-footer">
                <div class="order-total">总计: <span>¥${order.total_amount}</span></div>
                <div class="order-actions">${getOrderActions(order)}</div>
            </div>
        </div>
    `).join('');
}

function getStatusText(s) {
    return { pending:'待支付', paid:'已支付', shipped:'已发货', completed:'已完成', cancelled:'已取消', refunded:'已退款' }[s] || s;
}

function getOrderActions(order) {
    switch (order.status) {
        case 'pending':
            return `<button class="btn btn-primary btn-sm" onclick="payOrder(${order.id})">支付</button>
                    <button class="btn btn-outline btn-sm" onclick="cancelOrder(${order.id})">取消</button>`;
        case 'shipped':
            return `<button class="btn btn-success btn-sm" onclick="confirmOrder(${order.id})">确认收货</button>`;
        default: return '';
    }
}

async function payOrder(id) {
    try { await api('PUT', `/orders/${id}/pay`); showToast('支付成功', 'success'); loadOrders(); }
    catch (err) { showToast(err.message, 'error'); }
}

async function cancelOrder(id) {
    try { await api('PUT', `/orders/${id}/cancel`); showToast('订单已取消', 'success'); loadOrders(); }
    catch (err) { showToast(err.message, 'error'); }
}

async function confirmOrder(id) {
    try { await api('PUT', `/orders/${id}/confirm`); showToast('已确认收货', 'success'); loadOrders(); }
    catch (err) { showToast(err.message, 'error'); }
}

// ==================== 后台管理 ====================
function showAdminTab(tab, btn) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.admin-content').forEach(c => c.classList.remove('active'));
    if (btn) btn.classList.add('active');
    document.getElementById(`admin-${tab}`).classList.add('active');
    switch (tab) {
        case 'stats': loadAdminStats(); break;
        case 'orders': loadAdminOrders(); break;
        case 'users': loadAdminUsers(); break;
    }
}

async function loadAdminStats() {
    try {
        const [sales, users] = await Promise.all([
            api('GET', '/admin/stats/sales'),
            api('GET', '/admin/stats/users')
        ]);
        document.getElementById('stats-content').innerHTML = `
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-value">¥${sales.total_sales}</div><div class="stat-label">总销售额</div></div>
                <div class="stat-card"><div class="stat-value">${sales.total_orders}</div><div class="stat-label">总订单数</div></div>
                <div class="stat-card"><div class="stat-value">${users.total_users}</div><div class="stat-label">总用户数</div></div>
                <div class="stat-card"><div class="stat-value">${users.new_today}</div><div class="stat-label">今日新增</div></div>
            </div>
            <h3 style="margin-bottom:15px">订单状态分布</h3>
            <div style="display:flex;gap:10px;flex-wrap:wrap">
                ${Object.entries(sales.status_counts || {}).map(([s, c]) =>
                    `<span class="order-status status-${s}">${getStatusText(s)}: ${c}</span>`
                ).join('')}
            </div>
        `;
    } catch (err) {
        document.getElementById('stats-content').innerHTML = `<p class="empty-msg">加载失败: ${err.message}</p>`;
    }
}

async function loadAdminOrders() {
    try {
        const data = await api('GET', '/admin/orders');
        document.getElementById('admin-orders-content').innerHTML = data.items.map(order => `
            <div class="order-card">
                <div class="order-header">
                    <span class="order-no">#${order.order_no} | 用户ID: ${order.user_id}</span>
                    <span class="order-status status-${order.status}">${getStatusText(order.status)}</span>
                </div>
                <div class="order-footer">
                    <div class="order-total">¥${order.total_amount}</div>
                    <div class="order-actions">
                        ${order.status === 'paid' ? `<button class="btn btn-primary btn-sm" onclick="shipOrder(${order.id})">发货</button>` : ''}
                        ${['paid','shipped'].includes(order.status) ? `<button class="btn btn-danger btn-sm" onclick="refundOrder(${order.id})">退款</button>` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        document.getElementById('admin-orders-content').innerHTML = `<p class="empty-msg">加载失败</p>`;
    }
}

async function shipOrder(id) {
    try { await api('PUT', `/admin/orders/${id}/ship`); showToast('发货成功', 'success'); loadAdminOrders(); }
    catch (err) { showToast(err.message, 'error'); }
}

async function refundOrder(id) {
    try { await api('PUT', `/admin/orders/${id}/refund`); showToast('退款成功', 'success'); loadAdminOrders(); }
    catch (err) { showToast(err.message, 'error'); }
}

async function loadAdminUsers() {
    try {
        const data = await api('GET', '/admin/users');
        document.getElementById('admin-users-content').innerHTML = `
            <div style="overflow-x:auto">
                <table style="width:100%;background:var(--bg-card);border-radius:var(--radius);overflow:hidden;border:1px solid var(--border)">
                    <thead><tr style="background:var(--bg)">
                        <th style="padding:14px;text-align:left">ID</th>
                        <th style="padding:14px;text-align:left">用户名</th>
                        <th style="padding:14px;text-align:left">邮箱</th>
                        <th style="padding:14px;text-align:left">状态</th>
                        <th style="padding:14px;text-align:left">注册时间</th>
                    </tr></thead>
                    <tbody>${data.items.map(u => `
                        <tr style="border-top:1px solid var(--border)">
                            <td style="padding:14px">${u.id}</td>
                            <td style="padding:14px">${u.username} ${u.is_admin ? '<span style="color:var(--primary);font-size:0.8rem">(管理员)</span>' : ''}</td>
                            <td style="padding:14px">${u.email}</td>
                            <td style="padding:14px"><span style="color:${u.is_active ? 'var(--success)' : 'var(--danger)'}">${u.is_active ? '正常' : '禁用'}</span></td>
                            <td style="padding:14px">${new Date(u.created_at).toLocaleDateString()}</td>
                        </tr>
                    `).join('')}</tbody>
                </table>
            </div>
        `;
    } catch (err) {
        document.getElementById('admin-users-content').innerHTML = `<p class="empty-msg">加载失败</p>`;
    }
}

// ==================== AI 聊天 ====================
let chatSessionId = null;
let chatOpen = false;
let chatSending = false;

function toggleChat() {
    chatOpen = !chatOpen;
    const window = document.getElementById('ai-chat-window');
    const bubble = document.getElementById('ai-chat-bubble');
    const badge = document.getElementById('ai-badge');

    if (chatOpen) {
        window.classList.remove('chat-hidden');
        bubble.style.display = 'none';
        badge.style.display = 'none';
        document.getElementById('ai-chat-input').focus();
    } else {
        window.classList.add('chat-hidden');
        bubble.style.display = 'flex';
    }
}

function quickAsk(question) {
    if (!chatOpen) toggleChat();
    document.getElementById('ai-chat-input').value = question;
    sendChatMessage();
}

function sendOnEnter(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
    }
}

async function sendChatMessage() {
    if (chatSending) return;
    const input = document.getElementById('ai-chat-input');
    const message = input.value.trim();
    if (!message) return;

    if (!token) {
        showToast('请先登录后再咨询 AI', 'error');
        showPage('login');
        return;
    }

    input.value = '';
    chatSending = true;
    document.getElementById('chat-send-btn').disabled = true;

    // 移除欢迎区
    const welcome = document.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    // 添加用户消息
    appendMessage('user', message);

    // 显示打字指示器
    showTyping();

    try {
        const data = await api('POST', '/agent/chat', {
            message: message,
            session_id: chatSessionId
        });

        chatSessionId = data.session_id;
        hideTyping();

        // 添加 AI 回复
        appendMessage('ai', data.reply, data.tool_calls);

        // 如果需要确认
        if (data.needs_confirm) {
            appendConfirm(data.confirm_action, data.confirm_args, data.confirm_message);
        }
    } catch (err) {
        hideTyping();
        appendMessage('ai', `抱歉，出了点问题：${err.message}`);
    } finally {
        chatSending = false;
        document.getElementById('chat-send-btn').disabled = false;
    }
}

async function sendConfirm(approved) {
    if (!chatSessionId) return;

    showTyping();
    try {
        const data = await api('POST', '/agent/confirm', {
            session_id: chatSessionId,
            approved: approved
        });

        hideTyping();
        appendMessage('ai', data.reply, data.tool_calls);

        if (data.needs_confirm) {
            appendConfirm(data.confirm_action, data.confirm_args, data.confirm_message);
        }
    } catch (err) {
        hideTyping();
        appendMessage('ai', `操作失败：${err.message}`);
    }
}

function appendMessage(role, content, toolCalls = null) {
    const container = document.getElementById('ai-chat-messages');
    const now = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

    const msg = document.createElement('div');
    msg.className = `chat-msg ${role}`;

    let toolCallsHtml = '';
    if (toolCalls && toolCalls.length > 0) {
        toolCallsHtml = '<div class="tool-calls">' + toolCalls.map(tc => `
            <div class="tool-call-item">
                <div class="tool-call-name">🔧 ${tc.tool}</div>
                ${tc.result ? `<div class="tool-call-result">${typeof tc.result === 'object' ? JSON.stringify(tc.result).slice(0, 100) : String(tc.result).slice(0, 100)}</div>` : ''}
            </div>
        `).join('') + '</div>';
    }

    msg.innerHTML = `
        <div class="chat-msg-avatar">${role === 'ai' ? '🤖' : '👤'}</div>
        <div>
            <div class="chat-msg-bubble">${formatContent(content)}${toolCallsHtml}</div>
            <div class="chat-msg-time">${now}</div>
        </div>
    `;

    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

function appendConfirm(action, args, message) {
    const container = document.getElementById('ai-chat-messages');
    const confirm = document.createElement('div');
    confirm.className = 'chat-msg ai';
    confirm.innerHTML = `
        <div class="chat-msg-avatar">🤖</div>
        <div>
            <div class="chat-confirm">
                <div class="chat-confirm-msg">${message || '确认执行此操作？'}</div>
                <div class="chat-confirm-actions">
                    <button class="btn-confirm" onclick="this.closest('.chat-msg').remove(); sendConfirm(true)">✅ 确认</button>
                    <button class="btn-cancel" onclick="this.closest('.chat-msg').remove(); sendConfirm(false)">❌ 取消</button>
                </div>
            </div>
        </div>
    `;
    container.appendChild(confirm);
    container.scrollTop = container.scrollHeight;
}

function formatContent(text) {
    if (!text) return '';
    // 简单 markdown：**bold**, `code`, 换行
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.*?)`/g, '<code style="background:var(--border);padding:1px 4px;border-radius:3px;font-size:0.85em">$1</code>')
        .replace(/\n/g, '<br>');
}

function showTyping() {
    const container = document.getElementById('ai-chat-messages');
    const existing = container.querySelector('.typing-indicator');
    if (existing) return;

    const typing = document.createElement('div');
    typing.className = 'typing-indicator';
    typing.innerHTML = `
        <div class="chat-msg-avatar" style="background:var(--primary-light)">🤖</div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    container.appendChild(typing);
    container.scrollTop = container.scrollHeight;
}

function hideTyping() {
    const typing = document.querySelector('.typing-indicator');
    if (typing) typing.remove();
}

async function clearChatHistory() {
    if (chatSessionId && token) {
        try { await api('DELETE', `/agent/history/${chatSessionId}`); } catch { /* 静默 */ }
    }
    chatSessionId = null;
    document.getElementById('ai-chat-messages').innerHTML = `
        <div class="chat-welcome">
            <div class="welcome-icon">🤖</div>
            <h3>你好！我是 AI 导购助手</h3>
            <p>我可以帮你搜索商品、查看详情、校验库存、计算价格，甚至帮你加购！</p>
            <div class="quick-asks">
                <button onclick="quickAsk('推荐一款2000左右的手机')">📱 推荐手机</button>
                <button onclick="quickAsk('有什么好的蓝牙耳机？')">🎧 蓝牙耳机</button>
                <button onclick="quickAsk('学生买什么笔记本好？')">💻 学生笔记本</button>
            </div>
        </div>
    `;
    showToast('对话已清除');
}

// ==================== 初始化 ====================
async function init() {
    initTheme();
    if (token) {
        await loadUserInfo();
        updateCartCount();
    }
    loadHotProducts();
}

init();
