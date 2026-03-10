-- ============================================
-- Private Hub 功能数据库迁移脚本
-- 目的：添加 visibility、file_size、存储配额字段
-- 执行前请备份数据库！
-- ============================================

-- 1. Media 表：添加 visibility 字段
ALTER TABLE media
ADD COLUMN visibility ENUM('private', 'public') DEFAULT 'private' COMMENT '可见性' AFTER file_type;

-- 2. Media 表：添加 file_size 字段
ALTER TABLE media
ADD COLUMN file_size BIGINT DEFAULT NULL COMMENT '文件大小（字节）' AFTER file_name;

-- 3. Media 表：添加 visibility 索引
CREATE INDEX idx_media_visibility ON media(visibility);

-- 4. Resource 表：添加 visibility 字段
ALTER TABLE resources
ADD COLUMN visibility ENUM('private', 'public') DEFAULT 'private' COMMENT '可见性' AFTER file_type;

-- 5. Resource 表：添加 visibility 索引
CREATE INDEX idx_resources_visibility ON resources(visibility);

-- 6. Users 表：添加存储配额字段（默认200MB，管理员500MB通过应用层设置）
ALTER TABLE users
ADD COLUMN storage_used BIGINT DEFAULT 0 COMMENT '已用存储（字节）' AFTER signature,
ADD COLUMN storage_quota BIGINT DEFAULT 209715200 COMMENT '存储配额（字节，默认200MB）' AFTER storage_used;

-- 7. 设置现有 Media 文件的可见性为公共（保持向后兼容）
UPDATE media SET visibility = 'public';

-- 8. 设置现有 Resource 文件的可见性为公共（保持向后兼容）
UPDATE resources SET visibility = 'public';

-- 9. 验证查询
SELECT 'media 表字段:' as info;
SHOW COLUMNS FROM media LIKE 'visibility';
SHOW COLUMNS FROM media LIKE 'file_size';

SELECT 'resources 表字段:' as info;
SHOW COLUMNS FROM resources LIKE 'visibility';

SELECT 'users 表字段:' as info;
SHOW COLUMNS FROM users LIKE 'storage%';
