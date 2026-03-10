"""
文章模型 - SQLAlchemy ORM
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from db.session import db as db_session


class Post(db_session.Model):
    """文章表模型"""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="文章ID")
    title = Column(String(200), nullable=False, comment="文章标题")
    content = Column(Text, nullable=False, comment="文章内容")
    summary = Column(Text, nullable=True, comment="文章摘要")
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        comment="分类ID",
    )
    author_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="作者ID",
    )
    status = Column(
        Enum("draft", "published", "archived", name="post_status"),
        default="draft",
        nullable=False,
        comment="文章状态",
    )
    view_count = Column(Integer, default=0, nullable=False, comment="浏览次数")
    created_at = Column(
        DateTime, default=datetime.utcnow, nullable=False, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间",
    )

    # 关系
    category = relationship("Category", back_populates="posts")
    author = relationship("User", backref="posts")

    __table_args__ = (
        Index("idx_post_status", "status"),
        Index("idx_post_author", "author_id"),
        Index("idx_post_category", "category_id"),
        Index("idx_post_created", "created_at"),
        {"comment": "文章表"},
    )

    def to_dict(self, include_category=False, include_author=False):
        """转换为字典"""
        result = {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "category_id": self.category_id,
            "author_id": self.author_id,
            "status": self.status,
            "view_count": self.view_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_category and self.category:
            result["category_name"] = self.category.name

        if include_author and self.author:
            result["author_name"] = self.author.username

        return result

    def __repr__(self):
        return f"<Post {self.title}>"
