#!/bin/bash
################################################################################
# AI VPN 管理系统 - 一键部署脚本
#
# 功能：
# - 自动安装所有依赖
# - 配置 Systemd 服务
# - 设置 Nginx 反向代理
# - 申请 SSL 证书
# - 支持更新和卸载
#
# 使用方法：
#   安装: sudo bash install.sh
#   卸载: sudo bash install.sh --uninstall
#
# 作者: AI VPN Team
# 日期: 2026-02-05
################################################################################

set -e  # 遇到错误立即退出

# ==================== 颜色定义 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 配置常量 ====================
# 项目仓库地址（支持一键安装）
# 格式: https://github.com/用户名/仓库名.git
REPO_URL="https://github.com/your-username/ai-vpn.git"

# 安装路径
INSTALL_DIR="/opt/ai-vpn"
VENV_DIR="$INSTALL_DIR/venv"

# 服务配置
SERVICE_USER="aivpn"
BACKEND_SERVICE="ai-vpn-backend"
SCHEDULER_SERVICE="ai-vpn-scheduler"

# ==================== 工具函数 ====================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==================== 系统检查 ====================

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 root 权限运行此脚本"
        echo "使用方法: sudo bash $0"
        exit 1
    fi
}

check_system() {
    log_info "检查系统环境..."
    
    # 检查操作系统
    if [ ! -f /etc/os-release ]; then
        log_error "无法检测操作系统"
        exit 1
    fi
    
    source /etc/os-release
    
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        log_error "仅支持 Ubuntu/Debian 系统"
        log_error "当前系统: $ID"
        exit 1
    fi
    
    log_success "系统检查通过: $PRETTY_NAME"
}

# ==================== 依赖安装 ====================

install_dependencies() {
    log_info "安装系统依赖..."
    
    # 更新软件源
    apt-get update -qq
    
    # 安装必要软件包
    apt-get install -y \
        python3-full \
        python3-pip \
        python3-venv \
        git \
        nginx \
        redis-server \
        certbot \
        python3-certbot-nginx \
        curl \
        ufw \
        > /dev/null 2>&1
    
    log_success "系统依赖安装完成"
}

# ==================== 用户创建 ====================

create_service_user() {
    if id "$SERVICE_USER" &>/dev/null; then
        log_info "服务用户 $SERVICE_USER 已存在"
    else
        log_info "创建服务用户 $SERVICE_USER..."
        useradd -r -s /bin/bash -d $INSTALL_DIR -m $SERVICE_USER
        log_success "服务用户创建完成"
    fi
}

# ==================== 交互式配置 ====================

interactive_config() {
    log_info "开始交互式配置..."
    echo ""
    
    # 域名
    read -p "请输入绑定的域名 (例如 vpn.example.com): " DOMAIN
    if [ -z "$DOMAIN" ]; then
        log_error "域名不能为空"
        exit 1
    fi
    
    # 后端端口
    read -p "请输入后台管理端口 (默认 8000): " BACKEND_PORT
    BACKEND_PORT=${BACKEND_PORT:-8000}
    
    # 生成密钥
    ADMIN_SECRET=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    
    log_success "配置信息已收集"
    echo ""
    log_info "域名: $DOMAIN"
    log_info "后端口: $BACKEND_PORT"
    echo ""
}

# ==================== 项目部署 ====================

deploy_project() {
    log_info "部署项目文件..."
    
    # ========== 场景 A: 更新模式 ==========
    if [ -d "$INSTALL_DIR" ]; then
        log_warning "检测到现有安装，进入更新模式..."
        cd $INSTALL_DIR
        
        # 备份配置
        if [ -f ".env" ]; then
            cp .env .env.backup
            log_info "已备份现有配置"
        fi
        
        # 检查是否为 Git 仓库
        if [ -d ".git" ]; then
            log_info "从 Git 仓库更新代码..."
            sudo -u $SERVICE_USER git pull || {
                log_error "Git pull 失败"
                log_warning "尝试重置本地更改..."
                sudo -u $SERVICE_USER git reset --hard HEAD
                sudo -u $SERVICE_USER git pull || log_error "更新失败，请检查网络连接"
            }
        else
            log_warning "不是 Git 仓库，跳过更新"
        fi
        
        log_success "更新模式完成"
        return 0
    fi
    
    # ========== 场景 B: 本地安装（检测项目文件）==========
    # 检测当前目录是否包含项目文件
    current_dir=$(pwd)
    
    if [ -f "$current_dir/backend/main.py" ] && [ -f "$current_dir/requirements.txt" ]; then
        log_info "检测到本地项目文件，使用本地安装模式..."
        
        # 创建安装目录
        mkdir -p $INSTALL_DIR
        
        # 复制文件到安装目录
        log_info "复制项目文件到 $INSTALL_DIR..."
        cp -r $current_dir/* $INSTALL_DIR/ 2>/dev/null || {
            log_error "复制文件失败"
            exit 1
        }
        
        # 设置所有权
        chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
        
        log_success "本地安装完成"
        return 0
    fi
    
    # ========== 场景 C: 远程安装（Git Clone）==========
    log_info "未检测到本地项目文件，使用远程安装模式..."
    log_info "从仓库克隆代码: $REPO_URL"
    
    # 验证 Git 是否已安装
    if ! command -v git &> /dev/null; then
        log_error "Git 未安装，无法从远程仓库克隆代码"
        log_info "请先安装依赖或手动下载项目源码"
        exit 1
    fi
    
    # 验证仓库 URL 是否已配置
    if [[ "$REPO_URL" == "https://github.com/your-username/ai-vpn.git" ]]; then
        log_error "仓库地址未配置！"
        log_error "请编辑脚本，将 REPO_URL 修改为实际的 GitHub 地址"
        log_error "当前值: $REPO_URL"
        exit 1
    fi
    
    # 克隆仓库
    log_info "正在克隆仓库，这可能需要几分钟..."
    if sudo -u $SERVICE_USER git clone "$REPO_URL" "$INSTALL_DIR"; then
        log_success "远程仓库克隆成功"
    else
        log_error "Git clone 失败！"
        log_error "可能的原因:"
        log_error "  1. 网络连接问题"
        log_error "  2. 仓库地址错误: $REPO_URL"
        log_error "  3. 没有访问权限（私有仓库需要配置 SSH 密钥）"
        log_error ""
        log_error "解决方案:"
        log_error "  1. 检查网络连接"
        log_error "  2. 手动下载源码后再运行此脚本"
        log_error "  3. 使用 wget/curl 下载压缩包:"
        log_error "     wget https://github.com/your-username/ai-vpn/archive/main.zip"
        log_error "     unzip main.zip && cd ai-vpn-main && sudo bash install.sh"
        rm -rf "$INSTALL_DIR"  # 清理失败的克隆
        exit 1
    fi
    
    # 设置所有权
    chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    
    log_success "远程安装完成"
}

# ==================== Python 虚拟环境 ====================

setup_venv() {
    log_info "配置 Python 虚拟环境..."
    
    cd $INSTALL_DIR
    
    # 创建虚拟环境
    if [ ! -d "$VENV_DIR" ]; then
        sudo -u $SERVICE_USER python3 -m venv $VENV_DIR
        log_success "虚拟环境创建完成"
    else
        log_info "虚拟环境已存在"
    fi
    
    # 安装 Python 依赖
    log_info "安装 Python 依赖包..."
    sudo -u $SERVICE_USER $VENV_DIR/bin/pip install --upgrade pip > /dev/null 2>&1
    sudo -u $SERVICE_USER $VENV_DIR/bin/pip install -r requirements.txt > /dev/null 2>&1
    
    # 安装调度器依赖
    if [ -f "requirements_scheduler.txt" ]; then
        sudo -u $SERVICE_USER $VENV_DIR/bin/pip install -r requirements_scheduler.txt > /dev/null 2>&1
    fi
    
    log_success "Python 依赖安装完成"
}

# ==================== 环境配置 ====================

create_env_file() {
    log_info "生成环境配置文件..."
    
    cd $INSTALL_DIR
    
    # 如果有备份，恢复部分配置
    if [ -f ".env.backup" ]; then
        cp .env.backup .env
        log_info "已恢复现有配置"
    else
        # 创建新配置
        cat > .env <<EOF
# ==================== 数据库配置 ====================
DATABASE_URL=sqlite:///./vpn_management.db

# ==================== 应用配置 ====================
API_HOST=0.0.0.0
API_PORT=$BACKEND_PORT
APP_DOMAIN=$DOMAIN

# ==================== 安全配置 ====================
ADMIN_SECRET=$ADMIN_SECRET
JWT_SECRET=$JWT_SECRET

# ==================== Redis 配置 ====================
REDIS_URL=redis://localhost:6379/0

# ==================== 日志配置 ====================
LOG_LEVEL=INFO
EOF
        
        chown $SERVICE_USER:$SERVICE_USER .env
        chmod 600 .env
        log_success "环境配置文件创建完成"
    fi
}

# ==================== 数据库初始化 ====================

init_database() {
    log_info "初始化数据库..."
    
    cd $INSTALL_DIR
    
    # 运行数据库迁移（如果有）
    # sudo -u $SERVICE_USER $VENV_DIR/bin/python -c "from backend.database import init_db; init_db()"
    
    log_success "数据库初始化完成"
}

# ==================== Systemd 服务 ====================

create_systemd_services() {
    log_info "创建 Systemd 服务..."
    
    # 后端服务
    cat > /etc/systemd/system/${BACKEND_SERVICE}.service <<EOF
[Unit]
Description=AI VPN Backend Service
After=network.target redis-server.service

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/uvicorn backend.main:app --host 0.0.0.0 --port $BACKEND_PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # AI 调度服务
    cat > /etc/systemd/system/${SCHEDULER_SERVICE}.service <<EOF
[Unit]
Description=AI VPN Scheduler Service
After=network.target ${BACKEND_SERVICE}.service

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/python -c "from backend.services.scheduler import start_scheduler; import signal, time; start_scheduler(); signal.pause()"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载 systemd
    systemctl daemon-reload
    
    # 启用并启动服务
    systemctl enable ${BACKEND_SERVICE}
    systemctl enable ${SCHEDULER_SERVICE}
    
    systemctl restart ${BACKEND_SERVICE}
    systemctl restart ${SCHEDULER_SERVICE}
    
    log_success "Systemd 服务已创建并启动"
}

# ==================== Nginx 配置 ====================

configure_nginx() {
    log_info "配置 Nginx 反向代理..."
    
    cat > /etc/nginx/sites-available/ai-vpn <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static {
        alias $INSTALL_DIR/frontend/static;
        expires 30d;
    }
}
EOF
    
    # 启用站点
    ln -sf /etc/nginx/sites-available/ai-vpn /etc/nginx/sites-enabled/
    
    # 删除默认站点
    rm -f /etc/nginx/sites-enabled/default
    
    # 测试配置
    nginx -t
    
    # 重启 Nginx
    systemctl restart nginx
    
    log_success "Nginx 配置完成"
}

# ==================== SSL 证书 ====================

setup_ssl() {
    log_info "配置 SSL 证书..."
    
    read -p "是否申请 Let's Encrypt SSL 证书? (y/n, 默认 y): " SETUP_SSL
    SETUP_SSL=${SETUP_SSL:-y}
    
    if [[ "$SETUP_SSL" == "y" || "$SETUP_SSL" == "Y" ]]; then
        # 开放防火墙
        ufw allow 80/tcp > /dev/null 2>&1 || true
        ufw allow 443/tcp > /dev/null 2>&1 || true
        
        log_info "正在申请 SSL 证书，请确保域名已正确解析..."
        
        certbot --nginx -d $DOMAIN --non-interactive --agree-tos --register-unsafely-without-email || {
            log_warning "SSL 证书申请失败，请稍后手动执行: certbot --nginx -d $DOMAIN"
        }
        
        log_success "SSL 配置完成"
    else
        log_info "跳过 SSL 配置"
    fi
}

# ==================== 便捷管理工具 ====================

create_management_tool() {
    log_info "创建管理工具..."
    
    cat > /usr/local/bin/aivpn <<'EOF'
#!/bin/bash

BACKEND_SERVICE="ai-vpn-backend"
SCHEDULER_SERVICE="ai-vpn-scheduler"
INSTALL_DIR="/opt/ai-vpn"

case "$1" in
    start)
        systemctl start $BACKEND_SERVICE $SCHEDULER_SERVICE
        echo "✅ 服务已启动"
        ;;
    stop)
        systemctl stop $BACKEND_SERVICE $SCHEDULER_SERVICE
        echo "✅ 服务已停止"
        ;;
    restart)
        systemctl restart $BACKEND_SERVICE $SCHEDULER_SERVICE
        echo "✅ 服务已重启"
        ;;
    status)
        systemctl status $BACKEND_SERVICE $SCHEDULER_SERVICE
        ;;
    logs)
        journalctl -u $BACKEND_SERVICE -f
        ;;
    update)
        cd $INSTALL_DIR
        sudo -u aivpn git pull
        sudo -u aivpn venv/bin/pip install -r requirements.txt
        systemctl restart $BACKEND_SERVICE $SCHEDULER_SERVICE
        echo "✅ 更新完成"
        ;;
    uninstall)
        bash /opt/ai-vpn/install.sh --uninstall
        ;;
    *)
        echo "AI VPN 管理工具"
        echo ""
        echo "使用方法: aivpn <command>"
        echo ""
        echo "命令列表:"
        echo "  start      - 启动服务"
        echo "  stop       - 停止服务"
        echo "  restart    - 重启服务"
        echo "  status     - 查看状态"
        echo "  logs       - 查看日志"
        echo "  update     - 更新系统"
        echo "  uninstall  - 卸载系统"
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/aivpn
    log_success "管理工具已创建: aivpn"
}

# ==================== 卸载功能 ====================

uninstall() {
    log_warning "开始卸载 AI VPN 系统..."
    
    read -p "确定要卸载吗? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log_info "取消卸载"
        exit 0
    fi
    
    # 停止并删除服务
    log_info "停止服务..."
    systemctl stop ${BACKEND_SERVICE} ${SCHEDULER_SERVICE} || true
    systemctl disable ${BACKEND_SERVICE} ${SCHEDULER_SERVICE} || true
    
    rm -f /etc/systemd/system/${BACKEND_SERVICE}.service
    rm -f /etc/systemd/system/${SCHEDULER_SERVICE}.service
    
    systemctl daemon-reload
    
    # 删除 Nginx 配置
    log_info "删除 Nginx 配置..."
    rm -f /etc/nginx/sites-enabled/ai-vpn
    rm -f /etc/nginx/sites-available/ai-vpn
    systemctl reload nginx || true
    
    # 删除项目目录
    log_info "删除项目文件..."
    rm -rf $INSTALL_DIR
    
    # 删除管理工具
    rm -f /usr/local/bin/aivpn
    
    # 删除服务用户
    read -p "是否删除服务用户 $SERVICE_USER? (y/n): " DELETE_USER
    if [[ "$DELETE_USER" == "y" ]]; then
        userdel -r $SERVICE_USER || true
    fi
    
    log_success "卸载完成"
}

# ==================== 主流程 ====================

main() {
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "       🚀 AI VPN 管理系统 - 一键部署脚本"
    echo "════════════════════════════════════════════════════════"
    echo ""
    
    # 检查卸载模式
    if [[ "$1" == "--uninstall" ]]; then
        uninstall
        exit 0
    fi
    
    # 系统检查
    check_root
    check_system
    
    # 交互式配置
    interactive_config
    
    # 安装依赖
    install_dependencies
    
    # 创建服务用户
    create_service_user
    
    # 部署项目
    deploy_project
    
    # 配置虚拟环境
    setup_venv
    
    # 创建环境配置
    create_env_file
    
    # 初始化数据库
    init_database
    
    # 创建服务
    create_systemd_services
    
    # 配置 Nginx
    configure_nginx
    
    # 配置 SSL
    setup_ssl
    
    # 创建管理工具
    create_management_tool
    
    echo ""
    echo "════════════════════════════════════════════════════════"
    log_success "🎉 AI VPN 系统安装完成！"
    echo "════════════════════════════════════════════════════════"
    echo ""
    echo "📋 重要信息:"
    echo "  - 访问地址: https://$DOMAIN"
    echo "  - 后端端口: $BACKEND_PORT"
    echo "  - 安装目录: $INSTALL_DIR"
    echo ""
    echo "🔧 管理命令:"
    echo "  aivpn start    - 启动服务"
    echo "  aivpn stop     - 停止服务"
    echo "  aivpn restart  - 重启服务"
    echo "  aivpn status   - 查看状态"
    echo "  aivpn logs     - 查看日志"
    echo "  aivpn update   - 更新系统"
    echo ""
    echo "📖 下一步:"
    echo "  1. 访问 https://$DOMAIN/admin 进入管理后台"
    echo "  2. 访问 https://$DOMAIN/dashboard 进入用户面板"
    echo "  3. 查看日志: aivpn logs"
    echo ""
}

# 执行主流程
main "$@"
