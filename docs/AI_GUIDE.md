# AI Web Dev 项目维护指南

> 本文档供后续AI维护者使用，包含项目信息、服务器配置、更新流程等核心内容。

**⚠️ 给AI维护者的重要约束**：

### 工作原则
- **禁止创建新文档**：不要自动创建 .md 文档文件
- **代码风格**：使用相对路径，不要硬编码绝对路径
- **回答风格**：简洁直接，不要过度解释
- **问题优先级**：理解需求 > 分析根因 > 设计方案 > 编写代码

### 问题分析方法论
**拒绝"头痛医头"的打补丁思维**，采用系统性分析方法：

#### 1. 问题定位深度
```
表面现象 → 直接原因 → 根本原因 → 设计缺陷
   ↓          ↓          ↓          ↓
 修bug     打补丁     重构模块    架构优化
```

**深入分析步骤**：
1. 追踪调用链：从前端 → API → 业务逻辑 → 数据库
2. 检查数据流：参数传递 → 类型转换 → 边界条件
3. 验证假设：通过日志、断点确认实际行为
4. 识别模式：是否是同类问题的第N次出现？

#### 2. 反模式识别
遇到以下情况应考虑重构，而非打补丁：

| 反模式 | 示例 | 正确做法 |
|--------|------|----------|
| 硬编码类型判断 | `if value === 1` | 使用类型转换函数 |
| 重复的修复 | 相同bug在不同位置出现 | 提取公共逻辑 |
| 魔法数字 | `if user.role > 2` | 使用常量或枚举 |
| 类型假设 | 假设TINYINT返回int | 显式类型标准化 |
| 分散的权限检查 | 每个API重复判断 | 统一装饰器或中间件 |

#### 3. 重构决策树
```
问题出现
    │
    ├─ 是否影响功能？→ 是 → 立即修复
    │                  ↓ 否
    ├─ 是否是代码坏味道？→ 是 → 评估重构成本
    │                        ↓
    │                   成本可接受？→ 是 → 重构
    │                                 ↓ 否
    │                              记录技术债
    │
    └─ 是否有架构问题？→ 是 → 设计重构方案
```

#### 4. 代码质量标准

**自适应性**：
- ✅ 数据类型标准化（如 `normalize_permission_value`）
- ✅ 统一的错误处理机制
- ✅ 可配置的常量（非硬编码）
- ❌ 类型散弹：同一字段在不同位置有不同类型假设

**可维护性**：
- ✅ 单一职责：一个函数只做一件事
- ✅ DRY原则：重复逻辑提取为函数
- ✅ 明确的命名：变量名能表达意图
- ❌ 上帝函数：一个函数做太多事

**健壮性**：
- ✅ 边界检查：空值、类型、范围
- ✅ 幂等性：重复调用不产生副作用
- ✅ 降级处理：核心功能失败时优雅降级
- ❌ 脆弱依赖：假设外部输入永远正确

### 实施原则
1. **先理解，后动手**：读代码 > 理解设计 > 定位问题
2. **最小化改动**：能用配置解决的不写代码，能改局部的不重构全局
3. **保持一致**：新代码遵循现有模式，除非有明确理由改进
4. **留下痕迹**：关键逻辑加注释，设计决策写文档（更新本文档）

---

## 项目概述

Flask + MySQL 全栈博客系统，Docker容器化部署，运行在2核2G阿里云CentOS服务器。

### 核心功能
- **用户系统**：三级权限（root/admin/user）
- **内容管理**：文章、资源、媒体的上传下载
- **后台管理**：完整的权限控制界面

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | Flask 3.x + PyMySQL | bcrypt密码加密 |
| 前端 | 原生 HTML/CSS/JS | 无框架 |
| 数据库 | MySQL 8.0 | DictCursor返回字典 |
| 部署 | Docker + Gunicorn | Nginx反向代理 |

---

## 目录结构

```
ai_web_dev/
├── backend/
│   ├── api/
│   │   ├── auth.py       # 权限验证装饰器
│   │   ├── user.py       # 用户管理API
│   │   ├── media.py      # 媒体API（相对路径）
│   │   ├── resource.py   # 资源API（相对路径）
│   │   ├── post.py       # 文章API
│   │   └── system.py     # 系统API
│   ├── database.py       # 数据库连接（上下文管理器）
│   ├── config.py         # 配置文件
│   └── wsgi.py           # WSGI入口
├── frontend/
│   ├── admin.html        # 后台管理界面
│   ├── index.html        # 前台主页
│   └── js/
│       ├── api.js        # API请求封装
│       └── main.js       # 主逻辑
├── uploads/              # 上传文件（相对路径存储）
│   ├── media/
│   └── resources/
├── docker-compose.yml
├── nginx.conf
└── .env
```

---

## 数据库模型

### users 表
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt
    email VARCHAR(100),
    is_admin TINYINT(1) DEFAULT 0,
    is_root TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### media 表
```sql
CREATE TABLE media (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    file_path VARCHAR(500) NOT NULL,      -- 相对路径：media/images/xxx.jpg
    file_name VARCHAR(255) NOT NULL,
    file_type ENUM('image', 'video'),
    thumbnail_path VARCHAR(500),          -- 相对路径
    uploader_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### resources 表
```sql
CREATE TABLE resources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    file_path VARCHAR(500) NOT NULL,      -- 相对路径：resources/xxx.pdf
    file_name VARCHAR(255) NOT NULL,
    uploader_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 权限系统

### 三级权限

| 级别 | is_root | is_admin | 权限 |
|------|---------|----------|------|
| Root | 1 | - | 所有权限，可修改任何人 |
| Admin | 0 | 1 | 管理内容和普通用户，不能修改root |
| User | 0 | 0 | 只管理自己的内容 |

### 用户管理权限规则

| 操作     | Root | Admin | User |
|--------|------|-------|-----|
| 查看用户列表 | ✓ 所有人 | ✓ 过滤root | ✗ |
| 查看邮箱   | ✓ 所有人 | ✓ 非root用户 | ✗ |
| 设置管理员  | ✓ 任何人 | ✗ 无此按钮 | ✗ |
| 删除管理员  | ✓ 任何人 | ✗ 无此按钮 | ✗ |
| 删除用户   | ✓ 任何人（除自己） | ✓ 仅普通用户 | ✗ |

### 权限验证函数

```python
# backend/api/auth.py

@login_required  # 需要登录
def protected_function():
    pass

# 检查权限
is_root_user(user_id)         # 是否root
is_admin_user(user_id)        # 是否admin或root
can_modify_admin(user_id)     # 是否可修改管理员权限
can_delete_user(user_id)      # 是否可删除用户
```

---

## 文件路径规范

**禁止硬编码绝对路径**，所有路径使用相对路径：

```python
# ✅ 正确：相对路径存储
file_path = "media/images/abc123.jpg"
cursor.execute("INSERT INTO media (file_path) VALUES (%s)", (file_path,))

# ❌ 错误：绝对路径
file_path = "D:\\uploads\\media\\images\\abc123.jpg"
```

### 读取文件时转换

```python
# 存储的是相对路径，读取时转为绝对路径
relative_path = media['file_path']
uploads_dir = os.path.abspath(Config.UPLOAD_FOLDER)
file_path = os.path.join(uploads_dir, relative_path)
```

---

## 服务器配置

### 2核2G资源分配

| 服务 | CPU | 内存 | 说明 |
|------|-----|------|------|
| MySQL | 1核 | 512MB | 数据库 |
| Backend | 1核 | 512MB | Flask + Gunicorn |
| Nginx | 0.5核 | 128MB | 反向代理 |

### Gunicorn配置
```
Workers: 2
Threads: 2
Max Requests: 500
Timeout: 60秒
```

### 数据库配置
```
最大连接数: 100
缓冲池: 128M
连接超时: 5秒
重试次数: 2次
```

---

## 部署架构

**部署工具**：Xshell + Xftp 管理阿里云CentOS

**Docker命令**：使用 `docker compose`（空格），不是 `docker-compose`

### 完整更新
```bash
docker compose down && docker compose build && docker compose up -d
```

### 快速重启（代码修改）
```bash
docker compose restart backend
```

### 查看日志
```bash
docker compose logs -f backend
```

---

## 更新流程

### Python代码修改

**文件**：`backend/api/*.py`

1. Xftp上传到 `/root/ai_web_dev/`
2. `docker compose restart backend`
3. `docker compose logs -f backend` 确认启动

### 前端文件修改

**文件**：`frontend/*.html`, `frontend/js/*.js`

1. Xftp上传到 `/root/ai_web_dev/frontend/`
2. 刷新浏览器（无需重启容器）

### 配置文件修改

**文件**：`docker-compose.yml`, `nginx.conf`, `.env`

```bash
docker compose down
docker compose up -d
```

### 依赖修改

**文件**：`backend/requirements.txt`, `backend/Dockerfile`

```bash
docker compose build backend
docker compose up -d
```

---

## 常用命令

```bash
# 容器管理
docker ps                              # 查看运行容器
docker compose restart backend          # 重启后端
docker compose down                    # 停止所有
docker compose up -d                   # 启动所有

# 日志
docker compose logs -f backend          # 后端日志
docker compose logs --tail=50 backend   # 最近50行

# 进入容器
docker exec -it ai_web_dev_backend bash
docker exec -it ai_web_dev_mysql mysql -u root -p

# 数据库
docker exec ai_web_dev_mysql mysqldump -u root -p ai_web_dev > backup.sql
```

---


## 关键文件说明

| 文件 | 作用 | 注意事项 |
|------|------|----------|
| backend/database.py | 数据库连接 | 使用上下文管理器，TINYINT返回int |
| backend/api/auth.py | 权限验证 | 三级权限：ROOT(2) > ADMIN(1) > USER(0) |
| backend/api/user.py | 用户管理 | root可查看所有，admin过滤root |
| backend/api/media.py | 媒体API | 使用相对路径 |
| frontend/admin.html | 后台界面 | toggleUserAdmin参数是新状态 |

---




**最后更新**: 2026-03-08
**项目路径**: `D:\Program\Code\Python\ai_web_dev`
**服务器路径**: `/root/ai_web_dev`
