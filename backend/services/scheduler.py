"""
AI 智能调度服务

负责定期计算节点的 AI 评分，用于智能推荐最优节点。

评分逻辑：
- 延迟得分 (40%): 延迟越低分越高
- 负载得分 (30%): CPU/负载越低分越高  
- 稳定性得分 (30%): 丢包率越低分越高
- 晚高峰惩罚: 拥堵时段扣减 20 分

作者: AI VPN Team
日期: 2026-02-05
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from statistics import mean

from sqlmodel import Session, select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.database import get_session
from backend.models import Node, NodeMetrics


logger = logging.getLogger(__name__)


class AISchedulerService:
    """
    AI 智能调度服务
    
    负责定期计算和更新节点的 AI 评分
    """
    
    def __init__(self, interval_seconds: int = 60):
        """
        初始化调度服务
        
        Args:
            interval_seconds: 调度间隔（秒），默认 60 秒
        """
        self.interval_seconds = interval_seconds
        self.scheduler = AsyncIOScheduler()
        
    def start(self):
        """启动定时调度"""
        logger.info("🤖 启动 AI 调度服务...")
        
        # 添加定时任务
        self.scheduler.add_job(
            self.update_all_nodes_scores,
            trigger=IntervalTrigger(seconds=self.interval_seconds),
            id='update_node_scores',
            name='更新节点 AI 评分',
            replace_existing=True
        )
        
        # 启动调度器
        self.scheduler.start()
        logger.info(f"✅ AI 调度服务已启动，每 {self.interval_seconds} 秒更新一次")
        
        # 立即执行一次
        self.update_all_nodes_scores()
    
    def stop(self):
        """停止调度服务"""
        logger.info("🛑 停止 AI 调度服务...")
        self.scheduler.shutdown()
        logger.info("✅ AI 调度服务已停止")
    
    def update_all_nodes_scores(self):
        """
        更新所有节点的 AI 评分
        
        这是定时任务的主要执行函数
        """
        logger.info("=" * 60)
        logger.info("📊 开始更新节点 AI 评分...")
        
        with next(get_session()) as session:
            # 获取所有活跃节点
            statement = select(Node).where(Node.is_active == True)
            nodes = session.exec(statement).all()
            
            if not nodes:
                logger.warning("⚠️  没有找到活跃节点")
                return
            
            logger.info(f"📌 找到 {len(nodes)} 个活跃节点")
            
            # 计算每个节点的评分
            updated_count = 0
            for node in nodes:
                try:
                    # 获取节点的监控数据
                    metrics = self.get_recent_metrics(session, node.id)
                    
                    if not metrics:
                        logger.warning(f"⚠️  节点 {node.name} (ID:{node.id}) 没有监控数据")
                        continue
                    
                    # 计算 AI 评分
                    score = self.calculate_node_score(node, metrics)
                    
                    # 更新数据库
                    node.ai_score = score
                    session.add(node)
                    
                    logger.info(f"  ✅ {node.name}: {score:.2f}/100")
                    updated_count += 1
                
                except Exception as e:
                    logger.error(f"❌ 更新节点 {node.name} 失败: {e}")
            
            # 提交事务
            session.commit()
            
            logger.info(f"✅ 成功更新 {updated_count}/{len(nodes)} 个节点的评分")
            logger.info("=" * 60)
    
    def get_recent_metrics(
        self,
        session: Session,
        node_id: int,
        minutes: int = 5
    ) -> List[NodeMetrics]:
        """
        获取节点最近的监控数据
        
        Args:
            session: 数据库会话
            node_id: 节点 ID
            minutes: 时间范围（分钟），默认 5 分钟
        
        Returns:
            监控记录列表
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        
        statement = select(NodeMetrics).where(
            NodeMetrics.node_id == node_id,
            NodeMetrics.recorded_at >= cutoff_time
        ).order_by(NodeMetrics.recorded_at.desc())
        
        metrics = session.exec(statement).all()
        return list(metrics)
    
    def calculate_node_score(
        self,
        node: Node,
        metrics: List[NodeMetrics]
    ) -> float:
        """
        计算节点的 AI 评分
        
        评分公式：
        - 延迟得分 (40%): 延迟越低分越高
        - 负载得分 (30%): 负载越低分越高
        - 稳定性得分 (30%): 丢包率越低分越高
        - 晚高峰惩罚: -20 分
        
        Args:
            node: 节点对象
            metrics: 监控数据列表
        
        Returns:
            AI 评分 (0-100)
        """
        # 1. 延迟得分 (40%)
        latency_score = self.calculate_latency_score(metrics)
        
        # 2. 负载得分 (30%)
        load_score = self.calculate_load_score(node, metrics)
        
        # 3. 稳定性得分 (30%)
        stability_score = self.calculate_stability_score(metrics)
        
        # 4. 加权总分
        total_score = (
            latency_score * 0.4 +
            load_score * 0.3 +
            stability_score * 0.3
        )
        
        # 5. 晚高峰惩罚
        if self.is_peak_hour_congestion(metrics):
            logger.debug(f"  🕐 {node.name} 检测到晚高峰拥堵，扣减 20 分")
            total_score -= 20
        
        # 6. 确保分数在 0-100 之间
        total_score = max(0, min(100, total_score))
        
        return round(total_score, 2)
    
    def calculate_latency_score(self, metrics: List[NodeMetrics]) -> float:
        """
        计算延迟得分
        
        公式: score = 100 / (avg_latency + 1)
        
        Args:
            metrics: 监控数据列表
        
        Returns:
            延迟得分 (0-100)
        """
        if not metrics:
            return 0
        
        # 提取所有延迟值
        latencies = [m.latency for m in metrics if m.latency is not None]
        
        if not latencies:
            return 0
        
        # 计算平均延迟
        avg_latency = mean(latencies)
        
        # 计算得分（延迟越低分越高）
        score = 100 / (avg_latency + 1)
        
        # 归一化到 0-100
        score = min(100, score * 10)  # 放大系数，让低延迟更明显
        
        return score
    
    def calculate_load_score(
        self,
        node: Node,
        metrics: List[NodeMetrics]
    ) -> float:
        """
        计算负载得分
        
        公式: score = 100 - (load_factor * 100)
        
        Args:
            node: 节点对象
            metrics: 监控数据列表
        
        Returns:
            负载得分 (0-100)
        """
        # 使用节点当前的负载系数
        load_factor = node.load_factor
        
        # 如果有 CPU 使用率数据，也考虑进来
        # TODO: 从 metrics 中提取 CPU 使用率
        # 目前简化处理，只用 load_factor
        
        score = 100 - (load_factor * 100)
        
        return max(0, score)
    
    def calculate_stability_score(self, metrics: List[NodeMetrics]) -> float:
        """
        计算稳定性得分
        
        基于丢包率计算
        
        Args:
            metrics: 监控数据列表
        
        Returns:
            稳定性得分 (0-100)
        """
        if not metrics:
            return 0
        
        # 提取丢包率
        packet_losses = [
            m.packet_loss for m in metrics
            if m.packet_loss is not None
        ]
        
        if not packet_losses:
            # 如果没有丢包率数据，默认给 80 分
            return 80
        
        # 计算平均丢包率
        avg_packet_loss = mean(packet_losses)
        
        # 计算得分（丢包率越低分越高）
        # 假设丢包率是 0-1 的比例
        score = (1 - avg_packet_loss) * 100
        
        return max(0, score)
    
    def is_peak_hour_congestion(self, metrics: List[NodeMetrics]) -> bool:
        """
        检测是否为晚高峰拥堵时段
        
        判断逻辑：
        1. 当前时间是否为晚高峰 (18:00-23:00)
        2. 最近的延迟是否显著高于平均值
        
        Args:
            metrics: 监控数据列表
        
        Returns:
            是否为晚高峰拥堵
        """
        # 1. 检查当前时间
        current_hour = datetime.now().hour
        is_peak_time = 18 <= current_hour <= 23
        
        if not is_peak_time:
            return False
        
        # 2. 检查延迟是否异常高
        if len(metrics) < 10:
            return False
        
        latencies = [m.latency for m in metrics if m.latency is not None]
        
        if len(latencies) < 10:
            return False
        
        # 最近 3 个的平均延迟
        recent_latencies = latencies[:3]
        recent_avg = mean(recent_latencies)
        
        # 历史平均延迟
        historical_avg = mean(latencies)
        
        # 如果最近延迟比历史平均高 50% 以上，认为拥堵
        if recent_avg > historical_avg * 1.5:
            return True
        
        return False


# ==================== 全局实例 ====================

# 创建全局调度服务实例
scheduler_service = AISchedulerService(interval_seconds=60)


# ==================== 便捷函数 ====================

def start_scheduler():
    """启动 AI 调度服务"""
    scheduler_service.start()


def stop_scheduler():
    """停止 AI 调度服务"""
    scheduler_service.stop()


def update_scores_now():
    """立即更新所有节点评分（手动触发）"""
    scheduler_service.update_all_nodes_scores()
