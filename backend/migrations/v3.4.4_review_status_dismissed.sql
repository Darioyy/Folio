-- v3.4.4: 历史审核记录
-- 扩展 posts.review_status 枚举，加入 'approved'（补全）和 'dismissed'（举报被驳回）
ALTER TABLE posts
  MODIFY COLUMN review_status
    ENUM('none', 'pending', 'approved', 'rejected', 'dismissed')
    NOT NULL DEFAULT 'none'
    COMMENT '申诉/举报审核状态';
