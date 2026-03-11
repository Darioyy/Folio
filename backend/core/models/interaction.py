"""
点赞和收藏模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from db.session import db


class Like(db.Model):
    """点赞表"""
    __tablename__ = 'likes'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='点赞ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'), nullable=False, comment='文件ID')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='点赞时间')

    __table_args__ = (
        UniqueConstraint('user_id', 'file_id', name='unique_like'),
        Index('idx_like_user', 'user_id'),
        Index('idx_like_file', 'file_id'),
        {'comment': '点赞表'}
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'file_id': self.file_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Collection(db.Model):
    """收藏表"""
    __tablename__ = 'collections'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='收藏ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'), nullable=False, comment='文件ID')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='收藏时间')

    __table_args__ = (
        UniqueConstraint('user_id', 'file_id', name='unique_collect'),
        Index('idx_collect_user', 'user_id'),
        Index('idx_collect_file', 'file_id'),
        {'comment': '收藏表'}
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'file_id': self.file_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
