#!/bin/bash
# ============================================
# 应用部署脚本
# ============================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="/var/www/ai_web_dev"
BACKUP_DIR="/var/www/ai_web_dev_backup"

echo "========================================"
echo "   AI Web Dev - 应用部署"
echo "========================================"

# 1. 备份现有文件
if [ -d "$PROJECT_DIR/backend" ]; then
    echo -e "${YELLOW}备份现有文件...${NC}"
    rm -rf $BACKUP_DIR
    cp -r $PROJECT_DIR $BACKUP_DIR
fi

# 2. 停止现有服务
echo -e "\n${YELLOW}停止现有服务...${NC}"
pkill -f gunicorn || true
systemctl stop ai_web_dev || true

# 3. 初始化数据库
echo -e "\n${YELLOW}初始化数据库...${NC}"
cd $PROJECT_DIR
if [ -f "database/init.sql" ]; then
    echo "请手动执行数据库初始化："
    echo "  docker exec -i <mysql容器名> mysql -u root -p < database/init.sql"
fi

# 4. 创建.env文件（如果不存在）
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "\n${YELLOW}创建.env文件...${NC}"
    cat > $PROJECT_DIR/.env << 'EOF'
# 生产环境配置
SECRET_KEY=your-secret-key-change-in-production
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=ai_web_dev_user
MYSQL_PASSWORD=your-db-password
MYSQL_DATABASE=ai_web_dev
FLASK_ENV=production
EOF
    echo -e "${RED}请编辑 .env 文件，设置正确的数据库密码！${NC}"
fi

# 5. 设置目录权限
echo -e "\n${YELLOW}设置文件权限...${NC}"
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR
chmod -R 775 $PROJECT_DIR/uploads

# 6. 创建systemd服务文件
echo -e "\n${YELLOW}创建系统服务...${NC}"
cat > /etc/systemd/system/ai_web_dev.service << 'EOF'
[Unit]
Description=AI Web Dev Flask Application
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/ai_web_dev
Environment="PATH=/var/www/ai_web_dev/venv/bin"
ExecStart=/var/www/ai_web_dev/venv/bin/gunicorn --chdir /var/www/ai_web_dev/backend -w 4 -b 127.0.0.1:5000 "app:create_app('production')"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 7. 配置Nginx
echo -e "\n${YELLOW}配置Nginx...${NC}"
cat > /etc/nginx/sites-available/ai_web_dev << 'EOF'
server {
    listen 80;
    server_name _;

    # 前端静态文件
    location / {
        root /var/www/ai_web_dev/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API代理到Flask
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 上传文件访问
    location /uploads/ {
        alias /var/www/ai_web_dev/uploads/;
    }

    # Flask健康检查
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
    }
}
EOF

ln -sf /etc/nginx/sites-available/ai_web_dev /etc/nginx/sites-enabled/
nginx -t

# 8. 启动服务
echo -e "\n${YELLOW}启动服务...${NC}"
systemctl daemon-reload
systemctl enable ai_web_dev
systemctl start ai_web_dev
systemctl restart nginx

echo -e "\n${GREEN}========================================"
echo "   部署完成！"
echo "========================================${NC}"
echo ""
echo "服务状态检查："
echo "  应用状态: systemctl status ai_web_dev"
echo "  Nginx状态: systemctl status nginx"
echo ""
echo "日志查看："
echo "  应用日志: journalctl -u ai_web_dev -f"
echo "  Nginx日志: tail -f /var/log/nginx/error.log"
echo ""
echo "访问地址: http://121.40.237.168"
