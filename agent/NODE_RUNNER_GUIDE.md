# 📡 Node Runner 快速部署指南

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install requests psutil ping3
```

### 2. 配置环境变量

```bash
# Linux/Mac
export API_ENDPOINT="https://api.yourvpn.com/api/v1/node/heartbeat"
export NODE_KEY="your-secure-node-key"
export NODE_ID="hk-node-01"

# Windows (PowerShell)
$env:API_ENDPOINT="https://api.yourvpn.com/api/v1/node/heartbeat"
$env:NODE_KEY="your-secure-node-key"
$env:NODE_ID="hk-node-01"
```

或者复制配置文件：
```bash
cp .env.runner .env
nano .env  # 编辑配置
```

### 3. 运行脚本

```bash
python node_runner.py
```

**预期输出：**
```
============================================================
🚀 VPN 节点监控脚本启动
============================================================
节点 ID: hk-node-01
后端 API: https://api.yourvpn.com/api/v1/node/heartbeat
汇报间隔: 15 秒
延迟测试目标: 8.8.8.8, www.google.com, api.openai.com
============================================================
📊 收集监控数据...
  CPU: 15.2% | 内存: 45.7% | 延迟: 18.5ms
✅ 心跳发送成功
⏰ 等待 15 秒...
```

---

## 🐧 后台运行（Linux）

### 使用 nohup

```bash
nohup python node_runner.py > runner.log 2>&1 &
```

### 使用 systemd

创建服务文件：
```bash
sudo nano /etc/systemd/system/vpn-node-runner.service
```

内容：
```ini
[Unit]
Description=VPN Node Runner
After=network.target

[Service]
Type=simple
User=vpn
WorkingDirectory=/opt/vpn-agent
ExecStart=/usr/bin/python3 /opt/vpn-agent/node_runner.py
Restart=always
Environment="API_ENDPOINT=https://api.yourvpn.com/api/v1/node/heartbeat"
Environment="NODE_KEY=your-key"
Environment="NODE_ID=hk-node-01"

[Install]
WantedBy=multi-user.target
```

启动：
```bash
sudo systemctl start vpn-node-runner
sudo systemctl enable vpn-node-runner
sudo systemctl status vpn-node-runner
```

---

## 📊 数据格式

发送到后端的 JSON：

```json
{
  "node_id": "hk-node-01",
  "timestamp": "2026-02-05T13:45:32.123456",
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.7,
    "network_tx_kbps": 1234.56,
    "network_rx_kbps": 5678.90
  },
  "network": {
    "latencies": {
      "8.8.8.8": 18.5,
      "www.google.com": 20.3,
      "api.openai.com": 9999
    },
    "average_latency_ms": 19.4
  }
}
```

---

## ⚙️ 配置说明

| 环境变量 | 必需 | 默认值 | 说明 |
|---------|------|--------|------|
| `API_ENDPOINT` | ✅ | `http://localhost:8000/...` | 后端心跳接口 |
| `NODE_KEY` | ✅ | `your-node-secret-key` | 节点认证密钥 |
| `NODE_ID` | ✅ | `node-001` | 节点唯一标识 |
| `REPORT_INTERVAL` | 否 | `15` | 汇报间隔（秒） |
| `LOG_LEVEL` | 否 | `INFO` | 日志级别 |

---

## 🔍 故障排查

### 问题：导入失败 "No module named 'ping3'"

**解决：**
```bash
pip install ping3
```

**Windows 用户注意：** ping3 需要管理员权限
```powershell
# 以管理员身份运行
python node_runner.py
```

---

### 问题：延迟测试全部返回 9999

**原因：**
- 防火墙阻止 ICMP
- 网络连接问题

**解决：**
```bash
# 测试 ping 权限
ping 8.8.8.8

# 检查防火墙
sudo iptables -L
```

---

### 问题：连续失败

**检查：**
1. 后端 API 是否正常
2. NODE_KEY 是否正确
3. 网络连接是否稳定

---

## 📝 日志

查看日志：
```bash
tail -f node_runner.log
```

---

**部署完成！脚本将每 15 秒向后端汇报一次监控数据。** 🎉
