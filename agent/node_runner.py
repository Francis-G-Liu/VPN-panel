#!/usr/bin/env python3
"""
VPN 节点监控脚本 - 生产版本

功能：
- 系统资源监控（CPU、内存、网络流量）
- 网络延迟测试
- 定期向后端汇报心跳数据

部署：
1. 修改下方配置常量
2. pip install requests psutil ping3
3. python node_runner.py

作者: AI VPN Team
日期: 2026-02-05
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

try:
    import psutil
    import requests
    from ping3 import ping
except ImportError as e:
    print(f"❌ 缺少依赖库: {e}")
    print("请运行: pip install requests psutil ping3")
    sys.exit(1)


# ==================== 配置常量 ====================

# 后端 API 配置
API_ENDPOINT = os.getenv(
    "API_ENDPOINT",
    "http://localhost:8000/api/v1/node/heartbeat"
)

# 节点认证
NODE_KEY = os.getenv("NODE_KEY", "your-node-secret-key")
NODE_ID = os.getenv("NODE_ID", "node-001")

# 汇报间隔（秒）
REPORT_INTERVAL = int(os.getenv("REPORT_INTERVAL", "15"))

# 延迟测试目标
PING_TARGETS = [
    "8.8.8.8",           # Google DNS
    "www.google.com",    # Google 网站
    "api.openai.com"     # OpenAI API
]

# 超时时间（秒）
PING_TIMEOUT = 2
HTTP_TIMEOUT = 5

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ==================== 日志设置 ====================

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('node_runner.log')
    ]
)
logger = logging.getLogger(__name__)


# ==================== 监控功能函数 ====================

def get_system_status() -> Dict:
    """
    获取系统状态信息
    
    Returns:
        包含系统状态的字典：
        - cpu_percent: CPU 使用率 (%)
        - memory_percent: 内存使用率 (%)
        - network_tx_kbps: 网络发送速率 (KB/s)
        - network_rx_kbps: 网络接收速率 (KB/s)
    """
    try:
        # CPU 使用率（测量 1 秒间隔）
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # 网络流量速率
        # 第一次采样
        net_io_1 = psutil.net_io_counters()
        bytes_sent_1 = net_io_1.bytes_sent
        bytes_recv_1 = net_io_1.bytes_recv
        
        # 等待 1 秒
        time.sleep(1)
        
        # 第二次采样
        net_io_2 = psutil.net_io_counters()
        bytes_sent_2 = net_io_2.bytes_sent
        bytes_recv_2 = net_io_2.bytes_recv
        
        # 计算速率 (KB/s)
        network_tx_kbps = (bytes_sent_2 - bytes_sent_1) / 1024
        network_rx_kbps = (bytes_recv_2 - bytes_recv_1) / 1024
        
        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory_percent, 2),
            "network_tx_kbps": round(network_tx_kbps, 2),
            "network_rx_kbps": round(network_rx_kbps, 2)
        }
    
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "network_tx_kbps": 0,
            "network_rx_kbps": 0
        }


def check_network_latency() -> Dict[str, float]:
    """
    检测网络延迟
    
    测试到多个目标的延迟，如果超时返回 9999
    
    Returns:
        延迟字典，key 为目标主机，value 为延迟（毫秒）
    """
    latencies = {}
    
    for target in PING_TARGETS:
        try:
            # ping3.ping 返回秒数，需要转换为毫秒
            delay = ping(target, timeout=PING_TIMEOUT)
            
            if delay is None or delay is False:
                # 超时或失败
                latencies[target] = 9999
                logger.warning(f"Ping {target} 超时")
            else:
                # 转换为毫秒
                latencies[target] = round(delay * 1000, 2)
                logger.debug(f"Ping {target}: {latencies[target]}ms")
        
        except Exception as e:
            logger.error(f"Ping {target} 异常: {e}")
            latencies[target] = 9999
    
    return latencies


def get_average_latency(latencies: Dict[str, float]) -> float:
    """
    计算平均延迟（排除超时的）
    
    Args:
        latencies: 延迟字典
    
    Returns:
        平均延迟（毫秒），如果全部超时返回 9999
    """
    valid_latencies = [lat for lat in latencies.values() if lat < 9999]
    
    if not valid_latencies:
        return 9999
    
    return round(sum(valid_latencies) / len(valid_latencies), 2)


# ==================== 数据上报 ====================

def collect_metrics() -> Dict:
    """
    收集所有监控指标
    
    Returns:
        完整的监控数据字典
    """
    logger.info("📊 收集监控数据...")
    
    # 1. 系统状态
    system_status = get_system_status()
    
    # 2. 网络延迟
    latencies = check_network_latency()
    avg_latency = get_average_latency(latencies)
    
    # 3. 组装数据
    metrics = {
        "node_id": NODE_ID,
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": system_status["cpu_percent"],
            "memory_percent": system_status["memory_percent"],
            "network_tx_kbps": system_status["network_tx_kbps"],
            "network_rx_kbps": system_status["network_rx_kbps"]
        },
        "network": {
            "latencies": latencies,
            "average_latency_ms": avg_latency
        }
    }
    
    logger.info(
        f"  CPU: {system_status['cpu_percent']}% | "
        f"内存: {system_status['memory_percent']}% | "
        f"延迟: {avg_latency}ms"
    )
    
    return metrics


def send_heartbeat(metrics: Dict) -> bool:
    """
    发送心跳数据到后端
    
    Args:
        metrics: 监控指标数据
    
    Returns:
        发送成功返回 True，失败返回 False
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "X-Node-Key": NODE_KEY  # 节点认证密钥
        }
        
        response = requests.post(
            API_ENDPOINT,
            json=metrics,
            headers=headers,
            timeout=HTTP_TIMEOUT
        )
        
        if response.status_code == 200:
            logger.info("✅ 心跳发送成功")
            return True
        else:
            logger.error(
                f"❌ 心跳发送失败: HTTP {response.status_code} - {response.text}"
            )
            return False
    
    except requests.exceptions.Timeout:
        logger.error("❌ 请求超时")
        return False
    
    except requests.exceptions.ConnectionError:
        logger.error("❌ 无法连接到后端服务器")
        return False
    
    except Exception as e:
        logger.error(f"❌ 发送心跳异常: {e}")
        return False


# ==================== 主程序 ====================

def main():
    """主程序入口"""
    logger.info("=" * 60)
    logger.info("🚀 VPN 节点监控脚本启动")
    logger.info("=" * 60)
    logger.info(f"节点 ID: {NODE_ID}")
    logger.info(f"后端 API: {API_ENDPOINT}")
    logger.info(f"汇报间隔: {REPORT_INTERVAL} 秒")
    logger.info(f"延迟测试目标: {', '.join(PING_TARGETS)}")
    logger.info("=" * 60)
    
    # 连续失败计数器
    consecutive_failures = 0
    max_failures = 5
    
    try:
        while True:
            try:
                # 1. 收集监控数据
                metrics = collect_metrics()
                
                # 2. 发送心跳
                success = send_heartbeat(metrics)
                
                # 3. 处理结果
                if success:
                    consecutive_failures = 0  # 重置失败计数
                else:
                    consecutive_failures += 1
                    logger.warning(f"⚠️  连续失败 {consecutive_failures} 次")
                
                # 4. 如果连续失败过多，增加等待时间
                if consecutive_failures >= max_failures:
                    wait_time = REPORT_INTERVAL * 3
                    logger.warning(
                        f"⚠️  连续失败达到 {max_failures} 次，"
                        f"等待 {wait_time} 秒后重试"
                    )
                    time.sleep(wait_time)
                    consecutive_failures = 0  # 重置
                else:
                    # 正常等待
                    logger.debug(f"⏰ 等待 {REPORT_INTERVAL} 秒...")
                    time.sleep(REPORT_INTERVAL)
            
            except KeyboardInterrupt:
                raise  # 传递到外层处理
            
            except Exception as e:
                logger.error(f"❌ 循环中发生异常: {e}", exc_info=True)
                consecutive_failures += 1
                time.sleep(REPORT_INTERVAL)
    
    except KeyboardInterrupt:
        logger.info("\n👋 收到退出信号，正在关闭...")
    
    finally:
        logger.info("✅ 监控脚本已停止")


# ==================== 程序入口 ====================

if __name__ == "__main__":
    # 环境变量提示
    if NODE_KEY == "your-node-secret-key":
        logger.warning("⚠️  警告: 使用默认 NODE_KEY，请设置环境变量 NODE_KEY")
    
    if API_ENDPOINT == "http://localhost:8000/api/v1/node/heartbeat":
        logger.warning("⚠️  警告: 使用默认 API_ENDPOINT，请设置环境变量 API_ENDPOINT")
    
    # 启动主程序
    main()
