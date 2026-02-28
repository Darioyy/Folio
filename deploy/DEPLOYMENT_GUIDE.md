# 服务器部署指南

## 服务器信息
- **IP地址**: 121.40.237.168
- **服务商**: 阿里云
- **系统**: Linux (Ubuntu/Debian)
- **MySQL**: Docker容器运行

---

## 部署步骤

### 第一步：连接服务器

在本地打开终端/CMD：

```bash
ssh root@121.40.237.168
# 输入密码: Yc1995@@
```

---

### 第二步：配置服务器环境

上传并运行环境配置脚本：

```bash
# 方法1：如果有脚本文件
scp deploy/server_setup.sh root@121.40.237.168:/root/
ssh root@121.40.237.168 'bash /root/server_setup.sh'

# 方法2：直接在服务器上执行命令
ssh root@121.40.237.168
```

然后手动执行：

```bash
# 更新系统
apt-get update

# 安装Python和依赖
apt-get install -y python3 python3-pip python3-venv

# 安装Nginx
apt-get install -y nginx

# 安装Python依赖包
pip3 install Flask==3.0.0 \
               Flask-Cors==4.0.0 \
               PyMySQL==1.1.0 \
               opencv-python==4.8.1 \
               Pillow==10.1.0 \
               python-dotenv==1.0.0 \
               gunicorn==21.2.0
```

---

### 第三步：检查MySQL容器

```bash
# 查看运行的容器
docker ps

# 查看MySQL容器信息
docker ps | grep mysql

# 进入MySQL容器（假设容器名为mysql）
docker exec -it mysql mysql -u root -p

# 在MySQL中执行
CREATE DATABASE ai_web_dev;
CREATE USER 'ai_web_dev_user'@'%' IDENTIFIED BY 'YourPassword123!';
GRANT ALL PRIVILEGES ON ai_web_dev.* TO 'ai_web_dev_user'@'%';
FLUSH PRIVILEGES;

# 退出MySQL
exit;
```

**获取MySQL连接信息**：
```bash
# 查看MySQL容器端口映射
docker port mysql

# 查看MySQL root密码（如果在docker-compose中设置）
docker inspect mysql | grep MYSQL_ROOT_PASSWORD
```

---

### 第四步：上传项目文件

在本地电脑执行：

```bash
# 方法1：使用scp上传整个项目
scp -r D:/Program/Code/Python/ai_web_dev root@121.40.237.168:/var/www/

# 方法2：使用rsync（更快）
rsync -avz --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '.git' \
    /d/Program/Code/Python/ai_web_dev/ \
    root@121.40.237.168:/var/www/ai_web_dev/

# 方法3：使用Git（推荐）
ssh root@121.40.237.168
cd /var/www
git clone <你的仓库地址> ai_web_dev
```

---

### 第五步：配置环境变量

```bash
ssh root@121.40.237.168
cd /var/www/ai_web_dev

# 创建.env文件
cat > .env << 'EOF'
SECRET_KEY=ai-web-dev-prod-2026-change-me
MYSQL_HOST=172.17.0.1  # Docker容器内部地址，或使用宿主机IP
MYSQL_PORT=3306
MYSQL_USER=ai_web_dev_user
MYSQL_PASSWORD=YourPassword123!
MYSQL_DATABASE=ai_web_dev
FLASK_ENV=production
EOF
```

**MySQL连接说明**：
- 如果MySQL在Docker中运行，`MYSQL_HOST` 可能需要使用：
  - `172.17.0.1` (Docker默认网桥IP)
  - `host.docker.internal` (Docker Desktop)
  - 宿主机实际IP

---

### 第六步：初始化数据库

```bash
# 从本地上传SQL文件
scp database/init.sql root@121.40.237.168:/var/www/ai_web_dev/database/

# 在服务器上执行
ssh root@121.40.237.168
cd /var/www/ai_web_dev

# 方式1：通过docker exec执行
docker exec -i mysql mysql -u ai_web_dev_user -pYourPassword123! ai_web_dev < database/init.sql

# 方式2：直接进入MySQL容器
docker exec -it mysql mysql -u ai_web_dev_user -p
USE ai_web_dev;
source /var/www/ai_web_dev/database/init.sql;
```

---

### 第七步：创建虚拟环境并安装依赖

```bash
cd /var/www/ai_web_dev
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

---

### 第八步：配置Nginx

```bash
# 创建Nginx配置
cat > /etc/nginx/sites-available/ai_web_dev << 'EOF'
server {
    listen 80;
    server_name 121.40.237.168;

    # 前端
    location / {
        root /var/www/ai_web_dev/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 上传文件
    location /uploads/ {
        alias /var/www/ai_web_dev/uploads/;
    }
}
EOF

# 启用配置
ln -s /etc/nginx/sites-available/ai_web_dev /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重启Nginx
systemctl restart nginx
```

---

### 第九步：创建Systemd服务

```bash
cat > /etc/systemd/system/ai_web_dev.service << 'EOF'
[Unit]
Description=AI Web Dev Flask App
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/ai_web_dev
Environment="PATH=/var/www/ai_web_dev/venv/bin"
ExecStart=/var/www/ai_web_dev/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:create_app()
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable ai_web_dev
systemctl start ai_web_dev
```

---

### 第十步：测试和验证

```bash
# 检查服务状态
systemctl status ai_web_dev
systemctl status nginx

# 查看日志
journalctl -u ai_web_dev -f

# 检查端口
netstat -tlnp | grep :80
netstat -tlnp | grep :5000
```

在浏览器访问：`http://121.40.237.168`

---

## 常见问题

### 1. MySQL连接失败
```bash
# 检查MySQL容器是否运行
docker ps | grep mysql

# 检查MySQL端口
docker port mysql

# 测试连接
docker exec -it mysql mysql -u ai_web_dev_user -p -h 127.0.0.1
```

### 2. 静态文件404
```bash
# 检查文件权限
ls -la /var/www/ai_web_dev/frontend/
chown -R www-data:www-data /var/www/ai_web_dev
chmod -R 755 /var/www/ai_web_dev
```

### 3. 上传文件无法保存
```bash
# 确保uploads目录可写
chmod 775 /var/www/ai_web_dev/uploads
chown www-data:www-data /var/www/ai_web_dev/uploads
```

### 4. 查看应用日志
```bash
# Systemd日志
journalctl -u ai_web_dev -n 100

# 实时日志
journalctl -u ai_web_dev -f

# Nginx错误日志
tail -f /var/log/nginx/error.log
```

---

## 阿里云安全组配置

确保在阿里云控制台开放以下端口：

| 端口 | 协议 | 说明 |
|------|------|------|
| 22 | TCP | SSH |
| 80 | TCP | HTTP |
| 443 | TCP | HTTPS (后续配置SSL) |
| 3306 | TCP | MySQL (建议限制来源IP) |

---

## 目录结构

```
/var/www/ai_web_dev/
├── backend/           # 后端代码
├── frontend/          # 前端代码
├── database/          # 数据库脚本
├── uploads/           # 上传文件目录
├── logs/              # 日志目录
├── venv/              # Python虚拟环境
├── .env               # 环境变量
├── app.py             # Flask入口
└── requirements.txt   # 依赖列表
```

---

## 快速命令参考

```bash
# 重启服务
systemctl restart ai_web_dev

# 重启Nginx
systemctl restart nginx

# 查看服务状态
systemctl status ai_web_dev

# 进入虚拟环境
source /var/www/ai_web_dev/venv/bin/activate

# 退出虚拟环境
deactivate

# 查看Docker容器
docker ps

# 进入MySQL
docker exec -it mysql mysql -u ai_web_dev_user -p
```
