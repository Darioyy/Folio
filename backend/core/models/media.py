"""
媒体文件模型 - SQLAlchemy ORM
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Index, BigInteger
from sqlalchemy.orm import relationship
from db.session import db as db_session


class Media(db_session.Model):
    """媒体文件表模型"""
    __tablename__ = 'media'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='媒体ID')
    title = Column(String(200), nullable=False, comment='媒体标题')
    description = Column(Text, nullable=True, comment='媒体描述')
    file_path = Column(String(500), nullable=False, comment='文件存储路径（相对）')
    file_name = Column(String(255), nullable=False, comment='原始文件名')
    file_type = Column(Enum('image', 'video', name='media_file_type'), nullable=False, comment='媒体类型')
    file_size = Column(BigInteger, nullable=True, comment='文件大小（字节）')
    visibility = Column(Enum('private', 'public', name='media_visibility'), nullable=False, default='private', comment='可见性')
    thumbnail_path = Column(String(500), nullable=True, comment='缩略图路径（相对）')
    duration = Column(Integer, nullable=True, comment='视频时长（秒）')
    width = Column(Integer, nullable=True, comment='图片/视频宽度')
    height = Column(Integer, nullable=True, comment='图片/视频高度')
    uploader_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='上传者ID')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='上传时间')

    # 关系
    uploader = relationship('User', backref='media_files')

    __table_args__ = (
        Index('idx_file_type', 'file_type'),
        Index('idx_uploader', 'uploader_id'),
        Index('idx_created_at', 'created_at'),
        Index('idx_media_visibility', 'visibility'),
        {'comment': '媒体文件表'}
    )

    def to_dict(self, include_uploader=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'type': self.file_type,  # 兼容前端
            'file_size': self.file_size,
            'visibility': self.visibility,
            'thumbnail_path': self.thumbnail_path,
            'duration': self.duration,
            'width': self.width,
            'height': self.height,
            'uploader_id': self.uploader_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

        if include_uploader and self.uploader:
            result['uploader_name'] = self.uploader.username

        return result

    def __repr__(self):
        return f'<Media {self.title}>'
