"""
客户端 API - 为VPN客户端/App提供接口

提供以下功能：
1. 节点列表查询（JSON 格式）
2. 通用订阅链接（Base64 编码）
3. 流量使用回调

作者: AI VPN Team
日期: 2026-02-05
"""

import base64
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, Response
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select

from backend.database import get_session
from backend.models import User, Node
from backend.utils.link_generator import generate_vless_uri


router = APIRouter(prefix="/api/v1/client", tags=["客户端 API"])


# ==================== 认证依赖 ====================

def get_current_user(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session)
) -> User:
    """
    从 Authorization Header 获取当前用户
    
    支持两种格式：
    - Bearer {token}
    - {token}
    
    Args:
        authorization: Authorization Header
        session: 数据库会话
    
    Returns:
        当前用户对象
    
    Raises:
        HTTPException: 认证失败
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="未提供认证令牌 (Missing authentication token)"
        )
    
    # 提取 token
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]  # 移除 "Bearer " 前缀
    
    # 查询用户（这里简化处理，实际应该验证 JWT 或查询 token 表）
    # 假设 token 就是用户的 email 或 UUID
    statement = select(User).where(User.email == token)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="无效的认证令牌 (Invalid authentication token)"
        )
    
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="账户已被停用 (Account disabled)"
        )
    
    # 检查流量限制
    if user.current_traffic_gb >= user.traffic_limit_gb:
        raise HTTPException(
            status_code=403,
            detail=f"流量已超限 ({user.current_traffic_gb:.2f}/{user.traffic_limit_gb} GB)"
        )
    
    return user


# ==================== 节点列表接口 ====================

@router.get("/nodes")
def get_client_nodes(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    获取当前用户可用的节点列表
    
    Returns:
        节点列表，每个节点包含：
        - id: 节点 ID
        - name: 节点名称
        - link: VLESS 订阅链接
        - ai_score: AI 评分
        - latency: 延迟（如果有监控数据）
        - load_factor: 负载系数
    
    Example Response:
        ```json
        [
            {
                "id": 1,
                "name": "HK-Node-01",
                "link": "vless://user-uuid@1.2.3.4:443?type=tcp&encryption=none#HK-Node-01",
                "ai_score": 0.95,
                "latency": 20,
                "load_factor": 0.3
            }
        ]
        ```
    """
    # 获取所有激活的节点
    statement = select(Node).where(Node.is_active == True)
    nodes = session.exec(statement).all()
    
    # 构建返回数据
    result = []
    for node in nodes:
        # 生成 VLESS 链接（使用用户 UUID）
        # 注意：这里假设 User 表有 uuid 字段，如果没有需要生成
        user_uuid = getattr(current_user, 'uuid', str(current_user.id))
        
        try:
            vless_link = generate_vless_uri(node, user_uuid)
        except Exception as e:
            # 链接生成失败，跳过该节点
            print(f"生成链接失败 (Node {node.id}): {e}")
            continue
        
        # 组装节点信息
        node_info = {
            "id": node.id,
            "name": node.name,
            "link": vless_link,
            "ai_score": node.ai_score,
            "load_factor": node.load_factor,
            "protocol": node.protocol,
        }
        
        # 如果有监控数据，添加延迟信息
        # TODO: 从 NodeMetrics 表查询最新延迟
        # latest_metric = session.exec(
        #     select(NodeMetrics)
        #     .where(NodeMetrics.node_id == node.id)
        #     .order_by(NodeMetrics.recorded_at.desc())
        # ).first()
        # if latest_metric:
        #     node_info["latency"] = latest_metric.latency
        
        result.append(node_info)
    
    # 按 AI 评分降序排序
    result.sort(key=lambda x: x.get("ai_score", 0), reverse=True)
    
    return result


# ==================== 通用订阅接口 ====================

@router.get("/subscribe", response_class=PlainTextResponse)
def get_subscription(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    获取通用订阅链接（Base64 编码）
    
    供以下客户端导入：
    - v2rayNG (Android)
    - Shadowrocket (iOS)
    - v2rayN (Windows)
    - Clash (通用)
    
    Returns:
        Base64 编码的订阅链接（纯文本）
    
    Example:
        ```
        dmxlc3M6Ly91c2VyLXV1aWRAMS4yLjMuNDo0NDM/dHlwZT10Y3AmZW5jcnlwdGlvbj1ub25lI0hLLU5vZGUtMDE=
        ```
    
    使用方法：
        1. 客户端输入订阅地址：http://your-server/api/v1/client/subscribe
        2. 设置 Authorization Header: Bearer your-token
        3. 客户端自动解析并导入节点
    """
    # 获取所有激活的节点
    statement = select(Node).where(Node.is_active == True)
    nodes = session.exec(statement).all()
    
    # 生成所有节点的链接
    links = []
    user_uuid = getattr(current_user, 'uuid', str(current_user.id))
    
    for node in nodes:
        try:
            vless_link = generate_vless_uri(node, user_uuid)
            links.append(vless_link)
        except Exception as e:
            print(f"生成链接失败 (Node {node.id}): {e}")
            continue
    
    if not links:
        raise HTTPException(
            status_code=404,
            detail="没有可用的节点 (No available nodes)"
        )
    
    # 拼接所有链接（用换行符分隔）
    subscription_text = "\n".join(links)
    
    # Base64 编码（标准订阅格式）
    encoded = base64.b64encode(subscription_text.encode('utf-8')).decode('utf-8')
    
    # 返回纯文本响应
    return PlainTextResponse(
        content=encoded,
        headers={
            "Content-Type": "text/plain; charset=utf-8",
            "Subscription-Userinfo": f"upload=0; download={int(current_user.current_traffic_gb * 1024**3)}; total={int(current_user.traffic_limit_gb * 1024**3)}",
            "Profile-Update-Interval": "24",  # 建议客户端每 24 小时更新一次
        }
    )


# ==================== 流量回调接口 ====================

@router.post("/traffic")
def update_traffic(
    bytes_used: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    更新用户流量使用情况
    
    Args:
        bytes_used: 本次使用的流量（字节）
    
    Request Body:
        ```json
        {
            "bytes_used": 1048576
        }
        ```
    
    Returns:
        更新后的用户流量信息
    
    Example Response:
        ```json
        {
            "user_id": 1,
            "current_traffic_gb": 5.23,
            "traffic_limit_gb": 100,
            "remaining_gb": 94.77,
            "percentage": 5.23
        }
        ```
    """
    # 转换字节为 GB
    gb_used = bytes_used / (1024 ** 3)
    
    # 更新用户流量
    current_user.current_traffic_gb += gb_used
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    # 计算剩余流量
    remaining_gb = current_user.traffic_limit_gb - current_user.current_traffic_gb
    percentage = (current_user.current_traffic_gb / current_user.traffic_limit_gb) * 100
    
    return {
        "user_id": current_user.id,
        "current_traffic_gb": round(current_user.current_traffic_gb, 2),
        "traffic_limit_gb": current_user.traffic_limit_gb,
        "remaining_gb": round(max(0, remaining_gb), 2),
        "percentage": round(percentage, 2),
        "updated_at": datetime.now().isoformat()
    }


# ==================== 用户信息接口 ====================

@router.get("/user/info")
def get_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息
    
    Returns:
        用户基本信息和流量使用情况
    """
    remaining_gb = current_user.traffic_limit_gb - current_user.current_traffic_gb
    percentage = (current_user.current_traffic_gb / current_user.traffic_limit_gb) * 100
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "balance": current_user.balance,
        "traffic": {
            "used_gb": round(current_user.current_traffic_gb, 2),
            "total_gb": current_user.traffic_limit_gb,
            "remaining_gb": round(max(0, remaining_gb), 2),
            "percentage": round(percentage, 2)
        },
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if hasattr(current_user, 'created_at') else None
    }
