# 🚀 AI VPN Management System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/Platform-Linux-lightgrey.svg" alt="Platform">
</p>

<p align="center">
  <strong>基于 AI 智能流量调度的新一代 VPN 管理系统</strong>
</p>

<p align="center">
  集成 AI 节点评分算法、原生 Ubuntu 部署、Web 管理面板，打造极致的 VPN 管理体验
</p>

---

## ✨ 核心特性

### 🤖 AI 智能调度
- **自动节点评分**: 基于延迟（40%）、负载（30%）、稳定性（30%）的加权算法
- **晚高峰检测**: 自动识别拥堵时段，动态调整节点推荐
- **实时监控**: 每 60 秒更新一次全网节点评分
- **智能推荐**: AI 评分 >90 的节点自动标记为优选

### 🛠 原生部署架构
- **无 Docker 依赖**: 直接在 Ubuntu 20.04/22.04 LTS 上运行
- **Python 虚拟环境**: 完全隔离，不污染系统 Python
- **Systemd 服务**: 开机自启，自动重启，生产级稳定性
- **Nginx 反向代理**: 自动配置 SSL 证书（Let's Encrypt）

### 📊 Web 管理面板
- **用户面板**: 流量可视化、订阅管理、节点列表
- **管理后台**: 用户管理、节点配置、系统监控
- **实时数据**: Vue 3 驱动的响应式界面
- **移动适配**: Tailwind CSS 打造的现代化 UI

### 🔗 多协议支持
- **VLESS**: 主流协议，支持 Reality、TLS
- **传输层**: TCP、WebSocket、gRPC、HTTP/2
- **通用订阅**: 兼容 v2rayNG、Shadowrocket、Clash

---

## ⚡ 快速开始

### 一键安装（推荐）

```bash
# 下载安装脚本
curl -O https://raw.githubusercontent.com/your-repo/ai-vpn/main/install.sh

# 运行安装
sudo bash install.sh
```

**安装过程：**
1. 自动检测系统版本
2. 安装所有依赖（Python、Nginx、Redis）
3. 交互式配置域名和端口
4. 自动生成安全密钥
5. 配置 Systemd 服务
6. 申请 SSL 证书

---

### 手动开发部署

#### 1. 克隆项目

```bash
git clone https://github.com/your-repo/ai-vpn.git
cd ai-vpn
```

#### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
pip install -r requirements_scheduler.txt
```

#### 4. 配置环境

```bash
cp .env.example .env
nano .env  # 修改配置
```

#### 5. 启动后端

```bash
# 开发模式
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 6. 访问系统

- **用户面板**: http://localhost:8000/dashboard
- **管理后台**: http://localhost:8000/admin
- **API 文档**: http://localhost:8000/api/docs

---

## 📡 节点接入

### VPS 节点部署

在 VPN 服务器上运行监控 Agent：

#### 1. 安装依赖

```bash
cd agent
pip install -r requirements.txt
```

#### 2. 配置环境

```bash
cp .env.runner .env
nano .env
```

修改配置：
```env
API_ENDPOINT=https://your-control-server.com/api/v1/node/heartbeat
NODE_KEY=your-node-secret-key
NODE_ID=hk-node-01
```

#### 3. 运行 Agent

```bash
# 前台运行（测试）
python node_runner.py

# 后台运行
nohup python node_runner.py > runner.log 2>&1 &

# Systemd 服务
sudo cp vpn-node-reporter.service /etc/systemd/system/
sudo systemctl start vpn-node-reporter
sudo systemctl enable vpn-node-reporter
```

---

## 📚 目录结构

```
ai-vpn/
├── backend/                    # FastAPI 后端
│   ├── api/                    # API 路由
│   │   ├── client.py          # 客户端 API
│   │   └── admin.py           # 管理 API（待开发）
│   ├── services/               # 业务逻辑
│   │   ├── ai_scheduler.py    # AI 评分算法
│   │   └── scheduler.py       # 定时调度服务
│   ├── utils/                  # 工具函数
│   │   └── link_generator.py # 链接生成器
│   ├── models.py              # 数据模型
│   ├── database.py            # 数据库配置
│   ├── config.py              # 配置管理
│   └── main.py                # 应用入口
├── frontend/                   # 前端界面
│   ├── templates/             # HTML 模板
│   │   ├── user_dashboard.html
│   │   └── admin_index.html
│   └── static/                # 静态资源
│       ├── css/
│       └── js/
├── agent/                      # 节点 Agent
│   ├── node_runner.py         # 简化版监控脚本
│   ├── node_reporter.py       # 完整版监控脚本
│   └── DEPLOYMENT.md          # 部署文档
├── install.sh                  # 一键部署脚本
├── requirements.txt           # Python 依赖
└── README.md                  # 本文档
```

---

## 🔧 管理工具

安装后可使用 `aivpn` 命令管理系统：

```bash
aivpn start      # 启动服务
aivpn stop       # 停止服务
aivpn restart    # 重启服务
aivpn status     # 查看状态
aivpn logs       # 查看日志
aivpn update     # 更新系统
aivpn uninstall  # 卸载系统
```

---

## 📖 功能文档

- **[客户端 API 指南](CLIENT_API_GUIDE.md)** - API 接口文档
- **[AI 调度服务指南](AI_SCHEDULER_SERVICE_GUIDE.md)** - AI 算法详解
- **[节点 Agent 部署](agent/NODE_RUNNER_GUIDE.md)** - Agent 部署文档
- **[系统部署指南](DEPLOYMENT.md)** - 完整部署教程

---

## 🛡️ 安全建议

1. **修改默认密钥**: 生产环境必须修改 `.env` 中的 `ADMIN_SECRET` 和 `JWT_SECRET`
2. **启用 HTTPS**: 使用 `install.sh` 自动申请 SSL 证书
3. **配置防火墙**: 仅开放必要端口（80, 443）
4. **定期更新**: 使用 `aivpn update` 保持系统最新
5. **备份数据**: 定期备份 `/opt/ai-vpn/vpn_management.db`

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发流程

```bash
# Fork 项目
git clone https://github.com/your-username/ai-vpn.git
cd ai-vpn

# 创建分支
git checkout -b feature/your-feature

# 提交更改
git commit -m "Add: your feature description"
git push origin feature/your-feature

# 创建 Pull Request
```

---

## 📄 开源协议

本项目采用 MIT 协议开源 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化 Web 框架
- [SQLModel](https://sqlmodel.tiangolo.com/) - 优雅的 ORM
- [Vue.js](https://vuejs.org/) - 渐进式前端框架
- [Tailwind CSS](https://tailwindcss.com/) - 实用优先的 CSS 框架

---

## 📧 联系方式

- **Issues**: [GitHub Issues](https://github.com/your-repo/ai-vpn/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/ai-vpn/discussions)

---

<p align="center">
  Made with ❤️ by AI VPN Team
</p>

<p align="center">
  如果这个项目对你有帮助，请给我们一个 ⭐ Star！
</p>
