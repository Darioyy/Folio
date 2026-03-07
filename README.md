# AI Web Dev Practice

一个全栈个人博客应用，支持文章发布、文件上传、媒体展示和用户管理。

## 功能特性

### 前台展示
- 📝 文章列表展示
- 📚 学习资料下载
- 🎮 游戏媒体展示（图片/视频）
- 📊 数据统计概览

### 后台管理
- 🔐 用户登录/注册系统
- 📝 文章管理（创建/编辑/删除）
- 📤 文件上传（视频/图片/资料）
- 🏷️ 分类管理
- 👥 用户管理（仅admin）

### 权限系统
| 角色 | 权限 |
|------|------|
| admin | 管理所有内容、删除用户 |
| 普通用户 | 管理自己的内容 |

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置数据库
编辑 `.env` 文件：
```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ai_web_dev
```

### 3. 初始化数据库
```bash
mysql -u root -p < database/init.sql
```

### 4. 启动项目
双击 `start.bat` 或分别启动：

**后端**:
```bash
cd backend
python app.py
```

**前端**:
```bash
cd frontend
python -m http.server 5500
```

### 5. 访问应用
| 页面 | 地址 |
|------|------|
| 前台首页 | http://localhost:5500/index.html |
| 后台管理 | http://localhost:5500/admin.html |
| 后端API | http://localhost:5000/api/v1 |

## 默认账户

```
用户名: admin
密码:   admin123
```

## 项目结构

```
ai_web_dev/
├── backend/           # 后端Flask应用
│   ├── api/           # API路由模块
│   │   ├── auth.py    # 权限验证
│   │   ├── user.py    # 用户认证
│   │   ├── post.py    # 文章管理
│   │   ├── resource.py # 资源管理
│   │   ├── media.py   # 媒体管理
│   │   └── system.py  # 系统信息
│   ├── app.py         # Flask主入口
│   └── config.py      # 配置管理
├── frontend/          # 前端页面
│   ├── index.html     # 前台首页
│   ├── admin.html     # 后台管理
│   ├── css/           # 样式文件
│   └── js/            # JavaScript
├── database/          # 数据库脚本
│   └── init.sql       # 初始化SQL
├── docs/             # 项目文档
├── uploads/          # 上传文件存储
├── .env              # 环境变量
├── requirements.txt  # Python依赖
├── start.bat        # 启动脚本
└── stop.bat         # 停止脚本
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML + CSS + JavaScript |
| 后端 | Python + Flask |
| 数据库 | MySQL |
| 认证 | Session + 装饰器 |

## 数据库设计

```
ai_web_dev 数据库
├── users          # 用户表（管理员和普通用户）
├── categories     # 分类表（文章/资源/媒体）
├── posts          # 文章表（博客内容）
├── resources      # 学习资源表（文件上传下载）
└── media          # 媒体表（游戏截图/视频）
```

## API接口

### 认证相关
| 端点 | 方法 | 说明 |
|------|------|------|
| /api/v1/users/login | POST | 用户登录 |
| /api/v1/users/logout | POST | 用户登出 |
| /api/v1/users/register | POST | 用户注册 |
| /api/v1/users/me | GET | 获取当前用户 |

### 文章管理
| 端点 | 方法 | 权限 |
|------|------|------|
| /api/v1/posts | GET | 公开 |
| /api/v1/posts | POST | 登录后 |
| /api/v1/posts/:id | PUT | 作者/admin |
| /api/v1/posts/:id | DELETE | 作者/admin |

## 文档

详细文档请查看 `docs/` 目录：
- [plan.md](docs/plan.md) - 项目实施方案
- [progress.md](docs/progress.md) - 进度记录
- [troubleshooting_log.md](docs/troubleshooting_log.md) - 问题解决日志

## 学习目标

- [x] 前端页面开发与调试
- [x] 后端API设计与实现
- [x] 数据库设计与CRUD操作
- [x] 文件上传与存储
- [x] 用户认证与权限管理
- [ ] Linux服务器环境搭建
- [ ] 网站部署上线
- [x] 安全配置（SQL注入防护、XSS防护等）

## 许可证

MIT License
