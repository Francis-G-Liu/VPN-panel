# 📱 客户端 API 使用指南

## 📋 概述

客户端 API 提供给 VPN 客户端（App、v2rayNG、Shadowrocket 等）使用，实现节点查询、订阅导入和流量统计功能。

**基础URL**: `http://your-server:8000/api/v1/client`

---

## 🔐 认证方式

所有客户端 API 都需要在 HTTP Header 中提供认证令牌：

```http
Authorization: Bearer your-auth-token
```

或简化格式：
```http
Authorization: your-auth-token
```

---

## 📡 API 端点

### 1. 获取节点列表

**GET** `/api/v1/client/nodes`

获取当前用户可用的节点列表（JSON 格式）。

#### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/client/nodes" \
  -H "Authorization: Bearer your-token"
```

#### 响应示例

```json
[
  {
    "id": 1,
    "name": "HK-Node-01",
    "link": "vless://user-uuid@1.2.3.4:443?type=tcp&encryption=none&security=tls&sni=example.com#HK-Node-01",
    "ai_score": 0.95,
    "load_factor": 0.3,
    "protocol": "vless"
  },
  {
    "id": 2,
    "name": "US-Node-02",
    "link": "vless://user-uuid@5.6.7.8:443?type=ws&encryption=none&security=reality&pbk=xxx&sid=xxx#US-Node-02",
    "ai_score": 0.88,
    "load_factor": 0.5,
    "protocol": "vless"
  }
]
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | number | 节点 ID |
| `name` | string | 节点名称 |
| `link` | string | VLESS 订阅链接 |
| `ai_score` | number | AI 评分（0-1） |
| `load_factor` | number | 负载系数 |
| `protocol` | string | 协议类型 |

---

### 2. 通用订阅接口

**GET** `/api/v1/client/subscribe`

获取 Base64 编码的通用订阅链接，供主流客户端导入。

#### 支持的客户端

- ✅ v2rayNG (Android)
- ✅ Shadowrocket (iOS)
- ✅ v2rayN (Windows)
- ✅ Clash (跨平台)
- ✅ QuantumultX (iOS)

#### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/client/subscribe" \
  -H "Authorization: Bearer your-token"
```

#### 响应示例

```
dmxlc3M6Ly91c2VyLXV1aWRAMS4yLjMuNDo0NDM/dHlwZT10Y3AmZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9ZXhhbXBsZS5jb20jSEstTm9kZS0wMQ==
```

#### 响应头

```http
Content-Type: text/plain; charset=utf-8
Subscription-Userinfo: upload=0; download=5623654400; total=107374182400
Profile-Update-Interval: 24
```

#### 客户端配置

**v2rayNG (Android):**
1. 打开 v2rayNG
2. 点击 "+" → "导入订阅"
3. 输入订阅地址：`http://your-server:8000/api/v1/client/subscribe`
4. 设置 Auth Header：`Bearer your-token`
5. 点击"更新订阅"

**Shadowrocket (iOS):**
1. 打开 Shadowrocket
2. 首页 → "+" → "订阅"
3. URL: `http://your-server:8000/api/v1/client/subscribe`
4. 备注: 自定义名称
5. 保存并更新

---

### 3. 更新流量使用

**POST** `/api/v1/client/traffic`

客户端回调此接口来更新用户流量使用情况。

#### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/client/traffic?bytes_used=1048576" \
  -H "Authorization: Bearer your-token"
```

#### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `bytes_used` | number | ✅ | 本次使用的流量（字节） |

#### 响应示例

```json
{
  "user_id": 1,
  "current_traffic_gb": 5.23,
  "traffic_limit_gb": 100,
  "remaining_gb": 94.77,
  "percentage": 5.23,
  "updated_at": "2026-02-05T14:30:00"
}
```

---

### 4. 获取用户信息

**GET** `/api/v1/client/user/info`

获取当前用户的基本信息和流量使用情况。

#### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/client/user/info" \
  -H "Authorization: Bearer your-token"
```

#### 响应示例

```json
{
  "id": 1,
  "email": "user@example.com",
  "balance": 100.0,
  "traffic": {
    "used_gb": 5.23,
    "total_gb": 100,
    "remaining_gb": 94.77,
    "percentage": 5.23
  },
  "is_active": true,
  "created_at": "2026-01-01T00:00:00"
}
```

---

## 🔗 VLESS 链接格式

生成的 VLESS 链接遵循标准格式：

```
vless://uuid@server:port?params#name
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `type` | 传输协议 | tcp, ws, grpc, h2 |
| `encryption` | 加密方式 | none (VLESS 固定) |
| `security` | 安全层 | none, tls, reality |
| `sni` | TLS SNI | example.com |
| `fp` | TLS 指纹 | chrome, firefox |
| `pbk` | Reality 公钥 | xxx |
| `sid` | Reality Short ID | xxx |
| `host` | WS/HTTP Host | cdn.example.com |
| `path` | WS/HTTP Path | /path |
| `serviceName` | gRPC 服务名 | grpc-service |

### 示例链接

**TCP + TLS:**
```
vless://uuid@1.2.3.4:443?type=tcp&encryption=none&security=tls&sni=example.com&fp=chrome#Node-Name
```

**WebSocket + TLS:**
```
vless://uuid@1.2.3.4:443?type=ws&encryption=none&security=tls&host=cdn.example.com&path=/ws#Node-Name
```

**Reality:**
```
vless://uuid@1.2.3.4:443?type=tcp&encryption=none&security=reality&pbk=xxx&sid=xxx&sni=www.microsoft.com#Node-Name
```

---

## ❌ 错误处理

### 401 Unauthorized

**原因**: 未提供认证令牌或令牌无效

```json
{
  "detail": "无效的认证令牌 (Invalid authentication token)"
}
```

**解决**: 检查 Authorization Header 是否正确

---

### 403 Forbidden

**原因1**: 账户已被停用

```json
{
  "detail": "账户已被停用 (Account disabled)"
}
```

**原因2**: 流量已超限

```json
{
  "detail": "流量已超限 (5.00/3 GB)"
}
```

**解决**: 联系管理员或充值流量包

---

### 404 Not Found

**原因**: 没有可用的节点

```json
{
  "detail": "没有可用的节点 (No available nodes)"
}
```

**解决**: 联系管理员添加节点

---

## 🧪 测试示例

### Python 示例

```python
import requests
import base64

# 配置
BASE_URL = "http://localhost:8000/api/v1/client"
TOKEN = "your-auth-token"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# 1. 获取节点列表
response = requests.get(f"{BASE_URL}/nodes", headers=headers)
nodes = response.json()
print(f"共 {len(nodes)} 个节点")

# 2. 获取订阅
response = requests.get(f"{BASE_URL}/subscribe", headers=headers)
subscription_b64 = response.text
subscription_text = base64.b64decode(subscription_b64).decode('utf-8')
print("订阅链接：")
print(subscription_text)

# 3. 更新流量（使用了 1MB）
response = requests.post(
    f"{BASE_URL}/traffic",
    params={"bytes_used": 1024 * 1024},
    headers=headers
)
traffic_info = response.json()
print(f"已用流量: {traffic_info['current_traffic_gb']} GB")
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:8000/api/v1/client';
const TOKEN = 'your-auth-token';

const headers = {
  'Authorization': `Bearer ${TOKEN}`
};

// 1. 获取节点列表
fetch(`${BASE_URL}/nodes`, { headers })
  .then(res => res.json())
  .then(nodes => {
    console.log(`共 ${nodes.length} 个节点`);
    nodes.forEach(node => {
      console.log(`${node.name}: ${node.ai_score}`);
    });
  });

// 2. 获取订阅
fetch(`${BASE_URL}/subscribe`, { headers })
  .then(res => res.text())
  .then(b64 => {
    const text = atob(b64);
    console.log('订阅链接:', text);
  });
```

---

## 🔒 安全建议

1. **HTTPS**: 生产环境必须使用 HTTPS
2. **Token 管理**: 定期刷新 token
3. **速率限制**: 避免频繁调用 API
4. **错误处理**: 妥善处理 401/403 错误

---

## 📝 更新日志

**v1.0.0** (2026-02-05)
- ✅ 实现节点列表接口
- ✅ 实现通用订阅接口（Base64）
- ✅ 实现流量回调接口
- ✅ 实现用户信息接口
- ✅ 支持 VLESS/VMess/Trojan 链接生成

---

**技术支持**: 遇到问题请查看 `/api/docs` 交互式文档
