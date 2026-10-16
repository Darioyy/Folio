-- v3.4.5: 补全 notifications.type 枚举
-- 缺失 'report'（举报通知）和 'pinned'（置顶通知）导致举报通知静默失败、举报者无法被查询
ALTER TABLE notifications
  MODIFY COLUMN type
    ENUM('like', 'collect', 'comment', 'reply', 'follow', 'new_post',
         'admin', 'appeal', 'review_result', 'report', 'pinned')
    NOT NULL
    COMMENT '通知类型';
