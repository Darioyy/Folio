"""
通知模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, JSON, Index
from sqlalchemy.orm import relationship
from db.session import db


class Notification(db.Model):
    """通知表"""
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='通知ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='接收者用户ID')
    type = Column(
        Enum('like', 'collect', 'comment', 'reply', 'follow', 'new_post', 'admin', 'appeal', 'review_result',
             'report', 'pinned',
             name='notification_type_enum'),
        nullable=False, comment='通知类型'
    )
    actor_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='触发者用户ID')
    target_id = Column(Integer, nullable=True, default=None, comment='关联对象ID')
    extra = Column(JSON, nullable=True, comment='额外数据')
    is_read = Column(Integer, default=0, nullable=False, comment='是否已读')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')

    # 关系
    actor = relationship('User', foreign_keys=[actor_id], backref='sent_notifications')

    __table_args__ = (
        Index('idx_notif_user', 'user_id'),
        Index('idx_notif_user_read', 'user_id', 'is_read'),
        Index('idx_notif_created', 'created_at'),
        {'comment': '通知表'}
    )

    def to_dict(self, include_actor=False):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'actor_id': self.actor_id,
            'target_id': self.target_id,
            'extra': self.extra,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_actor and self.actor:
            result['actor_username'] = self.actor.username
            result['actor_nickname'] = self.actor.nickname
            result['actor_avatar'] = self.actor.avatar
        return result
