-- v4_comment_likes.sql: 评论点赞系统
-- 执行前请备份数据库

ALTER TABLE comments ADD COLUMN like_count INT NOT NULL DEFAULT 0 COMMENT '点赞数';

CREATE TABLE IF NOT EXISTS comment_likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    comment_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_cl (user_id, comment_id),
    INDEX idx_cl_comment (comment_id),
    CONSTRAINT fk_cl_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_cl_comment FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE
) COMMENT='评论点赞表';
