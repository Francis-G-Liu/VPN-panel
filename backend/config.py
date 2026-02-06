"""
AI VPN 管理系统 - 配置管理模块

使用 Pydantic Settings 集中管理所有配置项
支持环境变量和 .env 文件
自动生成数据库和 Redis 连接字符串
"""

from typing import Optional
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    应用配置类
    
    所有配置项通过环境变量或 .env 文件加载
    敏感信息（密钥、密码）必须在生产环境中设置
    """
    
    # ==================== 基础设置 ====================
    PROJECT_NAME: str = Field(
        default="AI VPN Management System",
        description="项目名称"
    )
    
    DOMAIN: Optional[str] = Field(
        default=None,
        description="部署域名，例如: vpn.example.com"
    )
    
    ENVIRONMENT: str = Field(
        default="production",
        description="运行环境: development, staging, production"
    )
    
    API_V1_STR: str = Field(
        default="/api/v1",
        description="API v1 路由前缀"
    )
    
    # ==================== 安全设置 ====================
    SECRET_KEY: str = Field(
        default="CHANGE-THIS-SECRET-KEY-IN-PRODUCTION",
        description="JWT 密钥，生产环境必须修改！"
    )
    
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT 加密算法"
    )
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440,  # 24小时
        description="访问令牌过期时间（分钟）"
    )
    
    ADMIN_SECRET: str = Field(
        default="CHANGE-THIS-ADMIN-SECRET",
        description="管理后台安全密钥"
    )
    
    NODE_COMMUNICATION_KEY: str = Field(
        default="CHANGE-THIS-NODE-KEY",
        description="节点通信密钥"
    )
    
    # ==================== 初始化设置 ====================
    FIRST_SUPERUSER: str = Field(
        default="admin@example.com",
        description="初始超级管理员邮箱"
    )
    
    FIRST_SUPERUSER_PASSWORD: str = Field(
        default="changeme",
        description="初始超级管理员密码"
    )
    
    # ==================== PostgreSQL 数据库 ====================
    POSTGRES_SERVER: str = Field(
        default="localhost",
        description="PostgreSQL 服务器地址"
    )
    
    POSTGRES_PORT: int = Field(
        default=5432,
        description="PostgreSQL 端口"
    )
    
    POSTGRES_USER: str = Field(
        default="vpn_user",
        description="PostgreSQL 用户名"
    )
    
    POSTGRES_PASSWORD: str = Field(
        default="",
        description="PostgreSQL 密码"
    )
    
    POSTGRES_DB: str = Field(
        default="vpn_db",
        description="PostgreSQL 数据库名"
    )
    
    # SQLite 备选方案（开发环境）
    USE_SQLITE: bool = Field(
        default=False,
        description="是否使用 SQLite（开发环境）"
    )
    
    SQLITE_PATH: str = Field(
        default="./vpn_management.db",
        description="SQLite 数据库文件路径"
    )
    
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """
        自动生成数据库连接 URL
        
        Returns:
            str: AsyncPG 格式的数据库连接字符串
        """
        if self.USE_SQLITE:
            return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"
        
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # ==================== Redis 设置 ====================
    REDIS_HOST: str = Field(
        default="localhost",
        description="Redis 服务器地址"
    )
    
    REDIS_PORT: int = Field(
        default=6379,
        description="Redis 端口"
    )
    
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        description="Redis 密码（可选）"
    )
    
    REDIS_DB: int = Field(
        default=0,
        description="Redis 数据库编号"
    )
    
    @computed_field
    @property
    def REDIS_URL(self) -> str:
        """
        自动生成 Redis 连接 URL
        
        Returns:
            str: Redis 连接字符串
        """
        if self.REDIS_PASSWORD:
            return (
                f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:"
                f"{self.REDIS_PORT}/{self.REDIS_DB}"
            )
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # ==================== API 服务配置 ====================
    API_HOST: str = Field(
        default="0.0.0.0",
        description="API 服务监听地址"
    )
    
    API_PORT: int = Field(
        default=8000,
        description="API 服务端口"
    )
    
    # ==================== CORS 配置 ====================
    CORS_ORIGINS: str = Field(
        default="*",
        description="允许的跨域来源，逗号分隔"
    )
    
    # ==================== 日志配置 ====================
    LOG_LEVEL: str = Field(
        default="INFO",
        description="日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    LOG_FILE: str = Field(
        default="./logs/app.log",
        description="日志文件路径"
    )
    
    # ==================== AI 调度器配置 ====================
    SCHEDULER_INTERVAL_SECONDS: int = Field(
        default=60,
        description="AI 调度器执行间隔（秒）"
    )
    
    SCHEDULER_ENABLED: bool = Field(
        default=True,
        description="是否启用 AI 调度器"
    )
    
    # ==================== 节点监控配置 ====================
    NODE_METRICS_RETENTION_DAYS: int = Field(
        default=30,
        description="节点监控数据保留天数"
    )
    
    NODE_HEARTBEAT_TIMEOUT_SECONDS: int = Field(
        default=300,
        description="节点心跳超时时间（秒）"
    )
    
    # ==================== 用户配置 ====================
    DEFAULT_TRAFFIC_LIMIT_GB: int = Field(
        default=100,
        description="新用户默认流量限制（GB）"
    )
    
    MAX_CONCURRENT_CONNECTIONS: int = Field(
        default=5,
        description="单用户最大并发连接数"
    )
    
    # ==================== SMTP 邮件配置（可选）====================
    SMTP_HOST: Optional[str] = Field(
        default=None,
        description="SMTP 服务器地址"
    )
    
    SMTP_PORT: int = Field(
        default=587,
        description="SMTP 端口"
    )
    
    SMTP_USER: Optional[str] = Field(
        default=None,
        description="SMTP 用户名"
    )
    
    SMTP_PASSWORD: Optional[str] = Field(
        default=None,
        description="SMTP 密码"
    )
    
    SMTP_FROM_EMAIL: Optional[str] = Field(
        default=None,
        description="发件人邮箱"
    )
    
    SMTP_TLS: bool = Field(
        default=True,
        description="是否使用 TLS"
    )
    
    # ==================== Pydantic 配置 ====================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,  # 环境变量大小写敏感
        extra="ignore"  # 忽略未定义的环境变量
    )
    
    # ==================== 验证器 ====================
    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """验证运行环境"""
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT 必须是以下之一: {', '.join(allowed)}")
        return v
    
    @field_validator('SECRET_KEY', 'ADMIN_SECRET', 'NODE_COMMUNICATION_KEY')
    @classmethod
    def validate_secrets(cls, v: str, info) -> str:
        """验证密钥强度"""
        field_name = info.field_name
        if "CHANGE-THIS" in v.upper():
            raise ValueError(
                f"{field_name} 包含默认值，生产环境必须修改！"
            )
        if len(v) < 32:
            raise ValueError(f"{field_name} 长度必须至少 32 个字符")
        return v
    
    @field_validator('POSTGRES_PASSWORD')
    @classmethod
    def validate_postgres_password(cls, v: str, info) -> str:
        """验证数据库密码"""
        values = info.data
        # 如果不使用 SQLite，则必须提供 PostgreSQL 密码
        if not values.get('USE_SQLITE', False) and not v:
            raise ValueError("使用 PostgreSQL 时必须设置 POSTGRES_PASSWORD")
        return v
    
    # ==================== 便捷属性 ====================
    @property
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.ENVIRONMENT == "development"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """获取 CORS 允许来源列表"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def base_url(self) -> str:
        """获取应用基础 URL"""
        if self.DOMAIN:
            protocol = "https" if self.is_production else "http"
            return f"{protocol}://{self.DOMAIN}"
        return f"http://localhost:{self.API_PORT}"


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例
    
    使用 LRU 缓存避免重复读取环境变量
    
    Returns:
        Settings: 全局配置实例
    """
    return Settings()


# 导出全局配置实例
settings = get_settings()
