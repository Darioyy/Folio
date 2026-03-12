"""
博文附件模型 - 博文与云盘文件的关联关系
"""
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from db.session import db


class PostAttachment(db.Model):
    """博文附件关联表"""
    __tablename__ = 'post_attachments'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='附件关联ID')
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False, comment='博文ID')
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'), nullable=False, comment='文件ID')
    sort_order = Column(Integer, default=0, nullable=False, comment='排序权重')

    post = relationship('Post', back_populates='attachments')
    file = relationship('File')

    __table_args__ = (
        UniqueConstraint('post_id', 'file_id', name='uq_pa'),
        Index('idx_pa_post', 'post_id'),
        {'comment': '博文附件关联表'}
    )

    def to_dict(self):
        """返回附件文件元数据"""
        f = self.file
        if not f:
            return {'file_id': self.file_id, 'sort_order': self.sort_order}
        return {
            'file_id': f.id,
            'file_name': f.file_name,
            'file_size': f.file_size,
            'mime_type': f.mime_type,
            'file_category': f.file_category,
            'sort_order': self.sort_order,
        }
