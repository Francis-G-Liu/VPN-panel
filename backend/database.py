"""数据库配置与连接管理 - 使用 SQLModel"""
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from backend.config import settings

# 导入所有模型，确保 SQLModel 元数据包含所有表定义
# 必须在 create_db_and_tables() 调用前导入
from backend.models import User, Node, NodeMetrics  # noqa: F401


# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    echo=settings.app_debug,  # 开发环境打印 SQL 语句
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)


def create_db_and_tables():
    """创建数据库表"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """获取数据库会话（依赖注入用）"""
    with Session(engine) as session:
        yield session


# 初始化数据库（可选）
def init_db():
    """初始化数据库 - 创建表结构"""
    print("📦 初始化数据库...")
    create_db_and_tables()
    print("✅ 数据库表创建完成")
