# 🚀 AI VPN 系统部署指南

## 📋 系统要求

- **操作系统**: Ubuntu 20.04/22.04 LTS 或 Debian 11/12
- **最低配置**: 1 CPU, 1GB RAM, 20GB 磁盘  
- **推荐配置**: 2 CPU, 2GB RAM, 50GB 磁盘
- **网络**: 公网 IP 和域名（用于 SSL 证书）

---

## 🎯 快速部署

### 1. 准备工作

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 克隆项目（或上传文件）
git clone https://github.com/your-repo/ai-vpn.git
cd ai-vpn
```

### 2. 一键安装

```bash
sudo bash install.sh
```

### 3. 交互式配置

脚本会提示以下信息：

```
请输入绑定的域名 (例如 vpn.example.com): your-domain.com
请输入后台管理端口 (默认 8000): 8000
是否申请 Let's Encrypt SSL 证书? (y/n, 默认 y): y
```

### 4. 等待完成

安装过程大约需要 5-10 分钟，完成后会显示：

```
════════════════════════════════════════════════════════
🎉 AI VPN 系统安装完成！
════════════════════════════════════════════════════════

📋 重要信息:
  - 访问地址: https://your-domain.com
  - 后端端口: 8000
  - 安装目录: /opt/ai-vpn

🔧 管理命令:
  aivpn start    - 启动服务
  aivpn stop     - 停止服务
  aivpn restart  - 重启服务
  aivpn status   - 查看状态
  aivpn logs     - 查看日志
  aivpn update   - 更新系统
```

---

## 🔧 管理工具使用

### 服务控制

```bash
# 启动服务
aivpn start

# 停止服务
aivpn stop

# 重启服务
aivpn restart

# 查看状态
aivpn status
```

### 日志查看

```bash
# 实时查看日志
aivpn logs

# 查看最近 100 行
journalctl -u ai-vpn-backend -n 100

# 查看调度器日志
journalctl -u ai-vpn-scheduler -f
```

### 系统更新

```bash
# 一键更新
aivpn update

# 手动更新
cd /opt/ai-vpn
sudo -u aivpn git pull
sudo -u aivpn venv/bin/pip install -r requirements.txt
aivpn restart
```

---

## 📁 目录结构

```
/opt/ai-vpn/
├── backend/          # 后端代码
├── frontend/         # 前端代码
├── agent/            # 节点 Agent
├── venv/             # Python 虚拟环境
├── .env              # 环境配置
├── requirements.txt  # Python 依赖
└── vpn_management.db # SQLite 数据库
```

---

## 🌐 访问地址

- **用户面板**: https://your-domain.com/dashboard
- **管理后台**: https://your-domain.com/admin
- **API 文档**: https://your-domain.com/api/docs
- **健康检查**: https://your-domain.com/health

---

## 🔒 安全配置

### 防火墙设置

```bash
# 启用防火墙
sudo ufw enable

# 开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# 查看状态
sudo ufw status
```

### SSL 证书更新

```bash
# 测试自动更新
sudo certbot renew --dry-run

# 手动更新
sudo certbot renew
```

### 修改密钥

编辑 `/opt/ai-vpn/.env`：

```bash
sudo nano /opt/ai-vpn/.env
```

修改以下配置：
```env
ADMIN_SECRET=your-new-admin-secret
JWT_SECRET=your-new-jwt-secret
```

然后重启服务：
```bash
aivpn restart
```

---

## 🔄 更新与升级

### 小版本更新

```bash
# 使用管理工具
aivpn update
```

### 大版本升级

```bash
# 备份数据
sudo cp /opt/ai-vpn/vpn_management.db /opt/ai-vpn/vpn_management.db.backup
sudo cp /opt/ai-vpn/.env /opt/ai-vpn/.env.backup

# 更新代码
cd /opt/ai-vpn
sudo -u aivpn git pull

# 更新依赖
sudo -u aivpn venv/bin/pip install -r requirements.txt --upgrade

# 重启服务
aivpn restart
```

---

## 🗑️ 卸载系统

### 完全卸载

```bash
# 使用管理工具
aivpn uninstall

# 或直接运行脚本
sudo bash install.sh --uninstall
```

### 卸载内容

- ✅ 停止并删除 systemd 服务
- ✅ 删除 Nginx 配置
- ✅ 删除 `/opt/ai-vpn` 目录
- ✅ 删除管理工具
- ⚠️  可选删除服务用户

---

## 🐛 故障排查

### 问题：服务无法启动

**检查：**
```bash
# 查看服务状态
systemctl status ai-vpn-backend
systemctl status ai-vpn-scheduler

# 查看详细日志
journalctl -u ai-vpn-backend -n 50
```

**解决：**
1. 检查端口是否被占用
2. 检查配置文件 `/opt/ai-vpn/.env`
3. 检查 Python 依赖是否安装完整

---

### 问题：无法访问网站

**检查：**
```bash
# 检查 Nginx 状态
systemctl status nginx

# 测试 Nginx 配置
nginx -t

# 查看 Nginx 日志
tail -f /var/log/nginx/error.log
```

**解决：**
1. 确认域名 DNS 已正确解析
2. 检查防火墙是否开放 80/443 端口
3. 检查 SSL 证书是否正确安装

---

### 问题：SSL 证书申请失败

**原因：**
- 域名未正确解析到服务器 IP
- 80 端口未开放
- Let's Encrypt 速率限制

**解决：**
```bash
# 手动申请证书
sudo certbot --nginx -d your-domain.com

# 使用 DNS 验证（如果 80 端口不可用）
sudo certbot certonly --manual --preferred-challenges dns -d your-domain.com
```

---

## 📊 性能优化

### 数据库优化

```bash
# 定期清理过期数据
cd /opt/ai-vpn
sudo -u aivpn venv/bin/python -c "
from backend.database import get_session
from backend.models import NodeMetrics
from datetime import datetime, timedelta
with next(get_session()) as session:
    cutoff = datetime.utcnow() - timedelta(days=30)
    session.query(NodeMetrics).filter(NodeMetrics.recorded_at < cutoff).delete()
    session.commit()
"
```

### Nginx 优化

编辑 `/etc/nginx/sites-available/ai-vpn`：

```nginx
# 启用 gzip 压缩
gzip on;
gzip_types text/plain text/css application/json application/javascript;

# 增加缓存
location /static {
    alias /opt/ai-vpn/frontend/static;
    expires 7d;
    add_header Cache-Control "public, immutable";
}
```

### Redis 优化

编辑 `/etc/redis/redis.conf`：

```
maxmemory 256mb
maxmemory-policy allkeys-lru
```

---

## 📞 技术支持

如遇到问题，请：
1. 查看日志: `aivpn logs`
2. 检查服务状态: `aivpn status`
3. 查阅本文档故障排查部分

---

**部署成功！享受 AI 智能 VPN 管理系统！** 🎉
