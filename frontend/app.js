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
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    if (data) {
        options.body = JSON.stringify(data);
    }
    try {
        const resp = await fetch(API_BASE + path, options);
        const json = await resp.json();
        if (!resp.ok) {
            throw new Error(json.detail || '请求失败');
        }
        return json;
    } catch (err) {
        throw err;
    }
}

// ==================== 页面切换 ====================
function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`page-${page}`).classList.add('active');
    currentPage = page;

    // 加载页面数据
    switch (page) {
        case 'products': loadProducts(); break;
        case 'cart': loadCart(); break;
        case 'orders': loadOrders(); break;
        case 'admin': loadAdminStats(); break;
    }
}

// ==================== Toast 提示 ====================
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.className = 'toast', 3000);
}

// ==================== 用户认证 ====================
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    try {
        const data = await api('POST', '/auth/login', { username, password });
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
    const data = {
        username: document.getElementById('reg-username').value,
        email: document.getElementById('reg-email').value,
        password: document.getElementById('reg-password').value,
        phone: document.getElementById('reg-phone').value || undefined
    };
    try {
        await api('POST', '/auth/register', data);
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
        document.getElementById('nav-auth').style.display = 'none';
        document.getElementById('nav-user').style.display = 'inline';
        document.getElementById('username-display').textContent = currentUser.username;
        document.getElementById('nav-orders').style.display = 'inline';
        if (currentUser.is_admin) {
            document.getElementById('nav-admin').style.display = 'inline';
        }
    } catch (err) {
        logout();
    }
}

function logout() {
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    document.getElementById('nav-auth').style.display = 'inline';
    document.getElementById('nav-user').style.display = 'none';
    document.getElementById('nav-orders').style.display = 'none';
    document.getElementById('nav-admin').style.display = 'none';
    showToast('已退出登录');
    showPage('home');
}

// ==================== 商品 ====================
async function loadProducts(page = 1) {
    const keyword = document.getElementById('search-keyword')?.value || '';
    try {
        const data = await api('GET', `/products?page=${page}&size=12&keyword=${keyword}`);
        productsPage = page;
        renderProducts(data);
    } catch (err) {
        showToast('加载商品失败', 'error');
    }
}

function renderProducts(data) {
    const grid = document.getElementById('products-list');
    grid.innerHTML = data.items.map(p => `
        <div class="product-card" onclick="showProductDetail(${p.id})">
            <div class="product-image">${getProductEmoji(p.name)}</div>
            <div class="product-info">
                <div class="product-name">${p.name}</div>
                <div class="product-price">CNY ${p.price}</div>
                <div class="product-stock">库存: ${p.stock}</div>
            </div>
        </div>
    `).join('');

    // 分页
    const pagination = document.getElementById('products-pagination');
    let pagesHtml = '';
    for (let i = 1; i <= data.pages; i++) {
        pagesHtml += `<button class="${i === data.page ? 'active' : ''}" onclick="loadProducts(${i})">${i}</button>`;
    }
    pagination.innerHTML = pagesHtml;
}

function getProductEmoji(name) {
    const emojis = ['📚', '💻', '🎮', '📱', '🎧', '⌚', '📷', '🖥️'];
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
        document.getElementById('product-detail-content').innerHTML = `
            <div style="background:white;padding:30px;border-radius:12px;">
                <button class="btn btn-outline" onclick="showPage('products')" style="margin-bottom:20px">返回列表</button>
                <div style="display:flex;gap:40px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:300px;">
                        <div class="product-image" style="height:300px;font-size:5rem;border-radius:12px">${getProductEmoji(p.name)}</div>
                    </div>
                    <div style="flex:1;min-width:300px;">
                        <h1 style="margin-bottom:15px">${p.name}</h1>
                        <p style="color:var(--gray-500);margin-bottom:20px">${p.description || '暂无描述'}</p>
                        <div class="product-price" style="font-size:2rem;margin-bottom:20px">CNY ${p.price}</div>
                        <p style="margin-bottom:20px">库存: ${p.stock} | 销量: ${p.sales_count}</p>
                        ${p.stock > 0 ? `
                            <div style="display:flex;gap:10px;align-items:center;margin-bottom:20px">
                                <label>数量:</label>
                                <input type="number" id="detail-quantity" value="1" min="1" max="${p.stock}" style="width:80px;padding:8px;border:2px solid var(--gray-200);border-radius:8px">
                            </div>
                            <button class="btn btn-primary" onclick="addToCartFromDetail(${p.id})">加入购物车</button>
                        ` : '<p style="color:var(--danger)">已售罄</p>'}
                    </div>
                </div>
            </div>
        `;
        showPage('product-detail');
    } catch (err) {
        showToast('商品不存在', 'error');
    }
}

async function addToCartFromDetail(productId) {
    const quantity = parseInt(document.getElementById('detail-quantity').value);
    await addToCart(productId, quantity);
}

async function addToCart(productId, quantity = 1) {
    if (!token) {
        showToast('请先登录', 'error');
        showPage('login');
        return;
    }
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
    if (!token) {
        showToast('请先登录', 'error');
        showPage('login');
        return;
    }
    try {
        const data = await api('GET', '/cart');
        renderCart(data);
    } catch (err) {
        showToast('加载购物车失败', 'error');
    }
}

function renderCart(data) {
    const content = document.getElementById('cart-content');
    if (!data.items || data.items.length === 0) {
        content.innerHTML = '<p class="empty-msg">购物车为空</p>';
        return;
    }
    content.innerHTML = `
        ${data.items.map(item => `
            <div class="cart-item">
                <div class="cart-item-image">${getProductEmoji(item.product_name)}</div>
                <div class="cart-item-info">
                    <div class="cart-item-name">${item.product_name}</div>
                    <div class="cart-item-price">CNY ${item.product_price}</div>
                </div>
                <div class="cart-item-quantity">
                    <button onclick="updateCartItem(${item.product_id}, ${item.quantity - 1})">-</button>
                    <span>${item.quantity}</span>
                    <button onclick="updateCartItem(${item.product_id}, ${item.quantity + 1})">+</button>
                </div>
                <div class="cart-item-subtotal">CNY ${item.subtotal}</div>
                <span class="cart-item-remove" onclick="removeCartItem(${item.product_id})">删除</span>
            </div>
        `).join('')}
        <div class="cart-summary">
            <div class="cart-total">总计: <span>CNY ${data.total_amount}</span></div>
            <button class="btn btn-primary" onclick="checkout()">去结算 (${data.selected_count} 件)</button>
        </div>
    `;
}

async function updateCartItem(productId, quantity) {
    try {
        await api('PUT', `/cart/${productId}`, { quantity });
        loadCart();
        updateCartCount();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function removeCartItem(productId) {
    try {
        await api('DELETE', `/cart/${productId}`);
        loadCart();
        updateCartCount();
        showToast('已删除');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function updateCartCount() {
    if (!token) return;
    try {
        const data = await api('GET', '/cart');
        document.getElementById('cart-count').textContent = data.selected_count || 0;
    } catch (err) {}
}

async function checkout() {
    try {
        const cart = await api('GET', '/cart');
        const productIds = cart.items.map(i => i.product_id);
        const order = await api('POST', '/orders', {
            address: { receiver: '默认收货人', phone: '13800138000', address: '默认地址' },
            cart_item_ids: productIds
        });
        showToast('订单创建成功', 'success');
        showPage('orders');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==================== 订单 ====================
async function loadOrders() {
    if (!token) {
        showToast('请先登录', 'error');
        showPage('login');
        return;
    }
    try {
        const data = await api('GET', '/orders');
        renderOrders(data);
    } catch (err) {
        showToast('加载订单失败', 'error');
    }
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
                        <span>${item.product_name} x${item.quantity}</span>
                        <span>CNY ${item.subtotal}</span>
                    </div>
                `).join('')}
            </div>
            <div class="order-footer">
                <div class="order-total">总计: <span>CNY ${order.total_amount}</span></div>
                <div class="order-actions">
                    ${getOrderActions(order)}
                </div>
            </div>
        </div>
    `).join('');
}

function getStatusText(status) {
    const map = {
        pending: '待支付',
        paid: '已支付',
        shipped: '已发货',
        completed: '已完成',
        cancelled: '已取消',
        refunded: '已退款'
    };
    return map[status] || status;
}

function getOrderActions(order) {
    switch (order.status) {
        case 'pending':
            return `<button class="btn btn-primary btn-sm" onclick="payOrder(${order.id})">支付</button>
                    <button class="btn btn-outline btn-sm" onclick="cancelOrder(${order.id})">取消</button>`;
        case 'shipped':
            return `<button class="btn btn-success btn-sm" onclick="confirmOrder(${order.id})">确认收货</button>`;
        default:
            return '';
    }
}

async function payOrder(id) {
    try {
        await api('PUT', `/orders/${id}/pay`);
        showToast('支付成功', 'success');
        loadOrders();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function cancelOrder(id) {
    try {
        await api('PUT', `/orders/${id}/cancel`);
        showToast('订单已取消', 'success');
        loadOrders();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function confirmOrder(id) {
    try {
        await api('PUT', `/orders/${id}/confirm`);
        showToast('已确认收货', 'success');
        loadOrders();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ==================== 后台管理 ====================
function showAdminTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.admin-content').forEach(c => c.classList.remove('active'));
    event.target.classList.add('active');
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
                <div class="stat-card">
                    <div class="stat-value">CNY ${sales.total_sales}</div>
                    <div class="stat-label">总销售额</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${sales.total_orders}</div>
                    <div class="stat-label">总订单数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${users.total_users}</div>
                    <div class="stat-label">总用户数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${users.new_today}</div>
                    <div class="stat-label">今日新增</div>
                </div>
            </div>
            <h3 style="margin-bottom:15px">订单状态分布</h3>
            <div style="display:flex;gap:10px;flex-wrap:wrap">
                ${Object.entries(sales.status_counts || {}).map(([status, count]) => `
                    <span class="order-status status-${status}">${getStatusText(status)}: ${count}</span>
                `).join('')}
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
                    <span class="order-no">订单号: ${order.order_no} | 用户ID: ${order.user_id}</span>
                    <span class="order-status status-${order.status}">${getStatusText(order.status)}</span>
                </div>
                <div class="order-footer">
                    <div class="order-total">总计: <span>CNY ${order.total_amount}</span></div>
                    <div class="order-actions">
                        ${order.status === 'paid' ? `<button class="btn btn-primary btn-sm" onclick="shipOrder(${order.id})">发货</button>` : ''}
                        ${['paid', 'shipped'].includes(order.status) ? `<button class="btn btn-danger btn-sm" onclick="refundOrder(${order.id})">退款</button>` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        document.getElementById('admin-orders-content').innerHTML = `<p class="empty-msg">加载失败: ${err.message}</p>`;
    }
}

async function shipOrder(id) {
    try {
        await api('PUT', `/admin/orders/${id}/ship`);
        showToast('发货成功', 'success');
        loadAdminOrders();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function refundOrder(id) {
    try {
        await api('PUT', `/admin/orders/${id}/refund`);
        showToast('退款成功', 'success');
        loadAdminOrders();
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function loadAdminUsers() {
    try {
        const data = await api('GET', '/admin/users');
        document.getElementById('admin-users-content').innerHTML = `
            <table style="width:100%;background:white;border-radius:12px;overflow:hidden">
                <thead>
                    <tr style="background:var(--gray-100)">
                        <th style="padding:15px;text-align:left">ID</th>
                        <th style="padding:15px;text-align:left">用户名</th>
                        <th style="padding:15px;text-align:left">邮箱</th>
                        <th style="padding:15px;text-align:left">状态</th>
                        <th style="padding:15px;text-align:left">注册时间</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.items.map(u => `
                        <tr style="border-bottom:1px solid var(--gray-200)">
                            <td style="padding:15px">${u.id}</td>
                            <td style="padding:15px">${u.username} ${u.is_admin ? '(管理员)' : ''}</td>
                            <td style="padding:15px">${u.email}</td>
                            <td style="padding:15px">
                                <span style="color:${u.is_active ? 'var(--success)' : 'var(--danger)'}">
                                    ${u.is_active ? '正常' : '禁用'}
                                </span>
                            </td>
                            <td style="padding:15px">${new Date(u.created_at).toLocaleDateString()}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    } catch (err) {
        document.getElementById('admin-users-content').innerHTML = `<p class="empty-msg">加载失败: ${err.message}</p>`;
    }
}

// ==================== 初始化 ====================
async function init() {
    if (token) {
        await loadUserInfo();
        updateCartCount();
    }
}

init();
