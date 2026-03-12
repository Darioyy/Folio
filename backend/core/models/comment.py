"""
评论模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from db.session import db


class Comment(db.Model):
    """评论表"""
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='评论ID')
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False, comment='博文ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='评论者ID')
    parent_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'), nullable=True, default=None, comment='父评论ID')
    content = Column(String(500), nullable=False, comment='评论内容')
    like_count = Column(Integer, default=0, nullable=False, comment='点赞数')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='评论时间')

    # 关系
    user = relationship('User', backref='comments')
    replies = relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='select')
    comment_likes = relationship('CommentLike', back_populates='comment', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_comment_post', 'post_id'),
        Index('idx_comment_user', 'user_id'),
        Index('idx_comment_parent', 'parent_id'),
        {'comment': '评论表'}
    )

    def to_dict(self, include_user=False, include_replies=False, liked=False):
        result = {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'parent_id': self.parent_id,
            'content': self.content,
            'like_count': self.like_count or 0,
            'liked': liked,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_user and self.user:
            result['username'] = self.user.username
            result['nickname'] = self.user.nickname
            result['avatar'] = self.user.avatar
        if include_replies:
            result['replies'] = [r.to_dict(include_user=include_user) for r in (self.replies or [])]
        return result


class CommentLike(db.Model):
    """评论点赞表"""
    __tablename__ = 'comment_likes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    comment_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    comment = relationship('Comment', back_populates='comment_likes')

    __table_args__ = (
        UniqueConstraint('user_id', 'comment_id', name='uk_cl'),
        Index('idx_cl_comment', 'comment_id'),
        {'comment': '评论点赞表'}
    )
