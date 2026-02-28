# 进度记录

## 2026-02-28

### 已完成
- [x] 项目架构搭建
- [x] 数据库表结构设计
- [x] Flask后端框架搭建
- [x] API路由模块化设计
- [x] 前端页面框架
- [x] 环境配置（.env文件创建）
- [x] 数据库初始化（ai_web_dev数据库及表创建）
- [x] 后端服务启动（Flask运行在 http://localhost:5000）
- [x] 前端服务启动（HTTP服务运行在 http://localhost:8080）
- [x] 创建上传页面（upload.html）
- [x] 添加静态文件服务

### 进行中
- [x] 本地环境测试
- [x] 功能测试与Bug修复

### 待完成
- [ ] 创建真实内容数据（文章、资源、媒体）
- [ ] 前端页面样式优化
- [x] 服务器部署准备

---

## 服务器部署信息

### 阿里云服务器
- **IP地址**: 121.40.237.168
- **用户**: root
- **系统**: Linux (Ubuntu/Debian)
- **MySQL**: Docker容器

### 部署文件
- `deploy/server_setup.sh` - 服务器环境配置脚本
- `deploy/deploy_app.sh` - 应用部署脚本
- `deploy/DEPLOYMENT_GUIDE.md` - 详细部署指南
- `deploy/QUICK_START.md` - 快速部署指南
- `.env.production.example` - 生产环境配置模板

### 部署架构
```
阿里云服务器 (121.40.237.168)
├── Nginx (端口80) → 前端静态文件
│   ├── / → 前端页面
│   ├── /api/ → 代理到Flask (127.0.0.1:5000)
│   └── /uploads/ → 上传文件
├── Gunicorn + Flask (端口5000)
│   └── API接口 (/api/v1/*)
└── MySQL (Docker容器)
    └── ai_web_dev数据库
```

### 部署命令快速参考
```bash
# 连接服务器
ssh root@121.40.237.168

# 上传项目（在本地执行）
scp -r backend frontend database root@121.40.237.168:/var/www/ai_web_dev/

# 配置环境
cd /var/www/ai_web_dev
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 配置数据库
docker exec -i mysql mysql -u root -p < database/init.sql

# 启动服务
systemctl start ai_web_dev
systemctl start nginx
```

---

## 问题记录

### 问题1：数据库初始化失败
- **描述**: `ERROR 1364 (HY000): Field 'password_hash' doesn't have a default value`
- **原因**: init.sql插入用户时未提供password_hash，但该字段为NOT NULL
- **解决**: 计算密码哈希值并修改SQL语句
  ```sql
  -- 修改前
  INSERT INTO users (username, email) VALUES ('admin', 'admin@example.com');

  -- 修改后
  INSERT INTO users (username, password_hash, email) VALUES
  ('admin', 'd60ee70b3fde10ec3a0d5789d39e6071999ed5e5ed1955c511e5e51fd7cc1861', 'admin@example.com');
  ```

### 问题2：Windows终端emoji乱码
- **描述**: `UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f680'`
- **原因**: Windows GBK编码不支持emoji字符，Flask启动时打印emoji导致错误
- **解决**: 移除app.py中所有emoji字符，改用文本标识
  ```python
  # 修改前
  print("🚀 启动 Flask 开发服务器")
  print("✓ 应用已启动")

  # 修改后
  print("启动 Flask 开发服务器")
  print("[OK] 应用已启动")
  ```

### 问题3：缺少flask-cors模块
- **描述**: `ModuleNotFoundError: No module named 'flask_cors'`
- **原因**: requirements.txt未包含Flask-CORS依赖
- **解决**:
  1. 在requirements.txt添加：`Flask-Cors==4.0.0`
  2. 安装依赖：`pip install -r requirements.txt`

### 问题4：主页缺少上传入口
- **描述**: 用户无法从主页找到上传文件的功能入口
- **原因**: 初始设计中导航栏未包含上传链接
- **解决**: 在index.html导航栏添加上传链接
  ```html
  <li><a href="upload.html" class="nav-link">上传</a></li>
  ```

### 问题5：上传后文件未正确存储/访问
- **描述**: 上传的文件无法通过前端正常访问
- **原因**:
  1. 文件路径不规范，包含 `backend\..\` 相对路径
  2. 缺少静态文件服务路由
- **解决**:
  1. 修改media.py，使用规范化绝对路径：
     ```python
     upload_dir = os.path.abspath(upload_dir)
     normalized_path = os.path.normpath(file_path)
     ```
  2. 在app.py添加静态文件服务：
     ```python
     @app.route('/uploads/<path:filename>')
     def serve_upload(filename):
         project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
         uploads_dir = os.path.join(project_root, 'uploads')
         return send_from_directory(uploads_dir, filename)
     ```

### 问题6：点击上传链接页面空白
- **描述**: 从首页点击"上传"导航链接后，页面显示空白
- **原因**: main.js的initNavigation()函数拦截了所有.nav-link的点击事件，使用e.preventDefault()阻止了默认导航行为。对于`upload.html`这种非锚点链接，代码尝试查找`getElementById('upload.html')`失败，导致页面无变化
- **解决**: 修改main.js导航逻辑，对非锚点链接放行：
  ```javascript
  // 修改前：所有链接都被拦截
  link.addEventListener('click', (e) => {
      e.preventDefault();
      // ...
  });

  // 修改后：非锚点链接放行
  link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      if (!href.startsWith('#')) {
          return; // 让默认导航发生
      }
      e.preventDefault();
      // ...
  });
  ```

### 问题7-16：其他已解决问题
详见 `docs/troubleshooting_log.md`，包括：
- API路由斜杠问题
- getMedia函数重复定义
- 文件名乱码
- 删除功能缺失
- 上传后错误处理
- 上传界面UI优化
- 数据库连接超时
- MediaAPI未定义
- 游戏媒体点击查看功能

### 问题17：JavaScript中使用Python代码 "os is not defined"
- **描述**: `加载失败: os is not defined`，视频封面无法显示
- **原因**: 在JavaScript代码中使用了Python的 `os.path.basename()` 函数
- **解决**: 使用JavaScript实现相同功能：
  ```javascript
  // 修改前（Python代码）
  os.path.basename(media.thumbnail_path)

  // 修改后（JavaScript代码）
  const getBasename = (path) => path.split(/[\\/]/).pop();
  getBasename(media.thumbnail_path)
  ```

### 问题18：视频缩略图404错误
- **描述**: 视频缩略图无法加载，显示404错误
- **原因**: 使用了错误的URL基础路径
  - Flask的 `/uploads/` 路由位于根路径：`http://localhost:5000/uploads/`
  - 但代码使用 `API_BASE_URL` = `http://localhost:5000/api/v1`
  - 结果URL变成：`http://localhost:5000/api/v1/uploads/...` （错误）
- **解决**: 添加专门的 `UPLOAD_BASE_URL` 常量：
  ```javascript
  // config.js
  const API_BASE_URL = 'http://localhost:5000/api/v1';      // API调用
  const UPLOAD_BASE_URL = 'http://localhost:5000/uploads';  // 文件访问（新增）

  // main.js
  const imageUrl = `${UPLOAD_BASE_URL}/media/thumbnails/${filename}`;
  ```

---

## 技术要点总结

### 文件路径处理
- 使用`os.path.abspath()`获取绝对路径
- 使用`os.path.normpath()`规范化路径
- 避免存储包含`..\`的相对路径到数据库

### 前端路由处理
- 锚点导航（单页应用）vs 外部链接导航
- 使用`href.startsWith('#')`区分两种导航模式

### Flask静态文件服务
- 使用`send_from_directory()`提供文件访问
- 确保目录路径安全（使用绝对路径）

---

## 服务配置

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:8080 | Python HTTP服务器 |
| 后端API | http://localhost:5000 | Flask开发服务器 |
| 上传页面 | http://localhost:8080/upload.html | 文件上传界面 |
| 健康检查 | http://localhost:5000/health | 服务状态检查 |
| API文档 | http://localhost:5000/api | API端点列表 |
