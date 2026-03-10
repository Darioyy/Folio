-- 添加个人资料字段到 users 表
-- 执行时间: 2026-03-09

-- 添加头像字段
ALTER TABLE `users`
ADD COLUMN `avatar` VARCHAR(255) NULL DEFAULT NULL COMMENT '头像路径'
AFTER `email`;

-- 添加昵称字段
ALTER TABLE `users`
ADD COLUMN `nickname` VARCHAR(50) NULL DEFAULT NULL COMMENT '昵称'
AFTER `avatar`;

-- 添加个性签名字段
ALTER TABLE `users`
ADD COLUMN `signature` VARCHAR(200) NULL DEFAULT NULL COMMENT '个性签名'
AFTER `nickname`;
