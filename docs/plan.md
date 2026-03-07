# 项目实施方案

## 项目概述

**项目名称**: AI Web Dev Practice
**项目类型**: 个人博客全栈应用
**技术目标**: 全栈开发、数据库操作、用户权限管理、服务器部署

**最新状态**: ✅ 功能完成，已实现后台管理系统和权限控制

---

## 一、技术选型

| 技术层 | 选型 | 理由 |
|--------|------|------|
| 前端 | HTML/CSS/JavaScript | 掌握前端基础原理，无需构建工具 |
| 后端 | Python + Flask | 轻量级框架，代码简洁，适合学习 |
| 数据库 | MySQL | 关系型数据库，生产环境标准 |
| 认证 | Session + 装饰器 | 用户登录和权限控制 |
| 部署 | Linux + Nginx | 主流服务器环境 |

---

## 二、系统架构

### 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                         前端层                          │
├─────────────────────────────────────────────────────────────┤
│  index.html      - 前台展示（文章、资源、媒体）                   │
│  admin.html      - 后台管理（需登录）                          │
│  └─ 登录/注册                                             │
│  └─ 文章管理（增删改查）                                   │
│  └─ 文件上传（视频/图片/资料）                               │
│  └─ 分类管理                                             │
│  └─ 用户管理（仅admin可见）                               │
└─────────────────────────────────────────────────────────────┘
                              ↓ API调用
┌─────────────────────────────────────────────────────────────┐
│                         后端层                          │
├─────────────────────────────────────────────────────────────┤
│  Flask App (端口5000)                                      │
│  ├── api/                                                 │
│  │   ├── user.py    - 用户认证、注册、权限验证               │
│  │   ├── post.py    - 文章CRUD（带权限控制）                │
│  │   ├── resource.py - 资源CRUD（带权限控制）                │
│  │   ├── media.py   - 媒体CRUD（带权限控制）                │
│  │   └── system.py  - 系统信息、分类管理                   │
│  └── auth.py       - 权限验证装饰器                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                         数据层                          │
├─────────────────────────────────────────────────────────────┤
│  MySQL (ai_web_dev)                                       │
│  ├── users         - 用户表（管理员和普通用户）             │
│  ├── categories    - 分类表（文章/资源/媒体）               │
│  ├── posts         - 文章表（博客内容）                     │
│  ├── resources     - 学习资源表（文件上传下载）             │
│  └── media         - 媒体表（游戏截图/视频）                 │
└─────────────────────────────────────────────────────────────┘
```

### 2. 权限设计

```
用户类型          权限范围
────────────────────────────────────
admin (管理员)    - 所有数据的增删改查
                  - 删除任何用户
                  - 访问用户管理页面
                  - 管理所有分类

普通用户          - 创建自己的文章/资源/媒体
                  - 编辑/删除自己的内容
                  - 无法访问用户管理
                  - 无法删除他人内容
```

---

## 三、数据库设计

### 表结构详解

#### 1. users (用户表)
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```
**设计要点**:
- 密码使用 SHA-256 + 盐 哈希存储
- 用户名唯一索引
- 时间戳记录创建和更新时间

#### 2. categories (分类表)
```sql
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    type ENUM('post', 'resource', 'media') NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
**设计要点**:
- 支持三种内容类型的分类
- 每种类型的分类名称唯一

#### 3. posts (文章表)
```sql
CREATE TABLE posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    summary VARCHAR(500),
    category_id INT,
    author_id INT NOT NULL,
    view_count INT DEFAULT 0,
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
);
```
**设计要点**:
- author_id 外键关联用户（级联删除）
- 支持草稿/发布/归档状态
- 浏览计数功能

#### 4. resources (学习资源表)
```sql
CREATE TABLE resources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    download_count INT DEFAULT 0,
    category_id INT,
    uploader_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE
);
```
**设计要点**:
- 文件路径存储绝对路径
- 保留原始文件名用于显示
- 下载计数功能

#### 5. media (媒体表)
```sql
CREATE TABLE media (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type ENUM('image', 'video') NOT NULL,
    thumbnail_path VARCHAR(500),
    duration INT,
    width INT,
    height INT,
    uploader_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE
);
```
**设计要点**:
- 支持图片和视频两种类型
- 视频支持缩略图（自动生成）
- 记录媒体尺寸信息

---

## 四、API接口设计

### RESTful API 列表

#### 用户认证相关
| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| /api/v1/users/login | POST | 用户登录 | 公开 |
| /api/v1/users/logout | POST | 用户登出 | 登录后 |
| /api/v1/users/register | POST | 用户注册 | 公开 |
| /api/v1/users/me | GET | 获取当前用户 | 登录后 |
| /api/v1/users/check-auth | GET | 检查登录状态 | 公开 |

#### 文章管理
| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| /api/v1/posts | GET | 获取文章列表 | 公开 |
| /api/v1/posts/:id | GET | 获取文章详情 | 公开 |
| /api/v1/posts | POST | 创建文章 | 登录后 |
| /api/v1/posts/:id | PUT | 更新文章 | 登录后 |
| /api/v1/posts/:id | DELETE | 删除文章 | 作者/admin |

#### 资源管理
| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| /api/v1/resources | GET | 获取资源列表 | 公开 |
| /api/v1/resources/:id | GET | 获取资源详情 | 公开 |
| /api/v1/resources/upload | POST | 上传资源 | 登录后 |
| /api/v1/resources/:id/download | GET | 下载资源 | 公开 |
| /api/v1/resources/:id | DELETE | 删除资源 | 上传者/admin |

#### 媒体管理
| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| /api/v1/media | GET | 获取媒体列表 | 公开 |
| /api/v1/media/:id | GET | 获取媒体详情 | 公开 |
| /api/v1/media/:id/view | GET | 查看媒体文件 | 公开 |
| /api/v1/media/upload | POST | 上传媒体 | 登录后 |
| /api/v1/media/:id | DELETE | 删除媒体 | 上传者/admin |

#### 系统管理
| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| /api/v1/system/info | GET | 获取系统统计 | 公开 |
| /api/v1/system/categories | GET | 获取分类列表 | 公开 |
| /api/v1/system/categories | POST | 创建分类 | 登录后 |

---

## 五、实施进度

### 阶段1：基础功能 ✅ 已完成
- [x] 项目架构搭建
- [x] 数据库设计与初始化
- [x] Flask后端框架搭建
- [x] API路由模块化设计
- [x] 前端页面框架
- [x] 环境配置（.env文件）
- [x] 本地服务启动

### 阶段2：核心功能 ✅ 已完成
- [x] 文章增删改查
- [x] 文件上传下载
- [x] 媒体展示与预览
- [x] 分类管理
- [x] 前后端联调

### 阶段3：用户系统 ✅ 已完成
- [x] 用户注册功能
- [x] 用户登录/登出
- [x] Session管理
- [x] 权限验证装饰器
- [x] 后台管理界面

### 阶段4：权限控制 ✅ 已完成
- [x] admin/普通用户权限区分
- [x] 内容所有权验证
- [x] 删除权限控制
- [x] 前台移除删除功能

---

## 六、默认账户

### 管理员账户
```
用户名: admin
密码:   admin123
权限:   所有操作权限
```

---

## 七、访问地址

### 本地开发环境
| 页面 | 地址 |
|------|------|
| 前台首页 | http://localhost:5500/index.html |
| 后台管理 | http://localhost:5500/admin.html |
| 后端API | http://localhost:5000/api/v1 |

---

## 八、文件结构

```
ai_web_dev/
├── backend/              # 后端代码
│   ├── api/              # API路由模块
│   │   ├── __init__.py
│   │   ├── auth.py      # 权限验证
│   │   ├── media.py     # 媒体API
│   │   ├── post.py      # 文章API
│   │   ├── resource.py  # 资源API
│   │   ├── system.py    # 系统API
│   │   └── user.py      # 用户API
│   ├── app.py           # Flask主入口
│   ├── config.py        # 配置管理
│   └── db.py            # 数据库连接（备用）
├── database/            # 数据库脚本
│   └── init.sql         # 初始化SQL
├── frontend/            # 前端代码
│   ├── css/
│   │   └── style.css    # 样式文件
│   ├── js/
│   │   ├── api.js       # API调用
│   │   ├── config.js    # 配置文件
│   │   ├── main.js      # 主逻辑
│   │   └── config.prod.js
│   ├── index.html       # 前台首页
│   └── admin.html       # 后台管理
├── docs/                # 项目文档
├── uploads/             # 上传文件存储
├── .env                 # 环境变量
├── requirements.txt     # Python依赖
├── start.bat           # 启动脚本
└── stop.bat            # 停止脚本
```

---

**文档创建时间**: 2024-02-28
**最后更新**: 2026-03-07
**项目状态**: ✅ 功能完成，权限系统已实现
