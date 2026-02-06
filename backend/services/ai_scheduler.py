"""
AI 节点调度器 - 智能选择最佳 VPN 节点

该模块实现了基于多因素加权的节点评分算法，用于：
1. 根据延迟、负载等指标计算节点得分
2. 返回按优先级排序的节点列表
3. 支持动态权重调整和随机因子

作者: AI VPN Team
日期: 2026-02-05
"""

import random
from typing import List, Dict, Union, Optional
import pandas as pd


class AIScheduler:
    """
    AI 节点调度器类
    
    负责计算和管理节点的 AI 评分，帮助系统选择最优节点。
    """
    
    def __init__(
        self,
        latency_weight: float = 0.5,
        load_weight: float = 0.3,
        random_weight: float = 0.2
    ):
        """
        初始化 AI 调度器
        
        Args:
            latency_weight: 延迟权重 (默认 0.5)
            load_weight: 负载权重 (默认 0.3)
            random_weight: 随机因子权重 (默认 0.2)
        
        Note:
            权重总和应该等于 1.0，否则会自动归一化
        """
        # 自动归一化权重
        total = latency_weight + load_weight + random_weight
        self.latency_weight = latency_weight / total
        self.load_weight = load_weight / total
        self.random_weight = random_weight / total
        
    def calculate_scores(
        self,
        nodes_data: Union[List[Dict], pd.DataFrame]
    ) -> List[Dict]:
        """
        计算所有节点的 AI 评分并排序
        
        算法逻辑：
        1. 数据标准化：将延迟和负载归一化到 [0, 1] 区间
        2. 加权计算：Score = Σ(因子 × 权重)
        3. 排序输出：按分数从高到低排序
        
        Args:
            nodes_data: 节点数据，可以是字典列表或 Pandas DataFrame
                       必需字段：
                       - id: 节点 ID
                       - latency: 延迟 (毫秒)
                       - load_factor: 负载系数 (0-1)
        
        Returns:
            按 AI 评分降序排列的节点列表，每个节点包含：
            - 原始数据的所有字段
            - ai_score: 计算得出的 AI 评分 (0-1)
            - rank: 排名 (1 为最优)
        
        Example:
            >>> scheduler = AIScheduler()
            >>> nodes = [
            ...     {"id": 1, "name": "Node-A", "latency": 50, "load_factor": 0.3},
            ...     {"id": 2, "name": "Node-B", "latency": 100, "load_factor": 0.7}
            ... ]
            >>> result = scheduler.calculate_scores(nodes)
            >>> print(result[0]['name'])  # 输出最优节点名称
            'Node-A'
        """
        # 1. 数据预处理：转换为统一格式
        if isinstance(nodes_data, pd.DataFrame):
            nodes = nodes_data.to_dict('records')
        else:
            nodes = list(nodes_data)
        
        if not nodes:
            return []
        
        # 2. 提取延迟和负载数据
        latencies = [node.get('latency', 0) for node in nodes]
        loads = [node.get('load_factor', 0) for node in nodes]
        
        # 3. 数据标准化（Min-Max 归一化）
        normalized_latencies = self._normalize(latencies)
        normalized_loads = self._normalize(loads)
        
        # 4. 计算每个节点的 AI 评分
        scored_nodes = []
        for i, node in enumerate(nodes):
            # 生成随机因子 (0-1)
            # 目的：防止所有流量集中在单一最优节点
            random_factor = random.random()
            
            # 加权评分公式
            # 注意：延迟和负载越低越好，所以使用 (1 - normalized_value)
            ai_score = (
                (1 - normalized_latencies[i]) * self.latency_weight +  # 低延迟贡献
                (1 - normalized_loads[i]) * self.load_weight +          # 低负载贡献
                random_factor * self.random_weight                      # 随机扰动
            )
            
            # 将评分添加到节点数据
            node_with_score = {**node, 'ai_score': round(ai_score, 4)}
            scored_nodes.append(node_with_score)
        
        # 5. 按评分降序排序（分数越高越优）
        scored_nodes.sort(key=lambda x: x['ai_score'], reverse=True)
        
        # 6. 添加排名信息
        for rank, node in enumerate(scored_nodes, start=1):
            node['rank'] = rank
        
        return scored_nodes
    
    def _normalize(self, values: List[float]) -> List[float]:
        """
        Min-Max 归一化
        
        将数据缩放到 [0, 1] 区间，公式：
        normalized = (value - min) / (max - min)
        
        Args:
            values: 原始数值列表
        
        Returns:
            归一化后的数值列表
        
        Note:
            - 如果所有值相同，返回全 0.5（中立）
            - 处理空列表和单元素列表的边界情况
        """
        if not values:
            return []
        
        if len(values) == 1:
            return [0.5]  # 单个值无法比较，返回中间值
        
        min_val = min(values)
        max_val = max(values)
        
        # 所有值相同的情况
        if max_val == min_val:
            return [0.5] * len(values)
        
        # Min-Max 归一化公式
        normalized = [
            (val - min_val) / (max_val - min_val)
            for val in values
        ]
        
        return normalized


# ==================== 便捷函数 ====================

def calculate_scores(
    nodes_data: Union[List[Dict], pd.DataFrame],
    latency_weight: float = 0.5,
    load_weight: float = 0.3,
    random_weight: float = 0.2
) -> List[Dict]:
    """
    快捷函数：计算节点评分（无需实例化类）
    
    这是 AIScheduler.calculate_scores() 的便捷封装。
    
    Args:
        nodes_data: 节点数据列表或 DataFrame
        latency_weight: 延迟权重 (默认 0.5)
        load_weight: 负载权重 (默认 0.3)
        random_weight: 随机因子权重 (默认 0.2)
    
    Returns:
        排序后的节点列表，包含 ai_score 和 rank
    
    Example:
        >>> from backend.services import calculate_scores
        >>> nodes = [{"id": 1, "latency": 50, "load_factor": 0.3}]
        >>> result = calculate_scores(nodes)
        >>> print(result[0]['ai_score'])
        0.9234
    """
    scheduler = AIScheduler(
        latency_weight=latency_weight,
        load_weight=load_weight,
        random_weight=random_weight
    )
    return scheduler.calculate_scores(nodes_data)


# ==================== 数学原理说明 ====================
"""
算法数学原理

1. Min-Max 标准化
   公式：x' = (x - x_min) / (x_max - x_min)
   作用：将不同量纲的数据统一到 [0, 1] 区间
   例子：延迟 [20ms, 100ms, 200ms] 
         -> 归一化后 [0, 0.44, 1]

2. 加权评分
   公式：Score = Σ(w_i × f_i)
   其中：
   - w_i: 第 i 个因子的权重
   - f_i: 第 i 个因子的标准化值
   
   本系统采用：
   Score = (1 - latency_norm) × 0.5    # 延迟越低越好
         + (1 - load_norm) × 0.3       # 负载越低越好
         + random_factor × 0.2         # 随机扰动

3. 为什么使用 (1 - normalized_value)?
   因为延迟和负载是"越低越好"的指标：
   - 延迟 20ms -> 归一化 0 -> 评分贡献 (1-0) = 1.0 (最优)
   - 延迟 200ms -> 归一化 1 -> 评分贡献 (1-1) = 0.0 (最差)

4. 随机因子的作用
   - 防止流量过度集中在单一节点
   - 在多个高分节点间实现负载均衡
   - 权重较低 (0.2)，不会显著影响排序

5. 可扩展性
   未来可以加入更多因素：
   - 丢包率 (packet_loss)
   - 带宽 (bandwidth)
   - 地理位置 (geo_distance)
   只需调整权重系数即可
"""
