-- ============================================================
-- v3.5.4 审计修复迁移（兼容 MySQL 5.7+，幂等可重复执行）
-- ============================================================

-- 1. Collection.folder_id 索引
SET @exists = (SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'collections' AND INDEX_NAME = 'idx_collect_folder');
SET @sql = IF(@exists = 0,
    'ALTER TABLE collections ADD INDEX idx_collect_folder (folder_id)',
    'SELECT ''[SKIP] idx_collect_folder already exists''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2. PostView.post_id 外键（先清理孤儿记录）
DELETE pv FROM post_views pv
    LEFT JOIN posts p ON pv.post_id = p.id
    WHERE p.id IS NULL;

SET @exists = (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'post_views' AND CONSTRAINT_NAME = 'fk_pv_post');
SET @sql = IF(@exists = 0,
    'ALTER TABLE post_views ADD CONSTRAINT fk_pv_post FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE',
    'SELECT ''[SKIP] fk_pv_post already exists''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 3. User.email 唯一约束
SET @exists = (SELECT COUNT(*) FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND INDEX_NAME = 'uk_email');
SET @sql = IF(@exists = 0,
    'ALTER TABLE users ADD UNIQUE INDEX uk_email (email)',
    'SELECT ''[SKIP] uk_email already exists''');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
