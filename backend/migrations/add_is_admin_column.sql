-- 添加 is_admin 字段到 users 表
ALTER TABLE users ADD COLUMN is_admin TINYINT(1) DEFAULT 0 COMMENT '是否为管理员';

-- 将现有的 admin 和 Dario 设置为管理员
UPDATE users SET is_admin = 1 WHERE username IN ('admin', 'Dario');
