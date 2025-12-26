#!/bin/bash

###############################################################################
# check_dolphin 一键安装脚本
# 用途: 自动安装和配置 check_dolphin
###############################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否以 root 运行（systemd 服务需要）
check_root() {
    if [ "$INSTALL_AS_SERVICE" = "yes" ] && [ "$EUID" -ne 0 ]; then
        print_error "安装为系统服务需要 root 权限，请使用 sudo 运行此脚本"
        exit 1
    fi
}

# 检查 Python 版本
check_python() {
    print_info "检查 Python 版本..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 未安装，请先安装 Python 3.7 或更高版本"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_info "Python 版本: $PYTHON_VERSION"

    # 检查版本是否 >= 3.7
    if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 7) else 1)'; then
        print_error "需要 Python 3.7 或更高版本，当前版本: $PYTHON_VERSION"
        exit 1
    fi
}

# 创建安装目录
create_install_dir() {
    print_info "创建安装目录: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
}

# 创建虚拟环境
create_venv() {
    print_info "创建 Python 虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate

    print_info "升级 pip..."
    pip install --upgrade pip -q
}

# 安装项目
install_project() {
    print_info "安装项目依赖..."
    pip install -r requirements.txt -q

    print_info "安装 check_dolphin..."
    pip install -e . -q

    print_info "✓ 安装完成"
}

# 创建配置文件
create_config() {
    print_info "创建配置文件..."

    # 复制环境变量示例
    if [ ! -f .env ]; then
        cp .env.example .env
        print_info "已创建 .env 文件，请编辑配置"
    else
        print_warn ".env 文件已存在，跳过创建"
    fi

    # 生成示例配置文件
    source venv/bin/activate
    check-dolphin config -o config.example.yaml
    print_info "已生成 config.example.yaml"
}

# 安装为 systemd 服务
install_systemd_service() {
    print_info "安装 systemd 服务..."

    # 创建服务文件
    cat > /etc/systemd/system/check-dolphin.service <<EOF
[Unit]
Description=DolphinScheduler Workflow Monitor and Retry Service
After=network.target

[Service]
Type=simple
User=${SUDO_USER:-$USER}
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$INSTALL_DIR/venv/bin/check-dolphin monitor --continuous
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# 安全加固
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载 systemd
    systemctl daemon-reload

    print_info "✓ systemd 服务已安装"
    print_info ""
    print_info "使用以下命令管理服务:"
    print_info "  启动服务: sudo systemctl start check-dolphin"
    print_info "  停止服务: sudo systemctl stop check-dolphin"
    print_info "  查看状态: sudo systemctl status check-dolphin"
    print_info "  开机自启: sudo systemctl enable check-dolphin"
    print_info "  查看日志: sudo journalctl -u check-dolphin -f"
}

# 显示使用说明
show_usage() {
    cat <<EOF

${GREEN}================================================================
check_dolphin 安装完成！
================================================================${NC}

安装位置: $INSTALL_DIR

下一步操作:

1. 配置 DolphinScheduler 连接信息
   编辑文件: $INSTALL_DIR/.env

   必填项:
   - DOLPHIN_BASE_URL: DolphinScheduler API 地址
   - DOLPHIN_TOKEN: API 访问令牌
   - PROJECT_CODES: 要监控的项目代码（逗号分隔）

2. 激活虚拟环境
   cd $INSTALL_DIR
   source venv/bin/activate

3. 运行监控
   # 单次运行
   check-dolphin monitor -p <项目代码>

   # 持续监控
   check-dolphin monitor -p <项目代码> --continuous

4. 查看帮助
   check-dolphin --help

EOF

    if [ "$INSTALL_AS_SERVICE" = "yes" ]; then
        cat <<EOF
${GREEN}Systemd 服务已安装${NC}

启动服务:
  sudo systemctl start check-dolphin

查看日志:
  sudo journalctl -u check-dolphin -f

EOF
    fi
}

# 主函数
main() {
    print_info "开始安装 check_dolphin..."
    print_info ""

    # 默认配置
    INSTALL_DIR=${INSTALL_DIR:-/opt/check_dolphin}
    INSTALL_AS_SERVICE=${INSTALL_AS_SERVICE:-no}

    # 交互式询问
    if [ -z "$NON_INTERACTIVE" ]; then
        echo -n "安装目录 [默认: /opt/check_dolphin]: "
        read -r USER_INSTALL_DIR
        INSTALL_DIR=${USER_INSTALL_DIR:-$INSTALL_DIR}

        echo -n "是否安装为 systemd 服务? (yes/no) [默认: no]: "
        read -r USER_INSTALL_SERVICE
        INSTALL_AS_SERVICE=${USER_INSTALL_SERVICE:-no}
    fi

    # 检查权限
    check_root

    # 检查 Python
    check_python

    # 创建安装目录
    create_install_dir

    # 如果当前目录没有项目文件，提示用户
    if [ ! -f "setup.py" ]; then
        print_error "请在 check_dolphin 项目根目录运行此脚本"
        print_error "或者先克隆项目: git clone <repository-url>"
        exit 1
    fi

    # 创建虚拟环境
    create_venv

    # 安装项目
    install_project

    # 创建配置文件
    create_config

    # 安装 systemd 服务（如果需要）
    if [ "$INSTALL_AS_SERVICE" = "yes" ]; then
        install_systemd_service
    fi

    # 显示使用说明
    show_usage

    print_info "${GREEN}安装完成！${NC}"
}

# 运行主函数
main "$@"
