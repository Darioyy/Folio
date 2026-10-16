-- v3.5.3: 给 posts 表的 title + content 建 FULLTEXT 索引，供搜索使用
-- 注意：posts 表引擎必须是 InnoDB（MySQL 5.6+ 支持 InnoDB FULLTEXT）
-- 执行时间视数据量而定，建议在低峰期执行

ALTER TABLE posts
    ADD FULLTEXT INDEX idx_posts_fulltext (title, content);
