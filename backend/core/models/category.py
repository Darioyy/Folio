"""
分类模型 - SQLAlchemy ORM
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Index, Text
from db.session import db as db_session
from sqlalchemy.orm import relationship


class Category(db_session.Model):
    """分类表模型"""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name = Column(String(100), unique=True, nullable=False, comment="分类名称")
    description = Column(String(500), nullable=True, comment="专栏描述")
    avatar_path = Column(String(500), nullable=True, comment="专栏头像路径")
    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )

    # 关系
    posts = relationship("Post", back_populates="category", lazy="dynamic")

    __table_args__ = (Index("idx_category_name", "name"), {"comment": "分类表"})

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "avatar_path": self.avatar_path,
            "avatar_url": f"/api/v1/system/categories/{self.id}/avatar/view" if self.avatar_path else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Category {self.name}>"
