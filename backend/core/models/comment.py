"""
评论模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from db.session import db


class Comment(db.Model):
    """评论表"""
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='评论ID')
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'), nullable=False, comment='文件ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='评论者ID')
    parent_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'), nullable=True, default=None, comment='父评论ID')
    content = Column(String(500), nullable=False, comment='评论内容')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='评论时间')

    # 关系
    user = relationship('User', backref='comments')
    replies = relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='select')

    __table_args__ = (
        Index('idx_comment_file', 'file_id'),
        Index('idx_comment_user', 'user_id'),
        Index('idx_comment_parent', 'parent_id'),
        {'comment': '评论表'}
    )

    def to_dict(self, include_user=False, include_replies=False):
        result = {
            'id': self.id,
            'file_id': self.file_id,
            'user_id': self.user_id,
            'parent_id': self.parent_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_user and self.user:
            result['username'] = self.user.username
            result['nickname'] = self.user.nickname
            result['avatar'] = self.user.avatar
        if include_replies:
            result['replies'] = [r.to_dict(include_user=include_user) for r in (self.replies or [])]
        return result
