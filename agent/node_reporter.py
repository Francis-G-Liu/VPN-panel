"""
VPN 节点状态汇报 Agent

该脚本运行在 VPN 节点服务器上，负责：
1. 监控系统资源（CPU、内存、网络流量）
2. 测试网络延迟
3. 定期向主控端发送心跳数据
4. 提供健壮的错误处理和重试机制

作者: AI VPN Team
日期: 2026-02-05
"""

import os
import sys
import time
import json
import platform
import subprocess
import logging
from typing import Dict, Optional
from datetime import datetime

import psutil
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ==================== 配置 ====================

# 主控端 API 地址
CONTROL_SERVER_URL = os.getenv("CONTROL_SERVER_URL", "http://localhost:8000")
HEARTBEAT_ENDPOINT = f"{CONTROL_SERVER_URL}/api/v1/node/heartbeat"

# 节点标识
NODE_ID = os.getenv("NODE_ID", "unknown-node")
NODE_NAME = os.getenv("NODE_NAME", platform.node())
NODE_SECRET = os.getenv("NODE_SECRET", "")  # 节点认证密钥

# 汇报间隔（秒）
REPORT_INTERVAL = int(os.getenv("REPORT_INTERVAL", "10"))

# 延迟测试目标
PING_TARGETS = [
    "8.8.8.8",        # Google DNS
    "1.1.1.1",        # Cloudflare DNS
]

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ==================== 日志设置 ====================

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('node_reporter.log')
    ]
)
logger = logging.getLogger(__name__)


# ==================== HTTP 客户端配置 ====================

def create_http_session() -> requests.Session:
    """
    创建带重试机制的 HTTP Session
    
    Returns:
        配置好的 requests.Session 对象
    """
    session = requests.Session()
    
    # 配置重试策略
    retry_strategy = Retry(
        total=3,                          # 总重试次数
        backoff_factor=1,                 # 重试间隔递增因子
        status_forcelist=[500, 502, 503, 504],  # 需要重试的 HTTP 状态码
        allowed_methods=["POST"]          # 允许重试的方法
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


# ==================== 系统监控函数 ====================

def get_cpu_usage() -> float:
    """
    获取 CPU 使用率
    
    Returns:
        CPU 使用率百分比 (0-100)
    """
    try:
        # interval=1 表示测量 1 秒内的平均 CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        return round(cpu_percent, 2)
    except Exception as e:
        logger.error(f"获取 CPU 使用率失败: {e}")
        return 0.0


def get_memory_usage() -> Dict[str, float]:
    """
    获取内存使用情况
    
    Returns:
        内存使用信息字典
    """
    try:
        mem = psutil.virtual_memory()
        return {
            "total_mb": round(mem.total / 1024 / 1024, 2),
            "used_mb": round(mem.used / 1024 / 1024, 2),
            "percent": round(mem.percent, 2)
        }
    except Exception as e:
        logger.error(f"获取内存使用率失败: {e}")
        return {"total_mb": 0, "used_mb": 0, "percent": 0}


def get_network_traffic() -> Dict[str, int]:
    """
    获取网络流量统计
    
    Returns:
        网络流量字典（接收和发送的字节数）
    """
    try:
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
    except Exception as e:
        logger.error(f"获取网络流量失败: {e}")
        return {
            "bytes_sent": 0,
            "bytes_recv": 0,
            "packets_sent": 0,
            "packets_recv": 0
        }


def get_disk_usage() -> Dict[str, float]:
    """
    获取磁盘使用情况
    
    Returns:
        磁盘使用信息字典
    """
    try:
        disk = psutil.disk_usage('/')
        return {
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
            "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
            "percent": round(disk.percent, 2)
        }
    except Exception as e:
        logger.error(f"获取磁盘使用率失败: {e}")
        return {"total_gb": 0, "used_gb": 0, "percent": 0}


# ==================== 网络延迟测试 ====================

def ping_host(host: str, count: int = 1, timeout: int = 2) -> Optional[float]:
    """
    Ping 指定主机测试延迟
    
    使用系统 ping 命令实现跨平台兼容
    
    Args:
        host: 目标主机 IP 或域名
        count: ping 次数
        timeout: 超时时间（秒）
    
    Returns:
        平均延迟（毫秒），失败返回 None
    """
    try:
        # 根据操作系统选择 ping 命令参数
        system = platform.system().lower()
        
        if system == "windows":
            # Windows: ping -n 1 -w 2000 8.8.8.8
            cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
        else:
            # Linux/Mac: ping -c 1 -W 2 8.8.8.8
            cmd = ["ping", "-c", str(count), "-W", str(timeout), host]
        
        # 执行 ping 命令
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 1,
            text=True
        )
        
        if result.returncode != 0:
            return None
        
        # 解析 ping 结果提取延迟
        output = result.stdout
        
        if system == "windows":
            # Windows: "平均 = 20ms" 或 "Average = 20ms"
            for line in output.split('\n'):
                if '平均' in line or 'Average' in line:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        latency_str = parts[-1].strip().replace('ms', '').strip()
                        try:
                            return float(latency_str)
                        except ValueError:
                            pass
        else:
            # Linux/Mac: "rtt min/avg/max/mdev = 19.123/20.456/21.789/1.234 ms"
            for line in output.split('\n'):
                if 'rtt' in line or 'round-trip' in line:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        stats = parts[-1].strip().split('/')
                        if len(stats) >= 2:
                            try:
                                return float(stats[1])  # avg
                            except ValueError:
                                pass
        
        return None
        
    except subprocess.TimeoutExpired:
        logger.warning(f"Ping {host} 超时")
        return None
    except Exception as e:
        logger.error(f"Ping {host} 失败: {e}")
        return None


def measure_latency() -> Dict[str, Optional[float]]:
    """
    测试到多个目标的网络延迟
    
    Returns:
        延迟字典，key 为目标主机，value 为延迟（毫秒）
    """
    latencies = {}
    
    for target in PING_TARGETS:
        latency = ping_host(target)
        latencies[target] = latency
        if latency:
            logger.debug(f"Ping {target}: {latency}ms")
        else:
            logger.warning(f"Ping {target}: 失败")
    
    return latencies


def get_average_latency() -> Optional[float]:
    """
    获取平均延迟
    
    Returns:
        所有成功测试的平均延迟（毫秒），全部失败返回 None
    """
    latencies = measure_latency()
    valid_latencies = [lat for lat in latencies.values() if lat is not None]
    
    if not valid_latencies:
        return None
    
    avg = sum(valid_latencies) / len(valid_latencies)
    return round(avg, 2)


# ==================== 数据汇报 ====================

def collect_metrics() -> Dict:
    """
    收集所有监控指标
    
    Returns:
        包含所有指标的字典
    """
    logger.info("📊 收集系统指标...")
    
    # 收集各项指标
    cpu_usage = get_cpu_usage()
    memory_usage = get_memory_usage()
    network_traffic = get_network_traffic()
    disk_usage = get_disk_usage()
    latency = get_average_latency()
    
    # 组装数据
    metrics = {
        "node_id": NODE_ID,
        "node_name": NODE_NAME,
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "hostname": platform.node(),
        },
        "cpu": {
            "usage_percent": cpu_usage
        },
        "memory": memory_usage,
        "disk": disk_usage,
        "network": network_traffic,
        "latency_ms": latency,
    }
    
    logger.info(f"  CPU: {cpu_usage}% | "
                f"内存: {memory_usage['percent']}% | "
                f"延迟: {latency}ms" if latency else "延迟: N/A")
    
    return metrics


def send_heartbeat(session: requests.Session, metrics: Dict) -> bool:
    """
    发送心跳数据到主控端
    
    Args:
        session: HTTP Session 对象
        metrics: 监控指标数据
    
    Returns:
        发送成功返回 True，失败返回 False
    """
    try:
        headers = {
            "Content-Type": "application/json",
        }
        
        # 如果配置了节点密钥，添加认证
        if NODE_SECRET:
            headers["X-Node-Secret"] = NODE_SECRET
        
        # 发送 POST 请求
        response = session.post(
            HEARTBEAT_ENDPOINT,
            json=metrics,
            headers=headers,
            timeout=5
        )
        
        # 检查响应
        if response.status_code == 200:
            logger.info(f"✅ 心跳发送成功")
            return True
        else:
            logger.error(f"❌ 心跳发送失败: HTTP {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("❌ 心跳发送超时")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ 无法连接到主控端")
        return False
    except Exception as e:
        logger.error(f"❌ 心跳发送异常: {e}")
        return False


# ==================== 主循环 ====================

def main():
    """主程序入口"""
    logger.info("=" * 60)
    logger.info("🚀 VPN 节点状态汇报 Agent 启动")
    logger.info("=" * 60)
    logger.info(f"节点 ID: {NODE_ID}")
    logger.info(f"节点名称: {NODE_NAME}")
    logger.info(f"主控端地址: {CONTROL_SERVER_URL}")
    logger.info(f"汇报间隔: {REPORT_INTERVAL} 秒")
    logger.info("=" * 60)
    
    # 创建 HTTP Session
    session = create_http_session()
    
    # 连续失败计数器
    consecutive_failures = 0
    max_consecutive_failures = 5
    
    try:
        while True:
            try:
                # 1. 收集指标
                metrics = collect_metrics()
                
                # 2. 发送心跳
                success = send_heartbeat(session, metrics)
                
                # 3. 处理结果
                if success:
                    consecutive_failures = 0  # 重置失败计数
                else:
                    consecutive_failures += 1
                    logger.warning(f"⚠️  连续失败 {consecutive_failures} 次")
                
                # 4. 如果连续失败过多，增加等待时间
                if consecutive_failures >= max_consecutive_failures:
                    wait_time = REPORT_INTERVAL * 3
                    logger.warning(f"⚠️  连续失败达到 {max_consecutive_failures} 次，"
                                   f"等待 {wait_time} 秒后重试")
                    time.sleep(wait_time)
                    consecutive_failures = 0  # 重置计数器
                else:
                    # 正常等待
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
        session.close()
        logger.info("✅ Agent 已停止")


if __name__ == "__main__":
    main()
