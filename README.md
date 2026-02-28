# Web Dev & Server Deployment Practice

个人博客练手项目 - 用于学习全栈开发、数据库操作、服务器部署

## 项目功能

1. **个人简介** - 展示个人信息
2. **学习资料** - 文件上传、下载管理
3. **游戏媒体** - 视频/截图展示
4. **文章管理** - 博客文章的增删改查

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML5 + CSS3 + JavaScript |
| 后端 | Python + Flask |
| 数据库 | MySQL |
| 部署 | Linux + Nginx + Gunicorn |

## 项目结构

```
ai_web_dev/
├── backend/          # 后端Flask应用
├── frontend/         # 前端静态页面
├── uploads/          # 用户上传文件存储
├── database/         # 数据库脚本
└── docs/             # 项目文档
```

## 快速开始

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置数据库
```bash
# 创建数据库
mysql -u root -p < database/init.sql
```

### 3. 运行后端
```bash
cd backend
python app.py
```

### 4. 访问前端
直接打开 `frontend/index.html`

## 学习目标

- [ ] 前端页面开发与调试
- [ ] 后端API设计与实现
- [ ] 数据库设计与CRUD操作
- [ ] 文件上传与存储
- [ ] Linux服务器环境搭建
- [ ] 网站部署上线
- [ ] 安全配置（SQL注入防护、XSS防护等）