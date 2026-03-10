"""
学习资源模型 - SQLAlchemy ORM
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from db.session import db as db_session


class Resource(db_session.Model):
    """学习资源表模型"""

    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="资源ID")
    title = Column(String(200), nullable=False, comment="资源标题")
    description = Column(Text, nullable=True, comment="资源描述")
    file_path = Column(String(500), nullable=False, comment="文件存储路径（相对）")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_size = Column(Integer, nullable=True, comment="文件大小（字节）")
    file_type = Column(String(100), nullable=True, comment="文件MIME类型")
    visibility = Column(Enum('private', 'public', name='resource_visibility'), nullable=False, default='private', comment='可见性')
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        comment="分类ID",
    )
    uploader_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="上传者ID",
    )
    download_count = Column(Integer, default=0, nullable=False, comment="下载次数")
    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )

    # 关系
    uploader = relationship('User', backref='resources')

    __table_args__ = (
        Index("idx_category", "category_id"),
        Index("idx_uploader", "uploader_id"),
        Index("idx_created_at", "created_at"),
        Index("idx_download_count", "download_count"),
        Index("idx_resources_visibility", "visibility"),
        {"comment": "学习资源表"},
    )

    def to_dict(self, include_category=False, include_uploader=False):
        """转换为字典"""
        result = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "visibility": self.visibility,
            "category_id": self.category_id,
            "uploader_id": self.uploader_id,
            "download_count": self.download_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_category and hasattr(self, "category_name"):
            result["category_name"] = self.category_name

        if include_uploader and self.uploader:
            result["uploader_name"] = self.uploader.username

        return result

    def __repr__(self):
        return f"<Resource {self.title}>"
