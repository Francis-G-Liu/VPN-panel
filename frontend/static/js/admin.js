// AI VPN 管理后台 JavaScript

const API_BASE = '/api/v1';

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 AI VPN 管理系统已加载');
    refreshStats();
});

// 刷新统计数据
async function refreshStats() {
    try {
        // 调用 API 获取统计数据
        const response = await fetch(`${API_BASE}/stats/dashboard`);

        if (!response.ok) {
            console.warn('统计数据暂时不可用');
            return;
        }

        const data = await response.json();

        // 更新页面显示
        document.getElementById('total-users').textContent = data.total_users || 0;
        document.getElementById('total-nodes').textContent = data.total_nodes || 0;
        document.getElementById('active-connections').textContent = data.active_connections || 0;
        document.getElementById('total-traffic').textContent = (data.total_traffic || 0).toFixed(2);

        console.log('✅ 统计数据已更新');
    } catch (error) {
        console.error('❌ 获取统计数据失败:', error);
    }
}

// 加载用户列表
async function loadUsers() {
    try {
        const response = await fetch(`${API_BASE}/users`);
        if (!response.ok) throw new Error('获取用户列表失败');

        const users = await response.json();
        console.log('📊 用户列表:', users);
        alert(`当前用户数: ${users.length}`);
    } catch (error) {
        console.error('❌ 加载用户失败:', error);
        alert('API 尚未实现，请先创建用户相关路由');
    }
}

// 加载节点列表
async function loadNodes() {
    try {
        const response = await fetch(`${API_BASE}/nodes`);
        if (!response.ok) throw new Error('获取节点列表失败');

        const nodes = await response.json();
        console.log('📊 节点列表:', nodes);
        alert(`当前节点数: ${nodes.length}`);
    } catch (error) {
        console.error('❌ 加载节点失败:', error);
        alert('API 尚未实现，请先创建节点相关路由');
    }
}

// 工具函数：格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 工具函数：格式化流量
function formatTraffic(gb) {
    if (gb < 1) {
        return `${(gb * 1024).toFixed(2)} MB`;
    }
    return `${gb.toFixed(2)} GB`;
}
