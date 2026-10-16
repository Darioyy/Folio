"""
关注关系模型 - SQLAlchemy ORM
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index, UniqueConstraint
from db.session import db


class Follow(db.Model):
    """关注关系表模型"""
    __tablename__ = 'follows'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='关注ID')
    follower_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True, comment='关注者ID')
    following_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True, comment='被关注者ID')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='关注时间')

    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='unique_follow'),
        Index('idx_follower_id', 'follower_id'),
        Index('idx_following_id', 'following_id'),
        {'comment': '关注关系表'}
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'follower_id': self.follower_id,
            'following_id': self.following_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Follow {self.follower_id} -> {self.following_id}>'
