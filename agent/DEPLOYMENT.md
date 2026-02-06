# 📡 VPN 节点 Agent 部署指南

## 📋 概述

`node_reporter.py` 是运行在 VPN 节点服务器上的状态汇报 Agent，负责：

- 🖥️ 监控系统资源（CPU、内存、磁盘、网络）
- 🌐 测试网络延迟（Ping Google/Cloudflare DNS）
- 💓 定期向主控端发送心跳数据
- 🔄 自动重试和错误恢复

---

## 🚀 快速部署

### 1. 安装依赖

```bash
cd agent
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置
nano .env
```

**必需配置：**
```bash
CONTROL_SERVER_URL=http://your-control-server:8000
NODE_ID=node-001
NODE_NAME=US-East-01
NODE_SECRET=your-secure-secret
```

### 3. 测试运行

```bash
python node_reporter.py
```

**预期输出：**
```
============================================================
🚀 VPN 节点状态汇报 Agent 启动
============================================================
节点 ID: node-001
节点名称: US-East-01
主控端地址: http://localhost:8000
汇报间隔: 10 秒
============================================================
📊 收集系统指标...
  CPU: 15.2% | 内存: 45.7% | 延迟: 18.5ms
✅ 心跳发送成功
```

---

## 🐧 Linux 系统服务部署

### 方法 1: systemd 服务（推荐）

#### 创建服务文件

```bash
sudo nano /etc/systemd/system/vpn-node-reporter.service
```

**服务文件内容：**
```ini
[Unit]
Description=VPN Node Status Reporter
After=network.target

[Service]
Type=simple
User=vpnagent
WorkingDirectory=/opt/vpn-agent
ExecStart=/usr/bin/python3 /opt/vpn-agent/node_reporter.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# 环境变量（也可以使用 EnvironmentFile）
Environment="CONTROL_SERVER_URL=http://your-server:8000"
Environment="NODE_ID=node-001"
Environment="NODE_NAME=US-East-01"
Environment="NODE_SECRET=your-secret"

[Install]
WantedBy=multi-user.target
```

#### 启动服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start vpn-node-reporter

# 查看状态
sudo systemctl status vpn-node-reporter

# 开机自启
sudo systemctl enable vpn-node-reporter

# 查看日志
sudo journalctl -u vpn-node-reporter -f
```

---

### 方法 2: Supervisor

#### 安装 Supervisor

```bash
sudo apt-get install supervisor
```

#### 创建配置文件

```bash
sudo nano /etc/supervisor/conf.d/vpn-node-reporter.conf
```

**配置文件内容：**
```ini
[program:vpn-node-reporter]
command=python3 /opt/vpn-agent/node_reporter.py
directory=/opt/vpn-agent
user=vpnagent
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/vpn-node-reporter.log
environment=CONTROL_SERVER_URL="http://your-server:8000",NODE_ID="node-001"
```

#### 启动

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start vpn-node-reporter
sudo supervisorctl status
```

---

## 🪟 Windows 部署

### 方法 1: NSSM (Windows Service Wrapper)

#### 1. 下载 NSSM

```powershell
# 从 https://nssm.cc/download 下载 NSSM
```

#### 2. 安装服务

```powershell
# 打开 NSSM GUI
nssm install VPNNodeReporter

# 或使用命令行
nssm install VPNNodeReporter "C:\Python\python.exe" "C:\vpn-agent\node_reporter.py"
nssm set VPNNodeReporter AppDirectory "C:\vpn-agent"
nssm set VPNNodeReporter AppEnvironmentExtra CONTROL_SERVER_URL=http://your-server:8000 NODE_ID=node-001

# 启动服务
nssm start VPNNodeReporter
```

---

### 方法 2: Task Scheduler

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：系统启动时
4. 操作：启动程序
   - 程序：`python.exe`
   - 参数：`C:\vpn-agent\node_reporter.py`
   - 起始于：`C:\vpn-agent`

---

## ⚙️ 配置说明

### 环境变量

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `CONTROL_SERVER_URL` | ✅ | `http://localhost:8000` | 主控端 API 地址 |
| `NODE_ID` | ✅ | `unknown-node` | 节点唯一标识 |
| `NODE_NAME` | 否 | 主机名 | 节点显示名称 |
| `NODE_SECRET` | ✅ | 空 | 节点认证密钥 |
| `REPORT_INTERVAL` | 否 | `10` | 汇报间隔（秒） |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别 |

---

## 📊 数据格式

Agent 发送到主控端的 JSON 格式：

```json
{
    "node_id": "node-001",
    "node_name": "US-East-01",
    "timestamp": "2026-02-05T09:15:32.123456",
    "system": {
        "platform": "Linux",
        "platform_version": "5.15.0-1234-generic",
        "hostname": "vpn-server-01"
    },
    "cpu": {
        "usage_percent": 15.2
    },
    "memory": {
        "total_mb": 8192.0,
        "used_mb": 3741.5,
        "percent": 45.7
    },
    "disk": {
        "total_gb": 100.0,
        "used_gb": 42.3,
        "percent": 42.3
    },
    "network": {
        "bytes_sent": 1234567890,
        "bytes_recv": 9876543210,
        "packets_sent": 5678901,
        "packets_recv": 12345678
    },
    "latency_ms": 18.5
}
```

---

## 🔍 故障排查

### Agent 无法连接到主控端

**检查：**
1. 主控端 URL 是否正确
2. 网络连接是否正常
3. 防火墙是否开放端口

**解决：**
```bash
# 测试主控端连接
curl http://your-server:8000/health

# 查看 Agent 日志
tail -f node_reporter.log
```

---

### 延迟测试失败

**原因：**
- 网络不通
- 防火墙阻止 ICMP
- Ping 命令不可用

**解决：**
```bash
# 手动测试 ping
ping -c 1 8.8.8.8

# 检查防火墙
sudo iptables -L
```

---

### CPU/内存数据为 0

**原因：**
- psutil 权限不足
- 系统不支持某些监控指标

**解决：**
```bash
# 以管理员权限运行
sudo python node_reporter.py
```

---

## 🔒 安全建议

1. **使用 HTTPS**：生产环境应使用 HTTPS 连接主控端
2. **节点认证**：设置强密钥 `NODE_SECRET`
3. **最小权限**：使用专用用户运行 Agent
4. **日志轮转**：配置日志文件轮转避免磁盘占满

---

## 📝 维护

### 查看日志

```bash
# systemd
sudo journalctl -u vpn-node-reporter -f

# 文件日志
tail -f /opt/vpn-agent/node_reporter.log
```

### 重启服务

```bash
# systemd
sudo systemctl restart vpn-node-reporter

# supervisor
sudo supervisorctl restart vpn-node-reporter
```

### 更新 Agent

```bash
cd /opt/vpn-agent
git pull
sudo systemctl restart vpn-node-reporter
```

---

## 🎯 性能优化

1. **调整汇报间隔**：根据需求设置 `REPORT_INTERVAL`（建议 10-60 秒）
2. **减少 Ping 目标**：如果延迟测试影响性能，可减少 Ping 目标数量
3. **日志级别**：生产环境使用 `INFO` 或 `WARNING`

---

**部署完成后，可在主控端查看节点状态！** 🎉
