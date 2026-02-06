// ==================== API Integration Script ====================
// 在 </body> 前添加此脚本

// API 配置
const API_BASE = '/api/v1';

// 工具函数：从 localStorage 获取 Token
function getAuthToken() {
    return localStorage.getItem('auth_token');
}

// 工具函数：检查认证状态
function checkAuth() {
    const token = getAuthToken();
    if (!token) {
        // 没有 Token，跳转到登录页
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

// 工具函数：带认证的 fetch 请求
async function authenticatedFetch(url, options = {}) {
    const token = getAuthToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
    };

    const response = await fetch(url, { ...options, headers });

    // 如果返回 401，跳转到登录页
    if (response.status === 401) {
        localStorage.removeItem('auth_token');
        window.location.href = '/login.html';
        throw new Error('Unauthorized');
    }

    return response;
}

// ==================== 数据获取函数 ====================

// 获取仪表板统计数据
async function getDashboardStats() {
    try {
        const response = await authenticatedFetch(`${API_BASE}/admin/dashboard`);
        if (!response.ok) throw new Error('Failed to fetch dashboard stats');
        return await response.json();
    } catch (error) {
        console.error('获取仪表板数据失败:', error);
        return null;
    }
}

// 获取节点列表
async function getNodes() {
    try {
        const response = await authenticatedFetch(`${API_BASE}/nodes`);
        if (!response.ok) throw new Error('Failed to fetch nodes');
        return await response.json();
    } catch (error) {
        console.error('获取节点列表失败:', error);
        return [];
    }
}

// ==================== UI 更新函数 ====================

// 更新仪表板统计数据
function updateDashboardStats(data) {
    if (!data) return;

    // 更新在线用户数 (行 133)
    const onlineUsersElement = document.querySelector('[data-stat="online-users"]');
    if (onlineUsersElement && data.online_users !== undefined) {
        onlineUsersElement.textContent = data.online_users.toLocaleString();
    }

    // 更新总流量 (行 158)
    const totalTrafficElement = document.querySelector('[data-stat="total-traffic"]');
    if (totalTrafficElement && data.total_traffic !== undefined) {
        totalTrafficElement.textContent = `${data.total_traffic} TB/s`;
    }

    // 更新总收入 (行 119)
    const revenueElement = document.querySelector('[data-stat="revenue"]');
    if (revenueElement && data.revenue !== undefined) {
        revenueElement.textContent = `$${data.revenue.toLocaleString()}`;
    }

    // 更新节点健康度 (行 144)
    const nodeHealthElement = document.querySelector('[data-stat="node-health"]');
    if (nodeHealthElement && data.node_health !== undefined) {
        nodeHealthElement.textContent = `${data.node_health}%`;
    }
}

// 渲染全局节点列表
function renderGlobalNodes(nodes) {
    if (!nodes || nodes.length === 0) return;

    // 找到节点容器 (行 251)
    const container = document.querySelector('[data-nodes-grid]');
    if (!container) return;

    // 清空现有内容
    container.innerHTML = '';

    // 按区域分组节点
    const nodesByRegion = {};
    nodes.forEach(node => {
        const region = node.region || node.name.split('-')[0] || 'Other';
        if (!nodesByRegion[region]) {
            nodesByRegion[region] = [];
        }
        nodesByRegion[region].push(node);
    });

    // 为每个区域渲染一个卡片
    Object.entries(nodesByRegion).forEach(([region, regionNodes]) => {
        // 计算区域平均健康度
        const avgHealth = regionNodes.reduce((sum, node) => {
            // 假设 ai_score 代表健康度，或者使用 load_factor 反向计算
            const health = node.ai_score ? node.ai_score * 100 : (1 - node.load_factor) * 100;
            return sum + health;
        }, 0) / regionNodes.length;

        // 确定健康度颜色
        let healthColor = 'green';
        if (avgHealth < 70) healthColor = 'red';
        else if (avgHealth < 90) healthColor = 'orange';

        // 检查是否有高 AI 评分的节点（✨ 推荐）
        const hasRecommendedNode = regionNodes.some(node => node.ai_score > 0.8);

        // 创建节点卡片
        const nodeCard = document.createElement('div');
        nodeCard.className = `flex flex-col items-center p-4 rounded-xl border border-[#e7ebf3] dark:border-white/10 bg-gray-50 dark:bg-white/5 relative ${hasRecommendedNode ? 'ring-2 ring-primary' : ''}`;

        nodeCard.innerHTML = `
            ${hasRecommendedNode ? '<div class="absolute -top-2 -right-2 bg-primary text-white text-xs font-bold px-2 py-1 rounded-full">✨ 推荐</div>' : ''}
            <p class="text-xs font-bold text-[#4c669a] uppercase mb-2">${region}</p>
            <p class="text-lg font-bold text-[#0d121b] dark:text-white">${Math.round(avgHealth)}%</p>
            <div class="w-full bg-gray-200 dark:bg-white/10 h-1.5 rounded-full mt-2 overflow-hidden">
                <div class="bg-${healthColor}-500 h-full" style="width: ${avgHealth}%"></div>
            </div>
            <p class="text-[10px] text-[#4c669a] mt-2">${regionNodes.length} node${regionNodes.length > 1 ? 's' : ''}</p>
        `;

        container.appendChild(nodeCard);
    });
}

// ==================== 主初始化函数 ====================

async function initializeDashboard() {
    console.log('🚀 初始化 VPN 管理面板...');

    // 1. 检查认证
    if (!checkAuth()) {
        return; // 如果未认证，会自动跳转
    }

    // 2. 显示加载状态（可选）
    console.log('📊 加载仪表板数据...');

    try {
        // 3. 并行获取数据
        const [dashboardStats, nodes] = await Promise.all([
            getDashboardStats(),
            getNodes()
        ]);

        // 4. 更新 UI
        if (dashboardStats) {
            updateDashboardStats(dashboardStats);
            console.log('✅ 仪表板数据更新完成');
        }

        if (nodes && nodes.length > 0) {
            renderGlobalNodes(nodes);
            console.log(`✅ 渲染 ${nodes.length} 个节点`);
        }

    } catch (error) {
        console.error('❌ 初始化失败:', error);
        // 可以显示错误提示给用户
    }
}

// ==================== 页面加载事件 ====================

document.addEventListener('DOMContentLoaded', function () {
    initializeDashboard();

    // 可选：每 30 秒自动刷新数据
    setInterval(async () => {
        console.log('🔄 自动刷新数据...');
        const [dashboardStats, nodes] = await Promise.all([
            getDashboardStats(),
            getNodes()
        ]);
        if (dashboardStats) updateDashboardStats(dashboardStats);
        if (nodes) renderGlobalNodes(nodes);
    }, 30000); // 30 秒
});
