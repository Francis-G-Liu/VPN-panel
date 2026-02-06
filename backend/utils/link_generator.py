"""
VLESS/VPN 链接生成器

基于 urlclash-converter 的逻辑生成标准的 VLESS 订阅链接
支持 Reality/TLS/WS/GRPC 等传输协议

作者: AI VPN Team
日期: 2026-02-05
"""

import json
import urllib.parse
from typing import Dict, Any, Optional


def generate_vless_uri(node, user_uuid: str) -> str:
    """
    基于 urlclash-converter 的逻辑生成 VLESS 链接
    
    Args:
        node: SQLModel 节点对象 (需包含 ip, port, name, config_json)
        user_uuid: 用户 UUID (作为 VLESS 的 UUID)
    
    Returns:
        完整的 VLESS URI 字符串
        格式: vless://uuid@ip:port?params#name
    
    Example:
        >>> node = Node(ip="1.2.3.4", port=443, name="HK-Node", config_json='{"tls": true}')
        >>> uri = generate_vless_uri(node, "your-user-uuid")
        >>> print(uri)
        vless://your-user-uuid@1.2.3.4:443?type=tcp&encryption=none&security=tls#HK-Node
    """
    # 1. 解析节点配置
    if hasattr(node, 'config_json') and node.config_json:
        try:
            config = json.loads(node.config_json) if isinstance(node.config_json, str) else node.config_json
        except (json.JSONDecodeError, TypeError):
            config = {}
    else:
        config = {}
    
    # 2. 基础信息
    server = node.ip
    port = node.port
    name = urllib.parse.quote(node.name)  # URL 编码节点名称
    
    # 3. 构建参数字典
    params: Dict[str, str] = {}
    
    # 传输协议类型 (type)
    network = config.get("network", "tcp")
    params["type"] = network
    
    # VLESS 固定加密方式为 none
    params["encryption"] = "none"
    
    # Flow (用于 XTLS)
    flow = config.get("flow")
    if flow:
        params["flow"] = flow
    
    # 4. 安全层 (TLS / Reality)
    security = "none"
    
    # 检测 TLS
    if config.get("tls"):
        security = "tls"
    
    # 检测 Reality (优先级更高)
    if config.get("reality-opts"):
        security = "reality"
    
    if security != "none":
        params["security"] = security
    
    # SNI (Server Name Indication)
    sni = config.get("servername") or config.get("sni")
    if sni:
        params["sni"] = sni
    
    # Fingerprint (用于 TLS 指纹伪造)
    fp = config.get("fingerprint") or config.get("client-fingerprint")
    if fp:
        params["fp"] = fp
    
    # ALPN (Application-Layer Protocol Negotiation)
    alpn = config.get("alpn")
    if alpn:
        if isinstance(alpn, list):
            params["alpn"] = ",".join(alpn)
        else:
            params["alpn"] = alpn
    
    # 跳过证书验证
    if config.get("skip-cert-verify"):
        params["allowInsecure"] = "1"
    
    # Reality 专用参数
    if security == "reality":
        ro = config.get("reality-opts", {})
        
        if ro.get("public-key"):
            params["pbk"] = ro["public-key"]
        
        if ro.get("short-id"):
            params["sid"] = ro["short-id"]
        
        if ro.get("spider-x"):
            params["spx"] = ro["spider-x"]
        
        if ro.get("mldsa65-verify"):
            params["pqv"] = ro["mldsa65-verify"]
    
    # 5. 传输层参数 (WS / GRPC / HTTP)
    
    if network == "ws":
        # WebSocket 配置
        ws_opts = config.get("ws-opts", {})
        
        # WS Host
        host = ws_opts.get("headers", {}).get("Host")
        if host:
            params["host"] = host
        
        # WS Path
        path = ws_opts.get("path")
        if path:
            params["path"] = path
    
    elif network == "grpc":
        # gRPC 配置
        grpc_opts = config.get("grpc-opts", {})
        
        service_name = grpc_opts.get("grpc-service-name")
        if service_name:
            params["serviceName"] = service_name
    
    elif network == "http" or network == "h2":
        # HTTP/H2 配置
        http_opts = config.get("http-opts", {}) or config.get("h2-opts", {})
        
        # HTTP Host
        host = http_opts.get("headers", {}).get("Host")
        if host:
            if isinstance(host, list):
                params["host"] = host[0]
            else:
                params["host"] = host
        
        # HTTP Path
        path = http_opts.get("path")
        if path:
            if isinstance(path, list):
                params["path"] = path[0]
            else:
                params["path"] = path
    
    # 6. 拼接最终链接
    # 格式: vless://uuid@ip:port?params#name
    query = urllib.parse.urlencode(params)
    vless_link = f"vless://{user_uuid}@{server}:{port}?{query}#{name}"
    
    return vless_link


def generate_vmess_uri(node, user_uuid: str, alter_id: int = 0) -> str:
    """
    生成 VMess 链接 (JSON 格式 Base64 编码)
    
    Args:
        node: SQLModel 节点对象
        user_uuid: 用户 UUID
        alter_id: alterId (通常为 0)
    
    Returns:
        VMess URI 字符串
    """
    import base64
    
    # 解析配置
    config = {}
    if hasattr(node, 'config_json') and node.config_json:
        try:
            config = json.loads(node.config_json) if isinstance(node.config_json, str) else node.config_json
        except:
            config = {}
    
    # 构建 VMess JSON
    vmess_config = {
        "v": "2",
        "ps": node.name,  # 备注名
        "add": node.ip,   # 服务器地址
        "port": str(node.port),
        "id": user_uuid,
        "aid": str(alter_id),
        "net": config.get("network", "tcp"),
        "type": "none",
        "host": "",
        "path": "",
        "tls": "tls" if config.get("tls") else "",
    }
    
    # WS 配置
    if config.get("network") == "ws":
        ws_opts = config.get("ws-opts", {})
        vmess_config["host"] = ws_opts.get("headers", {}).get("Host", "")
        vmess_config["path"] = ws_opts.get("path", "")
    
    # JSON 转 Base64
    json_str = json.dumps(vmess_config, separators=(',', ':'))
    b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    
    return f"vmess://{b64_str}"


def generate_trojan_uri(node, user_password: str) -> str:
    """
    生成 Trojan 链接
    
    Args:
        node: SQLModel 节点对象
        user_password: 用户密码
    
    Returns:
        Trojan URI 字符串
    """
    # 解析配置
    config = {}
    if hasattr(node, 'config_json') and node.config_json:
        try:
            config = json.loads(node.config_json) if isinstance(node.config_json, str) else node.config_json
        except:
            config = {}
    
    # 基础信息
    server = node.ip
    port = node.port
    name = urllib.parse.quote(node.name)
    
    # 构建参数
    params: Dict[str, str] = {}
    
    network = config.get("network", "tcp")
    if network != "tcp":
        params["type"] = network
    
    # SNI
    sni = config.get("sni") or config.get("servername")
    if sni:
        params["sni"] = sni
    
    # WS 配置
    if network == "ws":
        ws_opts = config.get("ws-opts", {})
        host = ws_opts.get("headers", {}).get("Host")
        if host:
            params["host"] = host
        path = ws_opts.get("path")
        if path:
            params["path"] = path
    
    # 拼接链接
    if params:
        query = urllib.parse.urlencode(params)
        return f"trojan://{urllib.parse.quote(user_password)}@{server}:{port}?{query}#{name}"
    else:
        return f"trojan://{urllib.parse.quote(user_password)}@{server}:{port}#{name}"
