"""
用户模型 - SQLAlchemy ORM
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index, BigInteger, CHAR, Text
from db.session import db


class User(db.Model):
    """用户表模型"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='用户ID')
    uid = Column(CHAR(8), unique=True, nullable=False, default='00000000', comment='公开用户ID（8位数字字符串）')
    username = Column(String(50), unique=True, nullable=False, index=True, comment='用户名')
    password_hash = Column(String(255), nullable=False, comment='密码哈希值')
    email = Column(String(254), nullable=True, unique=True, comment='邮箱')
    avatar = Column(String(255), nullable=True, comment='头像路径')
    nickname = Column(String(50), nullable=True, comment='昵称')
    signature = Column(String(200), nullable=True, comment='个性签名')
    cover_meta = Column(Text(16777215), nullable=True, comment='主页封面元数据（CSS backgroundImage 值）')
    storage_quota = Column(BigInteger, default=209715200, nullable=False, comment='存储配额（字节，默认200MB）')
    is_admin = Column(Integer, default=0, nullable=False, comment='是否管理员(0否1是)')
    is_root = Column(Integer, default=0, nullable=False, comment='是否超级管理员(0否1是)')
    # 关注相关字段
    followers_count = Column(Integer, default=0, nullable=False, comment='粉丝数')
    following_count = Column(Integer, default=0, nullable=False, comment='关注数')
    # 隐私设置
    privacy_avatar = Column(Integer, default=1, nullable=False, comment='头像公开(0私密1公开)')
    privacy_stats = Column(Integer, default=1, nullable=False, comment='统计公开(0私密1公开)')
    privacy_content = Column(Integer, default=1, nullable=False, comment='内容公开(0私密1公开)')
    privacy_follow = Column(Integer, default=1, nullable=False, comment='允许关注(0不允许1允许)')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment='更新时间')

    __table_args__ = (
        Index('idx_username', 'username'),
        Index('idx_uid', 'uid'),
        {'comment': '用户表'}
    )

    def to_dict(self, show_email: bool = False):
        """转换为字典。show_email=True 时才包含 email（仅用于用户自己或管理员）。"""
        d = {
            'id': self.id,
            'uid': self.uid,
            'username': self.username,
            'avatar': self.avatar,
            'nickname': self.nickname,
            'signature': self.signature,
            'cover_meta': self.cover_meta,
            'storage_quota': self.storage_quota,
            'is_admin': self.is_admin,
            'is_root': self.is_root,
            'followers_count': self.followers_count,
            'following_count': self.following_count,
            'privacy_avatar': self.privacy_avatar,
            'privacy_stats': self.privacy_stats,
            'privacy_content': self.privacy_content,
            'privacy_follow': self.privacy_follow,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if show_email:
            d['email'] = self.email
        return d

    def __repr__(self):
        return f'<User {self.username}>'
