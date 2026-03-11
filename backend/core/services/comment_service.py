"""
评论服务
"""
from typing import Dict, List
from sqlalchemy import select, func, and_
from db.session import db
from core.models.comment import Comment
from core.models.file import File
from core.models.user import User


class CommentService:

    @staticmethod
    def get_comments(file_id: int, page: int = 1, page_size: int = 20) -> Dict:
        """
        获取文件评论列表（根评论 + 每条评论的 replies）
        """
        offset = (page - 1) * page_size

        total = db.session.execute(
            select(func.count(Comment.id)).where(
                and_(Comment.file_id == file_id, Comment.parent_id.is_(None))
            )
        ).scalar() or 0

        root_comments = db.session.execute(
            select(Comment)
            .where(and_(Comment.file_id == file_id, Comment.parent_id.is_(None)))
            .order_by(Comment.created_at.desc())
            .offset(offset).limit(page_size)
        ).scalars().all()

        # 批量拉取 replies
        root_ids = [c.id for c in root_comments]
        replies_map: Dict[int, List[Comment]] = {rid: [] for rid in root_ids}
        if root_ids:
            all_replies = db.session.execute(
                select(Comment)
                .where(Comment.parent_id.in_(root_ids))
                .order_by(Comment.created_at.asc())
            ).scalars().all()
            for r in all_replies:
                if r.parent_id in replies_map:
                    replies_map[r.parent_id].append(r)

        items = []
        for c in root_comments:
            d = c.to_dict(include_user=True)
            d['replies'] = [r.to_dict(include_user=True) for r in replies_map.get(c.id, [])]
            items.append(d)

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }

    @staticmethod
    def create_comment(file_id: int, user_id: int, content: str, parent_id: int = None) -> Comment:
        """创建评论"""
        file = db.session.get(File, file_id)
        if not file:
            raise ValueError('文件不存在')

        # 校验 parent_id 只能指向根评论（两级楼）
        if parent_id is not None:
            parent = db.session.get(Comment, parent_id)
            if not parent:
                raise ValueError('父评论不存在')
            if parent.file_id != file_id:
                raise ValueError('父评论不属于该文件')
            if parent.parent_id is not None:
                raise ValueError('评论最多支持两级楼')

        comment = Comment(
            file_id=file_id,
            user_id=user_id,
            parent_id=parent_id,
            content=content.strip()
        )
        db.session.add(comment)
        db.session.commit()
        db.session.refresh(comment)
        return comment

    @staticmethod
    def delete_comment(comment_id: int, operator_id: int, is_admin: bool = False) -> bool:
        """删除评论"""
        comment = db.session.get(Comment, comment_id)
        if not comment:
            raise ValueError('评论不存在')

        if not is_admin and comment.user_id != operator_id:
            raise PermissionError('无权删除此评论')

        db.session.delete(comment)
        db.session.commit()
        return True


comment_service = CommentService()
