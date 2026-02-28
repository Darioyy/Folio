# 快速部署指南

## 方式一：自动化脚本部署（推荐）

### 1. 在本地准备好项目

```bash
cd D:\Program\Code\Python\ai_web_dev

# 复制部署脚本
xcopy deploy E:\temp\deploy\ /E /I
```

### 2. 连接服务器

```bash
ssh root@121.40.237.168
# 密码: Yc1995@@
```

### 3. 上传项目文件

在本地CMD执行：

```bash
# 进入项目目录
cd D:\Program\Code\Python\ai_web_dev

# 方式A: 使用WinSCP或FileZilla图形界面上传（推荐新手）
# 下载WinSCP: https://winscp.net/
# 连接信息:
#   主机: 121.40.237.168
#   用户: root
#   密码: Yc1995@@
# 上传整个项目到 /var/www/ai_web_dev

# 方式B: 使用scp命令
scp -r backend frontend database .env.production.example root@121.40.237.168:/var/www/ai_web_dev/
```

### 4. 在服务器上执行部署

```bash
ssh root@121.40.237.168

# 安装依赖
apt-get update
apt-get install -y python3 python3-pip nginx

# 创建项目目录
mkdir -p /var/www/ai_web_dev
cd /var/www/ai_web_dev

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install Flask Flask-Cors PyMySQL opencv-python Pillow python-dotenv gunicorn

# 配置环境变量
cp .env.production.example .env
nano .env  # 修改数据库密码

# 初始化数据库（需要MySQL已运行）
# docker exec -i mysql mysql -u root -p < database/init.sql

# 设置权限
chmod -R 755 .
chmod -R 775 uploads

# 测试启动
cd /var/www/ai_web_dev/backend
source ../venv/bin/activate
python app.py  # 测试是否能正常启动
```

---

## 方式二：Git部署（最推荐）

### 1. 推送代码到GitHub/Gitee

```bash
cd D:\Program\Code\Python\ai_web_dev
git init
git add .
git commit -m "Initial commit"
git remote add origin <你的仓库地址>
git push -u origin main
```

### 2. 在服务器上克隆

```bash
ssh root@121.40.237.168

# 安装git
apt-get install -y git

# 克隆项目
cd /var/www
git clone <你的仓库地址> ai_web_dev
cd ai_web_dev

# 后续步骤同方式一的步骤4
```

---

## MySQL Docker容器配置

### 查看MySQL信息

```bash
# 查看运行的容器
docker ps

# 假设MySQL容器名是 mysql，查看详细信息
docker inspect mysql

# 获取MySQL root密码
docker inspect mysql | grep MYSQL_ROOT_PASSWORD

# 进入MySQL
docker exec -it mysql mysql -u root -p
```

### 创建数据库和用户

```sql
CREATE DATABASE ai_web_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ai_web_dev_user'@'%' IDENTIFIED BY 'YourStrongPassword123!';
GRANT ALL PRIVILEGES ON ai_web_dev.* TO 'ai_web_dev_user'@'%';
FLUSH PRIVILEGES;
```

### 导入数据

```bash
# 退出MySQL，在服务器执行
docker exec -i mysql mysql -u ai_web_dev_user -pYourStrongPassword123! ai_web_dev < /var/www/ai_web_dev/database/init.sql
```

---

## 配置Nginx（一次性）

```bash
cat > /etc/nginx/sites-available/ai_web_dev << 'EOF'
server {
    listen 80;
    server_name 121.40.237.168;

    location / {
        root /var/www/ai_web_dev/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /uploads/ {
        alias /var/www/ai_web_dev/uploads/;
    }
}
EOF

ln -s /etc/nginx/sites-available/ai_web_dev /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

---

## 配置Systemd服务（一次性）

```bash
cat > /etc/systemd/system/ai_web_dev.service << 'EOF'
[Unit]
Description=AI Web Dev Flask App
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/ai_web_dev/backend
Environment="PATH=/var/www/ai_web_dev/venv/bin"
ExecStart=/var/www/ai_web_dev/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app('production')"
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai_web_dev
systemctl start ai_web_dev
```

---

## 验证部署

```bash
# 检查服务状态
systemctl status ai_web_dev
systemctl status nginx

# 查看日志
journalctl -u ai_web_dev -n 50

# 开放端口（阿里云安全组）
# 需要在阿里云控制台开放: 80, 443
```

在浏览器访问：**http://121.40.237.168**

---

## 常用维护命令

```bash
# 重启应用
systemctl restart ai_web_dev

# 查看实时日志
journalctl -u ai_web_dev -f

# 更新代码（Git方式）
cd /var/www/ai_web_dev
git pull
systemctl restart ai_web_dev

# 备份数据库
docker exec mysql mysqldump -u ai_web_dev_user -p ai_web_dev > backup.sql
```

---

## 故障排查

### 问题1: 网站无法访问
```bash
# 检查服务状态
systemctl status ai_web_dev
systemctl status nginx

# 检查端口
netstat -tlnp | grep :80
netstat -tlnp | grep :5000

# 检查防火墙
ufw status
# 阿里云安全组需要开放80端口
```

### 问题2: 数据库连接失败
```bash
# 检查MySQL容器
docker ps | grep mysql

# 测试连接
docker exec -it mysql mysql -u ai_web_dev_user -p -h 127.0.0.1

# 检查.env文件配置
cat /var/www/ai_web_dev/.env
```

### 问题3: 上传文件失败
```bash
# 检查目录权限
ls -la /var/www/ai_web_dev/uploads/
chmod 775 /var/www/ai_web_dev/uploads
chown www-data:www-data /var/www/ai_web_dev/uploads
```

---

## 目录结构参考

```
/var/www/ai_web_dev/
├── backend/
│   ├── app.py
│   ├── config.py
│   └── api/
├── frontend/
│   ├── index.html
│   ├── upload.html
│   ├── css/
│   └── js/
├── database/
│   └── init.sql
├── uploads/
│   ├── media/
│   └── resources/
├── venv/
├── .env
└── requirements.txt
```
