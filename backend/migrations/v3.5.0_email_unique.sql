-- v3.5.0: 邮箱唯一性约束
-- 允许 NULL（未填写邮箱的用户不受影响），非空邮箱不可重复
-- MySQL 唯一索引天然允许多个 NULL 值

ALTER TABLE users
    ADD UNIQUE INDEX uk_email (email);
