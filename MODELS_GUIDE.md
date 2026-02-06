# 📊 SQLModel 数据模型定义完成

## ✅ 已创建的数据模型

### 1. User (用户模型)
**文件**: [`backend/models/user.py`](file:///C:/Users/ljx10/Pictures/VPN/backend/models/user.py)

```python
class User(SQLModel, table=True):
    id: Optional[int]              # 主键
    email: str                     # 邮箱（唯一索引）
    hashed_password: str           # 密码哈希
    balance: float                 # 账户余额
    traffic_limit_gb: int          # 流量限制 (GB)
    current_traffic_gb: float      # 当前已用流量 (GB)
    is_active: bool                # 账户是否激活
```

### 2. Node (VPN 节点模型)
**文件**: [`backend/models/node.py`](file:///C:/Users/ljx10/Pictures/VPN/backend/models/node.py)

```python
class Node(SQLModel, table=True):
    id: Optional[int]              # 主键
    name: str                      # 节点名称
    ip: str                        # IP 地址
    port: int                      # 端口号
    protocol: str                  # 协议类型 (OpenVPN, WireGuard 等)
    ai_score: float                # AI 调度算法权重 (0-1)
    load_factor: float             # 负载系数 (0-1)
    
    # 关系：一个节点可以有多条监控记录
    metrics: List["NodeMetrics"]
```

### 3. NodeMetrics (节点监控日志模型)
**文件**: [`backend/models/metrics.py`](file:///C:/Users/ljx10/Pictures/VPN/backend/models/metrics.py)

```python
class NodeMetrics(SQLModel, table=True):
    id: Optional[int]              # 主键
    node_id: int                   # 外键 -> nodes.id
    latency: int                   # 延迟 (毫秒)
    packet_loss: float             # 丢包率 (0-1)
    recorded_at: datetime          # 记录时间
    
    # 关系：每条监控记录属于一个节点
    node: Optional["Node"]
```

## 🔧 数据库初始化

已更新 [`backend/database.py`](file:///C:/Users/ljx10/Pictures/VPN/backend/database.py)，导入所有模型：

```python
from backend.models import User, Node, NodeMetrics

def create_db_and_tables():
    """创建数据库表"""
    SQLModel.metadata.create_all(engine)
```

## 🧪 测试脚本

创建了 [`test_models.py`](file:///C:/Users/ljx10/Pictures/VPN/test_models.py) 用于测试数据模型：

```bash
# 运行测试
python test_models.py
```

测试内容：
✅ 创建数据库表  
✅ 插入示例数据（用户、节点、监控记录）  
✅ 查询数据验证关系

## 📝 使用示例

### 1. 初始化数据库

```python
from backend.database import init_db

# 创建所有表
init_db()
```

### 2. 创建用户

```python
from backend.models import User
from backend.database import get_session

with next(get_session()) as session:
    user = User(
        email="user@example.com",
        hashed_password="hashed_pw",
        balance=100.0,
        traffic_limit_gb=100,
        current_traffic_gb=0.0,
        is_active=True
    )
    session.add(user)
    session.commit()
```

### 3. 创建 VPN 节点

```python
from backend.models import Node

node = Node(
    name="US-West-01",
    ip="192.168.1.100",
    port=1194,
    protocol="OpenVPN",
    ai_score=0.85,
    load_factor=0.42
)
session.add(node)
session.commit()
```

### 4. 记录节点监控数据

```python
from backend.models import NodeMetrics
from datetime import datetime

metrics = NodeMetrics(
    node_id=node.id,
    latency=45,
    packet_loss=0.02,
    recorded_at=datetime.utcnow()
)
session.add(metrics)
session.commit()
```

### 5. 查询节点及其监控记录（关系查询）

```python
# 查询节点及其所有监控记录
node = session.get(Node, 1)
print(f"节点: {node.name}")
for metric in node.metrics:
    print(f"  - 延迟: {metric.latency}ms, 丢包: {metric.packet_loss*100}%")
```

## 🎯 数据库 ER 关系图

```
┌─────────────┐
│    User     │
├─────────────┤
│ id (PK)     │
│ email       │
│ password    │
│ balance     │
│ traffic_*   │
│ is_active   │
└─────────────┘

┌─────────────┐                ┌──────────────┐
│    Node     │                │ NodeMetrics  │
├─────────────┤                ├──────────────┤
│ id (PK)     │◄───────────────│ id (PK)      │
│ name        │  1         N   │ node_id (FK) │
│ ip          │                │ latency      │
│ port        │                │ packet_loss  │
│ protocol    │                │ recorded_at  │
│ ai_score    │                └──────────────┘
│ load_factor │
└─────────────┘
```

## 🔑 关键特性

1. **类型安全**: 使用 SQLModel 结合 Pydantic，提供完整的类型检查
2. **自动文档**: 每个字段都有 `description`，便于生成 API 文档
3. **关系映射**: Node ↔ NodeMetrics 一对多关系
4. **索引优化**: `User.email` 建立了唯一索引
5. **默认值**: 合理的字段默认值（如 `ai_score=0.0`）
6. **时间戳**: `recorded_at` 使用 `default_factory` 自动生成

## 🚀 下一步建议

1. **API 路由**: 为每个模型创建 CRUD API
   - `GET /api/v1/users` - 获取用户列表
   - `POST /api/v1/nodes` - 创建节点
   - `GET /api/v1/nodes/{id}/metrics` - 获取节点监控历史

2. **数据验证**: 添加 Pydantic 验证器
   - 邮箱格式验证
   - IP 地址格式验证
   - 端口范围验证（1-65535）

3. **AI 算法集成**: 
   - 根据 `NodeMetrics` 数据计算 `ai_score`
   - 智能负载均衡算法

4. **前端集成**: 在 Streamlit 中展示数据
   - 用户管理界面
   - 节点监控仪表板
   - 实时性能图表

---

**所有数据模型已就绪！** 🎉 现在可以运行 `python test_models.py` 测试数据库操作。
