"""
文件分组模型 - SQLAlchemy ORM
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from db.session import db as db_session


class FileGroup(db_session.Model):
    """文件分组表"""
    __tablename__ = 'file_groups'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='分组ID')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='所属用户ID')
    parent_id = Column(Integer, ForeignKey('file_groups.id', ondelete='SET NULL'), nullable=True, default=None, comment='父分组ID（NULL=根目录）')
    name = Column(String(100), nullable=False, comment='分组名称')
    sort_order = Column(Integer, default=0, nullable=False, comment='排序权重')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')

    # 关系
    user = relationship('User', backref='file_groups')
    files = relationship('File', back_populates='group', foreign_keys='[File.group_id]')

    __table_args__ = (
        Index('idx_group_user', 'user_id'),
        Index('idx_group_parent', 'parent_id'),
        {'comment': '文件分组表'}
    )

    def to_dict(self, file_count: int = 0, children_count: int = 0) -> dict:
        return {
            'id': self.id,
            'parent_id': self.parent_id,
            'name': self.name,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'file_count': file_count,
            'children_count': children_count,
        }

    def __repr__(self):
        return f'<FileGroup {self.name}>'
