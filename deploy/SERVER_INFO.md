# 服务器信息

## 连接信息

| 项目 | 值 |
|------|-----|
| IP地址 | 121.40.237.168 |
| 服务商 | 阿里云 |
| SSH用户 | root |
| SSH密码 | Yc1995@@ |
| 系统 | Linux (Ubuntu/Debian) |

## SSH连接

```bash
ssh root@121.40.237.168
```

## MySQL信息

| 项目 | 值 |
|------|-----|
| 运行方式 | Docker容器 |
| 数据库名 | ai_web_dev |
| 用户名 | ai_web_dev_user |
| 密码 | YourPassword123! |

### MySQL常用命令

```bash
# 查看运行的容器
docker ps

# 进入MySQL容器
docker exec -it mysql mysql -u ai_web_dev_user -p

# 导入数据库
docker exec -i mysql mysql -u ai_web_dev_user -pYourPassword123! ai_web_dev < /var/www/ai_web_dev/database/init.sql
```

## 阿里云安全组端口

| 端口 | 协议 | 说明 |
|------|------|------|
| 22 | TCP | SSH |
| 80 | TCP | HTTP |
| 443 | TCP | HTTPS |
| 3306 | TCP | MySQL (建议限制来源IP) |

## Docker 快速部署

### 本地测试（Docker Desktop）

```bash
# 1. 确保安装了 Docker Desktop
# 2. 在项目根目录执行
docker-compose up -d

# 3. 访问
# 前端: http://localhost
# 后端: http://localhost:5000

# 4. 停止
docker-compose down

# 5. 查看日志
docker-compose logs -f
```

### 服务器部署（一键启动）

```bash
# 1. 连接服务器
ssh root@121.40.237.168

# 2. 安装 Docker（如果没有）
curl -fsSL https://get.docker.com | sh
systemctl start docker
systemctl enable docker

# 3. 安装 Docker Compose
apt-get install docker-compose

# 4. 创建项目目录
mkdir -p /var/www/ai_web_dev
cd /var/www/ai_web_dev

# 5. 上传项目文件（在本地执行）
scp -r D:/Program/Code/Python/ai_web_dev/* root@121.40.237.168:/var/www/ai_web_dev/

# 6. 启动服务（在服务器上执行）
cd /var/www/ai_web_dev
docker-compose up -d

# 7. 查看状态
docker-compose ps
docker-compose logs
```

## 项目部署路径

```
/var/www/ai_web_dev/
├── backend/
├── frontend/
├── database/
├── uploads/
├── docker-compose.yml
├── nginx.conf
└── .env
```

## 常用维护命令

```bash
# Docker 相关
docker ps                          # 查看运行容器
docker logs <容器名>               # 查看日志
docker restart <容器名>            # 重启容器
docker exec -it <容器名> bash      # 进入容器

# Docker Compose 相关
docker-compose ps                  # 查看服务状态
docker-compose logs -f             # 查看实时日志
docker-compose restart             # 重启所有服务
docker-compose down                # 停止所有服务
docker-compose up -d --build       # 重新构建并启动

# Nginx 相关（如果不使用 Docker Nginx）
systemctl restart nginx
tail -f /var/log/nginx/error.log
```
