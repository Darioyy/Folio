#!/bin/bash

# AI Web Dev 项目部署脚本 v2.0
# 使用方法: ./deploy.sh [命令]
# 命令: init, start, stop, restart, logs, update, test, rebuild

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_COMPOSE="docker compose --env-file .env"

echo "======================================"
echo "AI Web Dev 项目部署脚本 v2.0"
echo "======================================"

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "错误: Docker未安装，请先安装Docker"
        exit 1
    fi

    if ! command -v docker compose &> /dev/null; then
        echo "错误: Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    echo "✓ Docker环境检查通过"
}

# 初始化项目
init_project() {
    echo "开始初始化项目..."

    # 检查.env文件
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        echo "创建.env文件..."
        cat > "$PROJECT_DIR/.env" << EOF
# Flask密钥
SECRET_KEY=ai-web-dev-secret-key-2024-change-in-production

# MySQL数据库配置
MYSQL_ROOT_PASSWORD=\$(openssl rand -base64 16)
MYSQL_DATABASE=ai_web_dev
MYSQL_USER=ai_web_dev_user
MYSQL_PASSWORD=\$(openssl rand -base64 16)

# 后端连接配置
MYSQL_HOST=mysql
MYSQL_PORT=3306
FLASK_ENV=production
EOF
        echo "✓ .env文件已创建"
        echo ""
        echo "生成的密码（请妥善保管）："
        grep PASSWORD .env
    else
        echo "✓ .env文件已存在"
    fi

    # 创建必要的目录
    mkdir -p "$PROJECT_DIR/uploads"
    mkdir -p "$PROJECT_DIR/uploads/videos"
    mkdir -p "$PROJECT_DIR/uploads/images"
    mkdir -p "$PROJECT_DIR/uploads/resources"
    mkdir -p "$PROJECT_DIR/uploads/media/thumbnails"
    echo "✓ 上传目录已创建"

    # 设置目录权限
    chmod -R 755 "$PROJECT_DIR/uploads"
    echo "✓ 目录权限已设置"

    echo ""
    echo "项目初始化完成！"
    echo "运行 './deploy.sh start' 启动服务"
}

# 启动服务
start_services() {
    echo "启动Docker服务..."
    cd "$PROJECT_DIR"
    $DOCKER_COMPOSE up -d
    echo "✓ 服务已启动"

    echo ""
    echo "服务状态:"
    $DOCKER_COMPOSE ps

    echo ""
    echo "等待服务就绪..."
    sleep 5

    echo ""
    echo "访问地址:"
    echo "  前端: http://localhost"
    echo "  后端API: http://localhost/api/v1"
    echo "  健康检查: http://localhost/health"
}

# 停止服务
stop_services() {
    echo "停止Docker服务..."
    cd "$PROJECT_DIR"
    $DOCKER_COMPOSE down
    echo "✓ 服务已停止"
}

# 重启服务
restart_services() {
    echo "重启Docker服务..."
    stop_services
    start_services
}

# 查看日志
view_logs() {
    local service=${1:-}
    cd "$PROJECT_DIR"
    if [ -z "$service" ]; then
        $DOCKER_COMPOSE logs -f --tail=100
    else
        $DOCKER_COMPOSE logs -f --tail=100 "$service"
    fi
}

# 更新项目
update_project() {
    echo "更新项目..."
    cd "$PROJECT_DIR"

    # 拉取最新代码
    git pull

    # 重新构建并启动
    $DOCKER_COMPOSE up -d --build

    echo "✓ 项目已更新"
}

# 重新构建
rebuild_project() {
    echo "重新构建项目..."
    cd "$PROJECT_DIR"

    # 停止容器
    $DOCKER_COMPOSE down

    # 删除旧镜像
    docker rmi ai_web_dev-backend 2>/dev/null || true

    # 重新构建
    $DOCKER_COMPOSE build --no-cache

    # 启动
    $DOCKER_COMPOSE up -d

    echo "✓ 项目已重新构建"
}

# 测试数据库连接
test_database() {
    echo "测试数据库连接..."
    cd "$PROJECT_DIR/backend"

    if [ -f "db_test.py" ]; then
        docker exec ai_web_dev_backend python db_test.py
    else
        echo "错误: db_test.py 不存在"
        return 1
    fi
}

# 备份数据库
backup_database() {
    echo "备份数据库..."
    local backup_dir="$PROJECT_DIR/backups"
    local backup_file="$backup_dir/db_backup_$(date +%Y%m%d_%H%M%S).sql"

    mkdir -p "$backup_dir"

    $DOCKER_COMPOSE exec -T mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} ${MYSQL_DATABASE} > "$backup_file"

    echo "✓ 数据库已备份到: $backup_file"
}

# 显示帮助
show_help() {
    cat << EOF
用法: $0 [命令]

命令:
  init       初始化项目配置
  start      启动所有服务
  stop       停止所有服务
  restart    重启所有服务
  logs       查看所有服务日志 (可指定服务名: logs backend)
  update     更新项目代码并重启
  rebuild    重新构建镜像（代码更新后使用）
  test       测试数据库连接
  backup     备份数据库
  help       显示此帮助信息

示例:
  $0 init          # 初始化项目
  $0 start         # 启动服务
  $0 logs backend  # 查看后端日志
  $0 rebuild       # 重新构建（代码修改后）

常见问题:
  - 数据库连接失败: 运行 $0 rebuild
  - 端口被占用: 修改 docker-compose.yml 中的端口映射
EOF
}

# 主逻辑
check_docker

case "${1:-}" in
    init)
        init_project
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        view_logs "$2"
        ;;
    update)
        update_project
        ;;
    rebuild)
        rebuild_project
        ;;
    test)
        test_database
        ;;
    backup)
        backup_database
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "错误: 未知命令 '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac
