-- v5: 管理员功能增强
-- 1. 博文增加 is_hidden 字段（管理员可隐藏不合规博文）
ALTER TABLE posts ADD COLUMN IF NOT EXISTS is_hidden TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否被管理员隐藏(0否1是)';

-- 2. 扩展通知类型枚举，增加 admin 类型
ALTER TABLE notifications MODIFY COLUMN type ENUM('like','comment','reply','follow','new_post','admin') NOT NULL;
