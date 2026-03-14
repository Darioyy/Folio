"""
反馈/建议模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from db.session import db as db_session


class Feedback(db_session.Model):
    """用户反馈/建议表"""

    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    type = Column(
        Enum("suggestion", "bug", "other", name="feedback_type_enum"),
        nullable=False,
        default="suggestion",
        comment="反馈类型",
    )
    content = Column(Text, nullable=False, comment="反馈内容")
    status = Column(
        Enum("pending", "resolved", name="feedback_status_enum"),
        nullable=False,
        default="pending",
        comment="处理状态",
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    author = relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "content": self.content,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "author": {
                "username": self.author.username,
                "nickname": self.author.nickname,
                "avatar": self.author.avatar,
            } if self.author else None,
        }
