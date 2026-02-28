-- ============================================
-- 数据库初始化脚本
-- 学习要点：数据库设计、表结构、外键约束、索引
-- ============================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS ai_web_dev
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE ai_web_dev;

-- ============================================
-- 1. 用户表 - 存储管理员信息
-- 学习要点：主键、密码哈希、时间戳
-- ============================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希值（不可逆）',
    email VARCHAR(100) COMMENT '邮箱',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ============================================
-- 2. 分类表 - 文章/资料的分类
-- 学习要点：层级结构、枚举约束
-- ============================================
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分类ID',
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '分类名称',
    type ENUM('post', 'resource', 'media') NOT NULL COMMENT '分类类型',
    description TEXT COMMENT '分类描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分类表';

-- ============================================
-- 3. 文章表 - 博客文章
-- 学习要点：富文本、外键、状态管理
-- ============================================
CREATE TABLE posts (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '文章ID',
    title VARCHAR(200) NOT NULL COMMENT '文章标题',
    content TEXT NOT NULL COMMENT '文章内容（支持Markdown）',
    summary VARCHAR(500) COMMENT '文章摘要',
    category_id INT COMMENT '所属分类',
    author_id INT NOT NULL COMMENT '作者ID',
    view_count INT DEFAULT 0 COMMENT '浏览次数',
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft' COMMENT '文章状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_created (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文章表';

-- ============================================
-- 4. 学习资源表 - 上传的文件资料
-- 学习要点：文件存储、文件类型管理
-- ============================================
CREATE TABLE resources (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '资源ID',
    title VARCHAR(200) NOT NULL COMMENT '资源标题',
    description TEXT COMMENT '资源描述',
    file_path VARCHAR(500) NOT NULL COMMENT '文件存储路径',
    file_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_size BIGINT NOT NULL COMMENT '文件大小（字节）',
    file_type VARCHAR(50) NOT NULL COMMENT '文件MIME类型',
    download_count INT DEFAULT 0 COMMENT '下载次数',
    category_id INT COMMENT '所属分类',
    uploader_id INT NOT NULL COMMENT '上传者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习资源表';

-- ============================================
-- 5. 媒体文件表 - 游戏视频/截图
-- 学习要点：多媒体文件、缩略图
-- ============================================
CREATE TABLE media (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '媒体ID',
    title VARCHAR(200) NOT NULL COMMENT '媒体标题',
    description TEXT COMMENT '媒体描述',
    file_path VARCHAR(500) NOT NULL COMMENT '文件存储路径',
    file_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_type ENUM('image', 'video') NOT NULL COMMENT '媒体类型',
    thumbnail_path VARCHAR(500) COMMENT '缩略图路径（视频用）',
    duration INT COMMENT '视频时长（秒）',
    width INT COMMENT '图片/视频宽度',
    height INT COMMENT '图片/视频高度',
    uploader_id INT NOT NULL COMMENT '上传者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_type (file_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='媒体文件表';

-- ============================================
-- 初始化基础数据
-- ============================================

-- 插入默认管理员用户（密码: admin123）
-- 密码哈希: SHA-256(password + salt), salt = "ai_web_dev_salt_2024"
INSERT INTO users (username, password_hash, email) VALUES
('admin', 'd60ee70b3fde10ec3a0d5789d39e6071999ed5e5ed1955c511e5e51fd7cc1861', 'admin@example.com');

-- 插入默认分类
INSERT INTO categories (name, type, description) VALUES
-- 文章分类
('技术学习', 'post', '学习笔记和技术文章'),
('生活随笔', 'post', '日常生活记录'),
-- 资源分类
('编程资料', 'resource', '编程相关的学习资料'),
('设计素材', 'resource', '设计相关的素材文件'),
-- 媒体分类
('游戏截图', 'media', '游戏精彩瞬间截图'),
('游戏视频', 'media', '游戏实况录像');

-- ============================================
-- 创建普通用户（用于学习权限管理）
-- ============================================
-- 后续学习任务：创建只读用户，理解最小权限原则
-- CREATE USER 'web_readonly'@'localhost' IDENTIFIED BY 'readonly_password';
-- GRANT SELECT ON ai_web_dev.* TO 'web_readonly'@'localhost';
-- FLUSH PRIVILEGES;