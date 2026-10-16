-- v3.5.1: 用户主页封面存储
-- 在 users 表添加 cover_meta 字段（MEDIUMTEXT，存储 CSS 渐变/SVG/data URL）

ALTER TABLE users
  ADD COLUMN cover_meta MEDIUMTEXT NULL COMMENT '主页封面元数据（CSS backgroundImage 值或预设）'
  AFTER signature;
