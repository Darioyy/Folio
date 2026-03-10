-- 添加关注系统和隐私设置字段
ALTER TABLE users ADD COLUMN followers_count INT DEFAULT 0 NOT NULL COMMENT '粉丝数' AFTER is_root;
ALTER TABLE users ADD COLUMN following_count INT DEFAULT 0 NOT NULL COMMENT '关注数' AFTER followers_count;
ALTER TABLE users ADD COLUMN privacy_avatar INT DEFAULT 1 NOT NULL COMMENT '头像公开(0私密1公开)' AFTER following_count;
ALTER TABLE users ADD COLUMN privacy_stats INT DEFAULT 1 NOT NULL COMMENT '统计公开(0私密1公开)' AFTER privacy_avatar;
ALTER TABLE users ADD COLUMN privacy_content INT DEFAULT 1 NOT NULL COMMENT '内容公开(0私密1公开)' AFTER privacy_stats;
ALTER TABLE users ADD COLUMN privacy_follow INT DEFAULT 1 NOT NULL COMMENT '允许关注(0不允许1允许)' AFTER privacy_content;

-- 创建关注关系表
CREATE TABLE IF NOT EXISTS follows (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '关注ID',
    follower_id INT NOT NULL COMMENT '关注者ID',
    following_id INT NOT NULL COMMENT '被关注者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '关注时间',
    UNIQUE KEY unique_follow (follower_id, following_id),
    INDEX idx_follower_id (follower_id),
    INDEX idx_following_id (following_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关注关系表';
