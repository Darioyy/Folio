-- 设置 root 用户的方案
-- 由于 MySQL 的 AUTO_INCREMENT 限制，我们将使用以下方案：
-- 方案1：禁用 AUTO_INCREMENT，插入 ID=0，然后重新启用
-- 方案2（更安全）：使用现有 ID，但在代码中特别处理 root 用户

-- 使用方案2（推荐，更安全）
-- 确保 root 用户存在并具有正确权限

-- 如果 root 用户不存在，创建它
INSERT IGNORE INTO users (username, password_hash, email, is_admin, is_root)
VALUES ('root', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWUIQk.0w2u', 'root@example.com', 1, 1);

-- 确保 root 用户具有最高权限
UPDATE users SET is_admin = 1, is_root = 1 WHERE username = 'root';

-- 注意：在应用代码中，root 用户将被特殊处理，显示为 ID=0
