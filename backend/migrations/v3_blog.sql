-- ============================================================
-- v3.0 博客系统迁移脚本
-- 执行方式：mysql -u root -p folio < backend/migrations/v3_blog.sql
-- ⚠️  互动表全量迁移（清空历史 file_id 数据），v3.0 clean start
-- ============================================================

-- 1. posts 表加字段
ALTER TABLE posts
  ADD COLUMN cover_image_id INT NULL COMMENT '封面图文件ID',
  ADD COLUMN like_count INT NOT NULL DEFAULT 0 COMMENT '点赞数',
  ADD COLUMN comment_count INT NOT NULL DEFAULT 0 COMMENT '评论数',
  ADD COLUMN collect_count INT NOT NULL DEFAULT 0 COMMENT '收藏数',
  ADD COLUMN published_at DATETIME NULL COMMENT '发布时间',
  ADD CONSTRAINT fk_post_cover FOREIGN KEY (cover_image_id) REFERENCES files(id) ON DELETE SET NULL;

-- 2. 重建 likes（file_id → post_id）
DROP TABLE IF EXISTS likes;
CREATE TABLE likes (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  post_id    INT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY unique_like (user_id, post_id),
  KEY idx_like_user (user_id),
  KEY idx_like_post (post_id),
  CONSTRAINT fk_like_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_like_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
) COMMENT='点赞表';

-- 3. 重建 collections（file_id → post_id）
DROP TABLE IF EXISTS collections;
CREATE TABLE collections (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  post_id    INT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY unique_collect (user_id, post_id),
  KEY idx_collect_user (user_id),
  KEY idx_collect_post (post_id),
  CONSTRAINT fk_col_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_col_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
) COMMENT='收藏表';

-- 4. 重建 comments（file_id → post_id）
DROP TABLE IF EXISTS comments;
CREATE TABLE comments (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  post_id    INT NOT NULL,
  user_id    INT NOT NULL,
  parent_id  INT NULL,
  content    VARCHAR(500) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY idx_comment_post (post_id),
  KEY idx_comment_user (user_id),
  KEY idx_comment_parent (parent_id),
  CONSTRAINT fk_com_post   FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_com_user   FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_com_parent FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
) COMMENT='评论表';

-- 5. 创建 post_attachments
CREATE TABLE IF NOT EXISTS post_attachments (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  post_id    INT NOT NULL,
  file_id    INT NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  UNIQUE KEY uq_pa (post_id, file_id),
  KEY idx_pa_post (post_id),
  CONSTRAINT fk_pa_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
  CONSTRAINT fk_pa_file FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
) COMMENT='博文附件关联表';

-- 6. notifications ENUM 加 new_post（MySQL 需完整重定义列）
ALTER TABLE notifications
  MODIFY COLUMN type ENUM('like','comment','reply','follow','new_post') NOT NULL COMMENT '通知类型';
