-- 添加 is_root 字段到 users 表
ALTER TABLE users ADD COLUMN is_root TINYINT(1) DEFAULT 0 COMMENT '是否为超级用户(root)';

-- 将现有的 admin 设置为普通管理员(非root)
UPDATE users SET is_root = 0 WHERE username = 'admin';

-- 创建 root 用户（密码: Root123456）
-- 密码哈希是 'Root123456' 的 bcrypt 哈希
INSERT INTO users (username, password_hash, email, is_admin, is_root)
VALUES ('root', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWUIQk.0w2u', 'root@example.com', 1, 1)
ON DUPLICATE KEY UPDATE is_root = 1, is_admin = 1;
