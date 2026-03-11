-- ============================================
-- 统一文件模型迁移脚本
-- Media + Resource → files 表
-- 执行前请备份数据库！
-- ============================================

-- 1. 创建 files 表
CREATE TABLE IF NOT EXISTS files (
    id           INT AUTO_INCREMENT PRIMARY KEY     COMMENT '文件ID',
    user_id      INT NOT NULL                       COMMENT '上传者ID',
    title        VARCHAR(200) NOT NULL              COMMENT '文件标题',
    description  TEXT NULL                          COMMENT '文件描述',
    file_path    VARCHAR(500) NOT NULL              COMMENT '文件存储路径（相对）',
    file_name    VARCHAR(255) NOT NULL              COMMENT '原始文件名',
    file_size    BIGINT NULL                        COMMENT '文件大小（字节）',
    mime_type    VARCHAR(100) NULL                  COMMENT 'MIME 类型',
    file_category ENUM('image','video','document','resource') NOT NULL COMMENT '文件分类',
    visibility   ENUM('private','public') NOT NULL DEFAULT 'private' COMMENT '可见性',
    thumbnail_path VARCHAR(500) NULL               COMMENT '缩略图路径（图片/视频专用）',
    duration     INT NULL                           COMMENT '视频时长（秒）',
    download_count INT NOT NULL DEFAULT 0          COMMENT '下载次数（资源专用）',
    view_count   INT NOT NULL DEFAULT 0            COMMENT '浏览次数',
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP            COMMENT '创建时间',
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_files_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_file_user_id   (user_id),
    INDEX idx_file_category  (file_category),
    INDEX idx_file_visibility (visibility),
    INDEX idx_file_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一文件表（合并 media + resources）';


-- 2. 从 media 表迁移数据
--    file_type IN ('image', 'video') 直接对应 file_category
--    media 无 mime_type 字段，留 NULL
INSERT INTO files (
    user_id, title, description,
    file_path, file_name, file_size, mime_type,
    file_category, visibility,
    thumbnail_path, duration,
    download_count, view_count,
    created_at, updated_at
)
SELECT
    uploader_id,
    title,
    description,
    file_path,
    file_name,
    file_size,
    NULL,           -- mime_type：media 表无此字段
    file_type,      -- 'image' 或 'video' → 直接对应 file_category
    visibility,
    thumbnail_path,
    duration,
    0,              -- download_count
    0,              -- view_count
    created_at,
    created_at      -- updated_at（media 无此字段，用 created_at 代替）
FROM media;


-- 3. 从 resources 表迁移数据
--    统一归入 file_category = 'resource'
--    resources.file_type 是 MIME 字符串（如 'application/pdf'），迁入 mime_type
INSERT INTO files (
    user_id, title, description,
    file_path, file_name, file_size, mime_type,
    file_category, visibility,
    thumbnail_path, duration,
    download_count, view_count,
    created_at, updated_at
)
SELECT
    uploader_id,
    title,
    description,
    file_path,
    file_name,
    file_size,
    file_type,      -- MIME 字符串（如 'application/pdf'）
    'resource',     -- 统一归为 resource 分类
    visibility,
    NULL,           -- thumbnail_path
    NULL,           -- duration
    download_count,
    0,              -- view_count
    created_at,
    created_at      -- updated_at
FROM resources;


-- 4. 备份旧表（重命名，暂不删除）
RENAME TABLE media TO media_backup;
RENAME TABLE resources TO resources_backup;


-- 5. 验证迁移结果
SELECT file_category, COUNT(*) AS count FROM files GROUP BY file_category;
SELECT '总文件数' AS info, COUNT(*) AS total FROM files;
