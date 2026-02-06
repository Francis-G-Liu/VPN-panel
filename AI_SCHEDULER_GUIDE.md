# 🤖 AI 节点调度器使用指南

## 📋 概述

AI 节点调度器 (`ai_scheduler.py`) 是 VPN 管理系统的核心算法模块，用于根据节点的延迟、负载等指标智能计算最优节点。

---

## 🎯 核心功能

### 算法逻辑

```
Score = (1 - Normalized_Latency) × 0.5   # 延迟越低越好
      + (1 - Normalized_Load) × 0.3      # 负载越低越好
      + Random_Factor × 0.2              # 防止流量集中
```

### 数学原理

1. **Min-Max 标准化**
   ```
   normalized = (value - min) / (max - min)
   ```
   - 将不同量纲的数据统一到 [0, 1] 区间

2. **加权评分**
   - 延迟权重: 50%（最重要）
   - 负载权重: 30%
   - 随机因子: 20%（负载均衡）

3. **反向转换**
   - 因为延迟和负载是"越低越好"的指标
   - 使用 `(1 - normalized_value)` 转换
   - 确保低延迟、低负载得到高分

---

## 🚀 快速开始

### 方法 1: 使用便捷函数（推荐）

```python
from backend.services import calculate_scores

# 节点数据
nodes = [
    {"id": 1, "name": "US-East", "latency": 20, "load_factor": 0.3},
    {"id": 2, "name": "EU-West", "latency": 100, "load_factor": 0.7},
    {"id": 3, "name": "Asia", "latency": 50, "load_factor": 0.2}
]

# 计算评分
result = calculate_scores(nodes)

# 查看结果
for node in result:
    print(f"{node['name']}: {node['ai_score']:.4f} (排名 #{node['rank']})")
```

**输出示例：**
```
Asia: 0.8234 (排名 #1)
US-East: 0.7891 (排名 #2)
EU-West: 0.4567 (排名 #3)
```

---

### 方法 2: 使用类（支持自定义权重）

```python
from backend.services.ai_scheduler import AIScheduler

# 延迟优先策略
scheduler = AIScheduler(
    latency_weight=0.7,    # 延迟权重提高到 70%
    load_weight=0.2,       # 负载权重降低到 20%
    random_weight=0.1      # 随机因子降低到 10%
)

result = scheduler.calculate_scores(nodes)
```

---

## 💼 实际应用场景

### 场景 1: 在 API 中使用

```python
from fastapi import APIRouter
from backend.services import calculate_scores
from backend.database import get_session
from backend.models import Node, NodeMetrics

router = APIRouter()

@router.get("/api/v1/nodes/recommended")
async def get_recommended_nodes(limit: int = 3):
    """获取推荐节点列表"""
    
    # 1. 从数据库获取节点及其最新监控数据
    with next(get_session()) as session:
        nodes = session.query(Node).all()
        
        # 2. 构建评分所需的数据
        nodes_data = []
        for node in nodes:
            # 获取该节点最新的监控记录
            latest_metric = session.query(NodeMetrics)\
                .filter(NodeMetrics.node_id == node.id)\
                .order_by(NodeMetrics.recorded_at.desc())\
                .first()
            
            nodes_data.append({
                "id": node.id,
                "name": node.name,
                "ip": node.ip,
                "port": node.port,
                "protocol": node.protocol,
                "latency": latest_metric.latency if latest_metric else 100,
                "load_factor": node.load_factor
            })
        
        # 3. 计算 AI 评分
        scored_nodes = calculate_scores(nodes_data)
        
        # 4. 返回前 N 个推荐节点
        return scored_nodes[:limit]
```

---

### 场景 2: 更新数据库中的 AI 评分

```python
from backend.services import calculate_scores
from backend.database import get_session
from backend.models import Node, NodeMetrics

def update_ai_scores():
    """定时任务：更新所有节点的 AI 评分"""
    
    with next(get_session()) as session:
        # 获取所有节点和监控数据
        nodes = session.query(Node).all()
        
        nodes_data = []
        for node in nodes:
            latest_metric = session.query(NodeMetrics)\
                .filter(NodeMetrics.node_id == node.id)\
                .order_by(NodeMetrics.recorded_at.desc())\
                .first()
            
            nodes_data.append({
                "id": node.id,
                "latency": latest_metric.latency if latest_metric else 100,
                "load_factor": node.load_factor
            })
        
        # 计算评分
        scored_nodes = calculate_scores(nodes_data)
        
        # 更新数据库
        for scored in scored_nodes:
            node = session.get(Node, scored['id'])
            if node:
                node.ai_score = scored['ai_score']
        
        session.commit()
        print(f"✅ 更新了 {len(scored_nodes)} 个节点的 AI 评分")

# 可以配置为定时任务（如每 5 分钟执行一次）
```

---

### 场景 3: 使用 Pandas DataFrame

```python
import pandas as pd
from backend.services import calculate_scores

# 从数据库查询结果转换为 DataFrame
df = pd.read_sql(
    "SELECT id, name, latency, load_factor FROM nodes",
    engine
)

# 直接传入 DataFrame
result = calculate_scores(df)

# 转换回 DataFrame 查看
result_df = pd.DataFrame(result)
print(result_df[['name', 'ai_score', 'rank']])
```

---

## ⚙️ 高级配置

### 自定义权重策略

根据不同场景调整权重：

```python
from backend.services.ai_scheduler import AIScheduler

# 🎮 游戏加速场景（延迟最重要）
gaming_scheduler = AIScheduler(
    latency_weight=0.8,
    load_weight=0.1,
    random_weight=0.1
)

# 📹 视频流媒体场景（负载均衡重要）
streaming_scheduler = AIScheduler(
    latency_weight=0.3,
    load_weight=0.6,
    random_weight=0.1
)

# ⚖️ 负载均衡场景（增大随机因子）
balanced_scheduler = AIScheduler(
    latency_weight=0.4,
    load_weight=0.3,
    random_weight=0.3
)
```

---

## 📊 返回数据格式

```python
[
    {
        "id": 3,
        "name": "Asia-Seoul",
        "ip": "192.168.1.102",
        "port": 51820,
        "protocol": "WireGuard",
        "latency": 25,
        "load_factor": 0.2,
        "ai_score": 0.9234,    # AI 评分（新增）
        "rank": 1              # 排名（新增）
    },
    {
        "id": 1,
        "name": "US-East",
        "latency": 50,
        "load_factor": 0.3,
        "ai_score": 0.8567,
        "rank": 2
    },
    ...
]
```

---

## 🧪 测试

运行测试脚本：

```bash
python test_ai_scheduler.py
```

**测试内容：**
1. 字典列表输入
2. Pandas DataFrame 输入
3. 自定义权重
4. 边界情况（单节点、相同延迟等）

---

## 🔍 边界情况处理

### 1. 空列表
```python
result = calculate_scores([])
# 返回: []
```

### 2. 单个节点
```python
result = calculate_scores([{"id": 1, "latency": 50, "load_factor": 0.5}])
# 返回: 评分为中间值 (约 0.5)
```

### 3. 所有节点指标相同
```python
nodes = [
    {"id": 1, "latency": 50, "load_factor": 0.5},
    {"id": 2, "latency": 50, "load_factor": 0.5}
]
result = calculate_scores(nodes)
# 返回: 所有节点评分接近，由随机因子决定排序
```

---

## 🎓 扩展建议

### 未来可以加入的因素

1. **丢包率** (`packet_loss`)
   ```python
   score += (1 - packet_loss_norm) * 0.1
   ```

2. **带宽** (`bandwidth`)
   ```python
   score += bandwidth_norm * 0.15
   ```

3. **地理距离** (`geo_distance`)
   ```python
   score += (1 - distance_norm) * 0.1
   ```

4. **历史可靠性** (`uptime_rate`)
   ```python
   score += uptime_norm * 0.05
   ```

---

## 💡 最佳实践

1. **定时更新**：建议每 5-10 分钟更新一次 AI 评分
2. **缓存结果**：对于高并发场景，缓存评分结果 1-2 分钟
3. **日志记录**：记录评分变化，用于后续分析优化
4. **A/B 测试**：测试不同权重策略的实际效果

---

## 🐛 故障排查

**问题：所有节点评分都很低**
- 检查：权重配置是否正确
- 解决：确保权重总和为 1.0

**问题：评分变化不明显**
- 检查：节点指标差异是否太小
- 解决：考虑增加权重或引入更多评分因素

**问题：评分随机性太大**
- 检查：`random_weight` 是否设置过高
- 解决：降低随机因子权重（如 0.1）

---

**文档版本**: v1.0  
**最后更新**: 2026-02-05
