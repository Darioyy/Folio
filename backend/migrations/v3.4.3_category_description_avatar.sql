-- v3.4.3: 专栏新增描述和头像字段
-- 执行方式（PowerShell）：
-- Get-Content backend/migrations/v3.4.3_category_description_avatar.sql -Encoding UTF8 | mysql -u root -p --default-character-set=utf8mb4 folio

ALTER TABLE categories ADD COLUMN IF NOT EXISTS description VARCHAR(500) NULL COMMENT '专栏描述' AFTER name;
ALTER TABLE categories ADD COLUMN IF NOT EXISTS avatar_path VARCHAR(500) NULL COMMENT '专栏头像路径' AFTER description;
