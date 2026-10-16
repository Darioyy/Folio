-- v3.4.0: 文件夹新增描述字段
-- 执行：mysql -u root -p folio < backend/migrations/v3.4.0_groups_description.sql
-- PowerShell：Get-Content backend/migrations/v3.4.0_groups_description.sql -Encoding UTF8 | mysql -u root -p --default-character-set=utf8mb4 folio

ALTER TABLE `file_groups`
  ADD COLUMN `description` TEXT NULL DEFAULT NULL COMMENT '分组描述' AFTER `name`;
