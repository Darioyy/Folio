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
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False, comment='博文ID')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='点赞时间')

    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='unique_like'),
        Index('idx_like_user', 'user_id'),
        Index('idx_like_post', 'post_id'),
        {'comment': '点赞表'}
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CollectionFolder(db.Model):
    """收藏夹表"""
    __tablename__ = 'collection_folders'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='收藏夹ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    name = Column(db.String(100), nullable=False, comment='收藏夹名称')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')

    __table_args__ = (
        Index('idx_cf_user', 'user_id'),
        {'comment': '收藏夹表'}
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Collection(db.Model):
    """收藏表"""
    __tablename__ = 'collections'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='收藏ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID')
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False, comment='博文ID')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='收藏时间')
    folder_id = Column(Integer, ForeignKey('collection_folders.id', ondelete='SET NULL'), nullable=True, comment='收藏夹ID')

    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='unique_collect'),
        Index('idx_collect_user', 'user_id'),
        Index('idx_collect_post', 'post_id'),
        Index('idx_collect_folder', 'folder_id'),
        {'comment': '收藏表'}
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'folder_id': self.folder_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
