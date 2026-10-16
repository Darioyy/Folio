-- v3.5.2: follows 表添加外键约束（ondelete CASCADE）
-- 执行前请确认 follows 表中没有孤立记录（follower_id / following_id 对应的 user 已不存在）
-- 清理孤立记录（可选，若数据干净可跳过）：
--   DELETE FROM follows WHERE follower_id NOT IN (SELECT id FROM users);
--   DELETE FROM follows WHERE following_id NOT IN (SELECT id FROM users);

ALTER TABLE follows
    ADD CONSTRAINT fk_follow_follower
        FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    ADD CONSTRAINT fk_follow_following
        FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE;
