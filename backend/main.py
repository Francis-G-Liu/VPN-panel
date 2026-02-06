"""
AI VPN 管理系统 - FastAPI 后端入口

自动加载配置、初始化数据库、注册路由
支持 Systemd 部署（使用绝对路径）
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from pathlib import Path
import uvicorn
import logging

# ==================== 导入配置 ====================
from backend.config import settings

# ==================== 路径配置（使用绝对路径）====================
# 禁止使用相对路径（"../frontend"），必须使用 pathlib 动态计算
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "frontend" / "static"
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"

# 验证路径存在
if not STATIC_DIR.exists():
    logging.warning(f"静态文件目录不存在: {STATIC_DIR}")
if not TEMPLATES_DIR.exists():
    logging.warning(f"模板目录不存在: {TEMPLATES_DIR}")

# 模板引擎
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ==================== 应用生命周期管理 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    启动时：
    - 初始化数据库连接
    - 启动 AI 调度服务
    
    关闭时：
    - 停止 AI 调度服务
    - 清理资源
    """
    # ========== 启动时执行 ==========
    print("=" * 60)
    print(f"🚀 启动 {settings.PROJECT_NAME}")
    print("=" * 60)
    print(f"📋 环境: {settings.ENVIRONMENT}")
    print(f"🌐 域名: {settings.DOMAIN or '未设置'}")
    print(f"🔌 API: {settings.API_HOST}:{settings.API_PORT}")
    print(f"📁 根目录: {BASE_DIR}")
    print(f"📊 数据库: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    print(f"🔴 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    print("=" * 60)
    
    # 初始化数据库
    print("📦 初始化数据库连接...")
    # TODO: 实现数据库初始化
    # from backend.database import init_db
    # await init_db()
    
    # 启动 AI 调度服务
    if settings.SCHEDULER_ENABLED:
        print("🤖 启动 AI 调度服务...")
        try:
            from backend.services.scheduler import start_scheduler
            start_scheduler()
            print("✅ AI 调度服务已启动")
        except Exception as e:
            print(f"⚠️  AI 调度服务启动失败: {e}")
    else:
        print("⏸️  AI 调度服务已禁用")
    
    print("✅ 系统启动完成")
    print("=" * 60)
    
    yield
    
    # ========== 关闭时执行 ==========
    print("\n" + "=" * 60)
    print(f"🛑 关闭 {settings.PROJECT_NAME}")
    print("=" * 60)
    
    # 停止 AI 调度服务
    if settings.SCHEDULER_ENABLED:
        print("🤖 停止 AI 调度服务...")
        try:
            from backend.services.scheduler import stop_scheduler
            stop_scheduler()
            print("✅ AI 调度服务已停止")
        except Exception as e:
            print(f"⚠️  停止调度服务失败: {e}")
    
    # TODO: 清理其他资源
    print("✅ 系统已安全关闭")
    print("=" * 60)


# ==================== 创建 FastAPI 应用 ====================
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=f"""
🚀 {settings.PROJECT_NAME} - 后端 API

## 功能特性
- 🔐 用户认证与授权
- 🌐 VPN 节点管理
- 📊 流量监控与统计
- 🤖 AI 智能节点调度
- 📡 实时节点心跳监控

## 环境信息
- 运行环境: {settings.ENVIRONMENT}
- API 版本: {settings.API_V1_STR}
""",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# ==================== CORS 中间件 ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


# ==================== 挂载静态文件 ====================
# 使用绝对路径，确保 Systemd 部署时能正确找到文件
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ==================== 注册 API 路由 ====================
from backend.api import client_router

app.include_router(
    client_router,
    prefix=settings.API_V1_STR,
    tags=["client"]
)


# ==================== 基础路由 ====================
@app.get("/")
async def root():
    """根路径 - 系统信息"""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "message": "Welcome to AI VPN Management System API",
        "docs": "/api/docs"
    }


@app.get("/admin")
async def admin_panel(request: Request):
    """管理后台主页"""
    return templates.TemplateResponse(
        "admin_index.html",
        {
            "request": request,
            "project_name": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT
        }
    )


@app.get("/dashboard")
async def user_dashboard(request: Request):
    """用户仪表盘"""
    return templates.TemplateResponse(
        "user_dashboard.html",
        {
            "request": request,
            "project_name": settings.PROJECT_NAME,
            "api_url": settings.base_url
        }
    )


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected",  # TODO: 实际检查数据库连接
        "redis": "connected"  # TODO: 实际检查 Redis 连接
    }


@app.get("/api/system/info")
async def system_info():
    """系统信息（脱敏）"""
    return {
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "api_version": settings.API_V1_STR,
        "scheduler_enabled": settings.SCHEDULER_ENABLED,
        "scheduler_interval": settings.SCHEDULER_INTERVAL_SECONDS,
        "default_traffic_limit_gb": settings.DEFAULT_TRAFFIC_LIMIT_GB,
        "paths": {
            "base_dir": str(BASE_DIR),
            "static_dir": str(STATIC_DIR),
            "templates_dir": str(TEMPLATES_DIR)
        }
    }


# ==================== 错误处理 ====================
@app.exception_handler(404)
async def not_found(request: Request, exc):
    """404 错误处理"""
    return {
        "error": "Not Found",
        "message": f"路径 {request.url.path} 不存在",
        "status_code": 404
    }


@app.exception_handler(500)
async def internal_error(request: Request, exc):
    """500 错误处理"""
    logging.error(f"Internal error: {exc}")
    return {
        "error": "Internal Server Error",
        "message": "服务器内部错误",
        "status_code": 500
    }


# ==================== 开发服务器 ====================
if __name__ == "__main__":
    """
    开发模式启动
    
    生产环境使用 Gunicorn:
    gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker
    """
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower()
    )
