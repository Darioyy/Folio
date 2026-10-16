-- v3.4.1: 添加博文置顶功能
-- 执行方式 (PowerShell):
--   Get-Content backend/migrations/v3.4.1_pinned_posts.sql -Encoding UTF8 | mysql -u root -p --default-character-set=utf8mb4 folio

ALTER TABLE posts
  ADD COLUMN is_pinned TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否置顶(0否1是)'
  AFTER is_hidden;

CREATE INDEX idx_post_pinned ON posts(is_pinned);
