@echo off
REM AI VPN 管理系统 - 一键启动脚本 (Windows)

echo 🚀 启动 AI VPN 管理系统...
echo.

REM 检查虚拟环境
if not exist "venv\" (
    echo 📦 未检测到虚拟环境，正在创建...
    python -m venv venv
    echo ✅ 虚拟环境创建完成
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 📥 安装依赖...
pip install -r requirements.txt

REM 检查环境变量文件
if not exist ".env" (
    echo ⚠️  未检测到 .env 文件，从模板复制...
    copy .env.example .env
    echo ✅ 已创建 .env 文件，请根据需要修改配置
)

echo.
echo ======================================
echo 🎉 项目初始化完成！
echo ======================================
echo.
echo 📝 使用以下命令启动服务：
echo.
echo 1. 启动后端 API：
echo    python backend\main.py
echo    或：
echo    uvicorn backend.main:app --reload
echo.
echo 2. 启动管理后台：
echo    streamlit run frontend\app.py
echo.
echo 3. 访问地址：
echo    - API 文档: http://localhost:8000/api/docs
echo    - 管理后台: http://localhost:8501
echo.
pause
