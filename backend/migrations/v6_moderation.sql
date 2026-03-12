-- v6: 审核申诉系统 + 资源类别重命名 + 通知去重支持
-- 执行顺序：本脚本依赖 v5_admin_features.sql 已执行

-- 1. 将 files 表中 file_category='resource' 的记录迁移为 'document'
UPDATE files SET file_category = 'document' WHERE file_category = 'resource';

-- 2. 修改 files.file_category 枚举：移除 'resource'
ALTER TABLE files
  MODIFY COLUMN file_category ENUM('image','video','document') NOT NULL COMMENT '文件分类';

-- 3. posts 表新增隐藏审核相关字段
ALTER TABLE posts
  ADD COLUMN IF NOT EXISTS hide_reason TEXT NULL COMMENT '管理员隐藏原因' AFTER is_hidden,
  ADD COLUMN IF NOT EXISTS review_status ENUM('none','pending','rejected') NOT NULL DEFAULT 'none' COMMENT '申诉审核状态(none/pending/rejected)' AFTER hide_reason,
  ADD COLUMN IF NOT EXISTS appeal_reason TEXT NULL COMMENT '作者申诉理由' AFTER review_status;

-- 4. 扩展 notifications.type 枚举
--    collect: 收藏通知（原先缺失）
--    appeal: 管理员收到作者申诉
--    review_result: 作者收到申诉结果
ALTER TABLE notifications
  MODIFY COLUMN type ENUM('like','collect','comment','reply','follow','new_post','admin','appeal','review_result') NOT NULL;
