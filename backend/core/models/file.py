"""
统一文件模型 - SQLAlchemy ORM
合并 Media（image/video）和 Resource 为统一 File 表
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Index, BigInteger
from sqlalchemy.orm import relationship
from db.session import db as db_session


class File(db_session.Model):
    """统一文件表模型"""
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='文件ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='上传者ID')
    group_id = Column(Integer, ForeignKey('file_groups.id', ondelete='SET NULL'), nullable=True, comment='所属分组')
    sort_order = Column(Integer, default=0, nullable=False, comment='分组内排序权重')
    title = Column(String(200), nullable=False, comment='文件标题')
    description = Column(Text, nullable=True, comment='文件描述')
    file_path = Column(String(500), nullable=False, comment='文件存储路径（相对）')
    file_name = Column(String(255), nullable=False, comment='原始文件名')
    file_size = Column(BigInteger, nullable=True, comment='文件大小（字节）')
    mime_type = Column(String(100), nullable=True, comment='MIME 类型')
    file_category = Column(
        Enum('image', 'video', 'document', 'resource', name='file_category_enum'),
        nullable=False,
        comment='文件分类'
    )
    visibility = Column(
        Enum('private', 'public', name='file_visibility_enum'),
        nullable=False,
        default='private',
        comment='可见性'
    )
    thumbnail_path = Column(String(500), nullable=True, comment='缩略图路径（图片/视频专用）')
    duration = Column(Integer, nullable=True, comment='视频时长（秒）')
    download_count = Column(Integer, default=0, nullable=False, comment='下载次数（资源专用）')
    view_count = Column(Integer, default=0, nullable=False, comment='浏览次数')
    like_count = Column(Integer, default=0, nullable=False, comment='点赞数')
    collect_count = Column(Integer, default=0, nullable=False, comment='收藏数')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment='更新时间')

    # 关系
    user = relationship('User', backref='files')
    group = relationship('FileGroup', back_populates='files', foreign_keys=[group_id])

    __table_args__ = (
        Index('idx_file_user_id', 'user_id'),
        Index('idx_file_group_id', 'group_id'),
        Index('idx_file_category', 'file_category'),
        Index('idx_file_visibility', 'visibility'),
        Index('idx_file_created_at', 'created_at'),
        {'comment': '统一文件表（合并 media + resources）'}
    )

    def to_dict(self, include_user=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'group_id': self.group_id,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'file_category': self.file_category,
            'visibility': self.visibility,
            'thumbnail_path': self.thumbnail_path,
            'duration': self.duration,
            'download_count': self.download_count,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'collect_count': self.collect_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_user and self.user:
            result['username'] = self.user.username
            result['nickname'] = self.user.nickname
            result['avatar'] = self.user.avatar

        return result

    def __repr__(self):
        return f'<File {self.title}>'
