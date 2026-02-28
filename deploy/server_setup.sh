#!/bin/bash
# ============================================
# 服务器环境配置脚本
# 阿里云服务器部署 - ai_web_dev项目
# ============================================

set -e  # 遇到错误立即退出

echo "========================================"
echo "   AI Web Dev - 服务器环境配置"
echo "========================================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 检查系统信息
echo -e "\n${YELLOW}[1/8] 检查系统信息...${NC}"
uname -a
cat /etc/os-release | grep PRETTY_NAME

# 2. 检查Docker和MySQL容器
echo -e "\n${YELLOW}[2/8] 检查Docker环境...${NC}"
docker --version
echo -e "\n运行的Docker容器："
docker ps

echo -e "\n${GREEN}MySQL容器状态：${NC}"
docker ps | grep mysql || echo -e "${RED}MySQL容器未运行${NC}"

# 3. 安装Python 3和pip
echo -e "\n${YELLOW}[3/8] 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo "安装Python 3..."
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
else
    echo -e "${GREEN}Python已安装: $(python3 --version)${NC}"
fi

if ! command -v pip3 &> /dev/null; then
    echo "安装pip..."
    apt-get install -y python3-pip
else
    echo -e "${GREEN}pip已安装: $(pip3 --version)${NC}"
fi

# 4. 安装Python依赖
echo -e "\n${YELLOW}[4/8] 安装Python依赖包...${NC}"
pip3 install --upgrade pip
pip3 install Flask==3.0.0
pip3 install Flask-Cors==4.0.0
pip3 install Werkzeug==3.0.1
pip3 install PyMySQL==1.1.0
pip3 install cryptography==41.0.7
pip3 install opencv-python==4.8.1
pip3 install Pillow==10.1.0
pip3 install python-dotenv==1.0.0
pip3 install gunicorn==21.2.0  # 生产环境WSGI服务器

echo -e "${GREEN}依赖安装完成${NC}"

# 5. 安装Nginx（反向代理）
echo -e "\n${YELLOW}[5/8] 安装Nginx...${NC}"
if ! command -v nginx &> /dev/null; then
    apt-get install -y nginx
    echo -e "${GREEN}Nginx安装完成${NC}"
else
    echo -e "${GREEN}Nginx已安装${NC}"
fi

# 6. 配置防火墙
echo -e "\n${YELLOW}[6/8] 配置防火墙...${NC}"
echo "请确保阿里云安全组已开放以下端口："
echo "  - 80    (HTTP)"
echo "  - 443   (HTTPS)"
echo "  - 5000  (Flask API，可选，建议通过Nginx代理)"

# 7. 创建项目目录
echo -e "\n${YELLOW}[7/8] 创建项目目录...${NC}"
mkdir -p /var/www/ai_web_dev
mkdir -p /var/www/ai_web_dev/uploads
mkdir -p /var/www/ai_web_dev/logs

echo -e "${GREEN}项目目录创建完成: /var/www/ai_web_dev${NC}"

# 8. 检查MySQL连接
echo -e "\n${YELLOW}[8/8] 检查MySQL容器...${NC}"
echo "请手动检查MySQL容器配置："
echo "  1. 查看MySQL容器: docker ps"
echo "  2. 进入MySQL容器: docker exec -it <容器名> mysql -u root -p"
echo "  3. 创建数据库: CREATE DATABASE ai_web_dev;"
echo "  4. 创建用户并授权（如果需要）"

echo -e "\n${GREEN}========================================"
echo "   环境配置完成！"
echo "========================================${NC}"
echo ""
echo "下一步："
echo "  1. 上传项目文件到服务器"
echo "  2. 配置 .env 文件（数据库连接）"
echo "  3. 运行 deploy_app.sh 部署应用"
echo ""
