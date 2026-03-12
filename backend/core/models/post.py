"""
文章模型 - SQLAlchemy ORM
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Index, SmallInteger
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
    cover_image_id = Column(
        Integer,
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
        comment="封面图文件ID",
    )
    status = Column(
        Enum("draft", "published", "archived", name="post_status"),
        default="draft",
        nullable=False,
        comment="文章状态",
    )
    view_count = Column(Integer, default=0, nullable=False, comment="浏览次数")
    like_count = Column(Integer, default=0, nullable=False, comment="点赞数")
    comment_count = Column(Integer, default=0, nullable=False, comment="评论数")
    collect_count = Column(Integer, default=0, nullable=False, comment="收藏数")
    is_hidden = Column(Integer, default=0, nullable=False, comment="是否被管理员隐藏(0否1是)")
    hide_reason = Column(Text, nullable=True, comment="管理员隐藏原因")
    review_status = Column(
        Enum('none', 'pending', 'rejected', name='post_review_status'),
        default='none', nullable=False, comment="申诉审核状态"
    )
    appeal_reason = Column(Text, nullable=True, comment="作者申诉理由")
    published_at = Column(DateTime, nullable=True, comment="发布时间")
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
    cover_image = relationship("File", foreign_keys=[cover_image_id])
    attachments = relationship(
        "PostAttachment",
        back_populates="post",
        order_by="PostAttachment.sort_order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_post_status", "status"),
        Index("idx_post_author", "author_id"),
        Index("idx_post_category", "category_id"),
        Index("idx_post_created", "created_at"),
        {"comment": "文章表"},
    )

    def to_dict(self, include_category=False, include_author=False, include_attachments=False):
        """转换为字典"""
        result = {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "category_id": self.category_id,
            "author_id": self.author_id,
            "cover_image_id": self.cover_image_id,
            "status": self.status,
            "is_hidden": self.is_hidden or 0,
            "hide_reason": self.hide_reason,
            "review_status": self.review_status or 'none',
            "appeal_reason": self.appeal_reason,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "collect_count": self.collect_count,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if self.cover_image:
            result["cover_image_url"] = self.cover_image.file_path
        else:
            result["cover_image_url"] = None

        if include_category and self.category:
            result["category_name"] = self.category.name

        if include_author and self.author:
            result["author_name"] = self.author.username
            result["author_nickname"] = self.author.nickname
            result["author_avatar"] = self.author.avatar

        if include_attachments:
            result["attachments"] = [a.to_dict() for a in (self.attachments or [])]

        return result

    def __repr__(self):
        return f"<Post {self.title}>"
