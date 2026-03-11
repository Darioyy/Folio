-- ============================================
-- 数据库初始化脚本（全量 Schema）
-- 版本: v2.0.0
-- 最后更新: 2026-03-11
-- 用途: Docker 首次启动时初始化空数据库
-- ============================================

CREATE DATABASE IF NOT EXISTS ai_web_dev
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE ai_web_dev;

-- ============================================
-- 1. 用户表
-- ============================================
CREATE TABLE users (
    id               INT AUTO_INCREMENT PRIMARY KEY       COMMENT '用户ID',
    uid              CHAR(8)      NOT NULL UNIQUE DEFAULT '00000000' COMMENT '公开用户ID（8位数字字符串）',
    username         VARCHAR(50)  NOT NULL UNIQUE         COMMENT '用户名',
    password_hash    VARCHAR(255) NOT NULL                COMMENT '密码哈希（bcrypt）',
    email            VARCHAR(100) NULL                    COMMENT '邮箱',
    avatar           VARCHAR(255) NULL                    COMMENT '头像路径',
    nickname         VARCHAR(50)  NULL                    COMMENT '昵称',
    signature        VARCHAR(200) NULL                    COMMENT '个性签名',
    storage_quota    BIGINT       NOT NULL DEFAULT 209715200 COMMENT '存储配额（字节，默认200MB）',
    is_admin         TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '是否管理员(0否1是)',
    is_root          TINYINT(1)   NOT NULL DEFAULT 0      COMMENT '是否超级管理员(0否1是)',
    followers_count  INT          NOT NULL DEFAULT 0      COMMENT '粉丝数',
    following_count  INT          NOT NULL DEFAULT 0      COMMENT '关注数',
    privacy_avatar   INT          NOT NULL DEFAULT 1      COMMENT '头像公开(0私密1公开)',
    privacy_stats    INT          NOT NULL DEFAULT 1      COMMENT '统计公开(0私密1公开)',
    privacy_content  INT          NOT NULL DEFAULT 1      COMMENT '内容公开(0私密1公开)',
    privacy_follow   INT          NOT NULL DEFAULT 1      COMMENT '允许关注(0不允许1允许)',
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_uid (uid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 2. 关注关系表
-- ============================================
CREATE TABLE follows (
    id           INT AUTO_INCREMENT PRIMARY KEY  COMMENT '关注ID',
    follower_id  INT NOT NULL                    COMMENT '关注者ID',
    following_id INT NOT NULL                    COMMENT '被关注者ID',
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '关注时间',
    UNIQUE KEY unique_follow (follower_id, following_id),
    INDEX idx_follower_id  (follower_id),
    INDEX idx_following_id (following_id),
    CONSTRAINT fk_follows_follower  FOREIGN KEY (follower_id)  REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_follows_following FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关注关系表';

-- ============================================
-- 3. 文件分组表
-- ============================================
CREATE TABLE file_groups (
    id         INT AUTO_INCREMENT PRIMARY KEY         COMMENT '分组ID',
    user_id    INT NOT NULL                           COMMENT '所属用户ID',
    parent_id  INT NULL DEFAULT NULL                  COMMENT '父分组ID（NULL=根目录）',
    name       VARCHAR(100) NOT NULL                  COMMENT '分组名称',
    sort_order INT NOT NULL DEFAULT 0                 COMMENT '排序权重',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_group_user   FOREIGN KEY (user_id)   REFERENCES users(id)       ON DELETE CASCADE,
    CONSTRAINT fk_group_parent FOREIGN KEY (parent_id) REFERENCES file_groups(id) ON DELETE SET NULL,
    INDEX idx_group_user        (user_id),
    INDEX idx_group_parent      (parent_id),
    INDEX idx_group_user_parent (user_id, parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件分组表';

-- ============================================
-- 5. 分类表（原第 3 节）
-- ============================================
CREATE TABLE categories (
    id          INT AUTO_INCREMENT PRIMARY KEY  COMMENT '分类ID',
    name        VARCHAR(50) NOT NULL UNIQUE     COMMENT '分类名称',
    type        ENUM('post','resource','media') NOT NULL COMMENT '分类类型',
    description TEXT NULL                       COMMENT '分类描述',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分类表';

-- ============================================
-- 4. 文章表
-- ============================================
CREATE TABLE posts (
    id          INT AUTO_INCREMENT PRIMARY KEY     COMMENT '文章ID',
    title       VARCHAR(200) NOT NULL              COMMENT '文章标题',
    content     TEXT         NOT NULL              COMMENT '文章内容（Markdown）',
    summary     VARCHAR(500) NULL                  COMMENT '文章摘要',
    category_id INT          NULL                  COMMENT '所属分类',
    author_id   INT          NOT NULL              COMMENT '作者ID',
    view_count  INT          NOT NULL DEFAULT 0    COMMENT '浏览次数',
    status      ENUM('draft','published','archived') NOT NULL DEFAULT 'draft' COMMENT '文章状态',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_posts_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    CONSTRAINT fk_posts_author   FOREIGN KEY (author_id)   REFERENCES users(id)       ON DELETE CASCADE,
    INDEX idx_posts_status     (status),
    INDEX idx_posts_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章表';

-- ============================================
-- 6. 统一文件表（合并 media + resources）
-- ============================================
CREATE TABLE files (
    id             INT AUTO_INCREMENT PRIMARY KEY         COMMENT '文件ID',
    user_id        INT          NOT NULL                  COMMENT '上传者ID',
    group_id       INT          NULL                      COMMENT '所属分组（NULL=未分组）',
    sort_order     INT          NOT NULL DEFAULT 0        COMMENT '分组内排序权重',
    title          VARCHAR(200) NOT NULL                  COMMENT '文件标题',
    description    TEXT         NULL                      COMMENT '文件描述',
    file_path      VARCHAR(500) NOT NULL                  COMMENT '文件存储路径（相对）',
    file_name      VARCHAR(255) NOT NULL                  COMMENT '原始文件名',
    file_size      BIGINT       NULL                      COMMENT '文件大小（字节）',
    mime_type      VARCHAR(100) NULL                      COMMENT 'MIME 类型',
    file_category  ENUM('image','video','document','resource') NOT NULL COMMENT '文件分类',
    visibility     ENUM('private','public') NOT NULL DEFAULT 'private' COMMENT '可见性',
    thumbnail_path VARCHAR(500) NULL                      COMMENT '缩略图路径（图片/视频专用）',
    duration       INT          NULL                      COMMENT '视频时长（秒）',
    download_count INT          NOT NULL DEFAULT 0        COMMENT '下载次数（资源专用）',
    view_count     INT          NOT NULL DEFAULT 0        COMMENT '浏览次数',
    like_count     INT          NOT NULL DEFAULT 0        COMMENT '点赞数',
    collect_count  INT          NOT NULL DEFAULT 0        COMMENT '收藏数',
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_files_user  FOREIGN KEY (user_id)  REFERENCES users(id)       ON DELETE CASCADE,
    CONSTRAINT fk_files_group FOREIGN KEY (group_id) REFERENCES file_groups(id) ON DELETE SET NULL,
    INDEX idx_file_user_id        (user_id),
    INDEX idx_file_group_id       (group_id),
    INDEX idx_file_category       (file_category),
    INDEX idx_file_visibility     (visibility),
    INDEX idx_file_created_at     (created_at),
    INDEX idx_file_user_group     (user_id, group_id),
    INDEX idx_file_user_vis       (user_id, visibility),
    INDEX idx_file_user_cat       (user_id, file_category),
    INDEX idx_file_cat_vis_date   (file_category, visibility, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一文件表（合并 media + resources）';

-- ============================================
-- 7. 点赞表
-- ============================================
CREATE TABLE likes (
    id         INT AUTO_INCREMENT PRIMARY KEY  COMMENT '点赞ID',
    user_id    INT NOT NULL                    COMMENT '用户ID',
    file_id    INT NOT NULL                    COMMENT '文件ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '点赞时间',
    UNIQUE KEY unique_like (user_id, file_id),
    INDEX idx_like_user (user_id),
    INDEX idx_like_file (file_id),
    CONSTRAINT fk_likes_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_likes_file FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='点赞表';

-- ============================================
-- 8. 收藏表
-- ============================================
CREATE TABLE collections (
    id         INT AUTO_INCREMENT PRIMARY KEY  COMMENT '收藏ID',
    user_id    INT NOT NULL                    COMMENT '用户ID',
    file_id    INT NOT NULL                    COMMENT '文件ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
    UNIQUE KEY unique_collect (user_id, file_id),
    INDEX idx_collect_user (user_id),
    INDEX idx_collect_file (file_id),
    CONSTRAINT fk_collections_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_collections_file FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='收藏表';

-- ============================================
-- 9. 评论表
-- ============================================
CREATE TABLE comments (
    id         INT AUTO_INCREMENT PRIMARY KEY         COMMENT '评论ID',
    file_id    INT NOT NULL                           COMMENT '文件ID',
    user_id    INT NOT NULL                           COMMENT '评论者ID',
    parent_id  INT NULL DEFAULT NULL                  COMMENT '父评论ID（NULL=根评论）',
    content    VARCHAR(500) NOT NULL                  COMMENT '评论内容',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评论时间',
    INDEX idx_comment_file (file_id),
    INDEX idx_comment_user (user_id),
    INDEX idx_comment_parent (parent_id),
    CONSTRAINT fk_comments_file   FOREIGN KEY (file_id)   REFERENCES files(id)    ON DELETE CASCADE,
    CONSTRAINT fk_comments_user   FOREIGN KEY (user_id)   REFERENCES users(id)    ON DELETE CASCADE,
    CONSTRAINT fk_comments_parent FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论表';

-- ============================================
-- 10. 通知表
-- ============================================
CREATE TABLE notifications (
    id         INT AUTO_INCREMENT PRIMARY KEY         COMMENT '通知ID',
    user_id    INT NOT NULL                           COMMENT '接收者用户ID',
    type       ENUM('like','comment','reply','follow') NOT NULL COMMENT '通知类型',
    actor_id   INT NOT NULL                           COMMENT '触发者用户ID',
    target_id  INT NULL DEFAULT NULL                  COMMENT '关联对象ID（file_id或comment_id等）',
    extra      JSON NULL                              COMMENT '额外数据',
    is_read    TINYINT(1) NOT NULL DEFAULT 0          COMMENT '是否已读',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_notif_user (user_id),
    INDEX idx_notif_user_read (user_id, is_read),
    INDEX idx_notif_created (created_at),
    CONSTRAINT fk_notif_user  FOREIGN KEY (user_id)  REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_notif_actor FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通知表';

-- ============================================
-- 初始化基础数据
-- ============================================

-- 默认分类
INSERT INTO categories (name, type, description) VALUES
    ('技术学习', 'post',     '学习笔记和技术文章'),
    ('生活随笔', 'post',     '日常生活记录'),
    ('编程资料', 'resource', '编程相关的学习资料'),
    ('设计素材', 'resource', '设计相关的素材文件'),
    ('游戏截图', 'media',    '游戏精彩瞬间截图'),
    ('游戏视频', 'media',    '游戏实况录像');

-- 注意：管理员账号请通过应用初始化脚本或后台注册创建，不在此处硬编码密码。
