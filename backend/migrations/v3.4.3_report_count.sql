-- v3.4.3: 为博文添加举报计数字段
-- 执行：Get-Content backend/migrations/v3.4.3_report_count.sql -Encoding UTF8 | mysql -u root -p --default-character-set=utf8mb4 folio

ALTER TABLE posts
  ADD COLUMN report_count INT NOT NULL DEFAULT 0 COMMENT '累计被举报次数' AFTER is_hidden;
