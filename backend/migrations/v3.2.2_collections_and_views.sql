-- v3.2.2 迁移：收藏夹系统 + 博文浏览去重
-- 请在生产环境执行此脚本

-- 1. 创建收藏夹表
CREATE TABLE IF NOT EXISTS collection_folders (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  name VARCHAR(100) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_cf_user (user_id),
  CONSTRAINT fk_cf_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 2. collections 表新增 folder_id 字段
ALTER TABLE collections ADD COLUMN IF NOT EXISTS folder_id INT NULL,
  ADD CONSTRAINT fk_collections_folder FOREIGN KEY (folder_id) REFERENCES collection_folders(id) ON DELETE SET NULL;

-- 3. 创建博文浏览去重表
CREATE TABLE IF NOT EXISTS post_views (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  post_id INT NOT NULL,
  viewer_key VARCHAR(128) NOT NULL COMMENT 'user:id 或 anon:key',
  viewed_date DATE NOT NULL,
  UNIQUE KEY uniq_post_view (post_id, viewer_key, viewed_date),
  INDEX idx_pv_post (post_id)
);
