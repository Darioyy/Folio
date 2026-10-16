"""
博文浏览记录模型（用于去重）
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Date, UniqueConstraint, Index, ForeignKey
from db.session import db


class PostView(db.Model):
    """博文浏览记录（每用户每天仅计一次）"""
    __tablename__ = 'post_views'

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False, comment='博文ID')
    viewer_key = Column(String(128), nullable=False, comment='user:id 或 session:key')
    viewed_date = Column(Date, default=date.today, nullable=False, comment='浏览日期')

    __table_args__ = (
        UniqueConstraint('post_id', 'viewer_key', 'viewed_date', name='uniq_post_view'),
        Index('idx_pv_post', 'post_id'),
        {'comment': '博文浏览去重记录'}
    )
