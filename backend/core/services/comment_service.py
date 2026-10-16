"""
评论服务（v3.0：绑定 post_id）
"""
from typing import Dict, List
from sqlalchemy import select, func, and_, update as sql_update
from sqlalchemy.orm import joinedload
from db.session import db
from core.models.comment import Comment
from core.models.post import Post


class CommentService:

    @staticmethod
    def get_comments(post_id: int, page: int = 1, page_size: int = 20, viewer_id: int = None) -> Dict:
        """获取博文评论列表（根评论 + 每条评论的 replies）"""
        offset = (page - 1) * page_size

        total = db.session.execute(
            select(func.count(Comment.id)).where(
                and_(Comment.post_id == post_id, Comment.parent_id.is_(None))
            )
        ).scalar() or 0

        root_comments = db.session.execute(
            select(Comment)
            .options(joinedload(Comment.user))
            .where(and_(Comment.post_id == post_id, Comment.parent_id.is_(None)))
            .order_by(Comment.created_at.desc())
            .offset(offset).limit(page_size)
        ).scalars().all()

        # 批量拉取 replies
        root_ids = [c.id for c in root_comments]
        replies_map: Dict[int, List[Comment]] = {rid: [] for rid in root_ids}
        all_reply_ids = []
        if root_ids:
            all_replies = db.session.execute(
                select(Comment)
                .options(joinedload(Comment.user))
                .where(Comment.parent_id.in_(root_ids))
                .order_by(Comment.created_at.asc())
            ).scalars().all()
            for r in all_replies:
                if r.parent_id in replies_map:
                    replies_map[r.parent_id].append(r)
                all_reply_ids.append(r.id)

        # 批量查询点赞状态
        liked_set: set = set()
        if viewer_id:
            from core.models.comment import CommentLike
            all_ids = root_ids + all_reply_ids
            if all_ids:
                liked_rows = db.session.execute(
                    select(CommentLike.comment_id).where(
                        and_(CommentLike.user_id == viewer_id, CommentLike.comment_id.in_(all_ids))
                    )
                ).scalars().all()
                liked_set = set(liked_rows)

        items = []
        for c in root_comments:
            d = c.to_dict(include_user=True, liked=(c.id in liked_set))
            d['replies'] = [r.to_dict(include_user=True, liked=(r.id in liked_set)) for r in replies_map.get(c.id, [])]
            items.append(d)

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }

    @staticmethod
    def create_comment(post_id: int, user_id: int, content: str, parent_id: int = None) -> Comment:
        """创建评论"""
        post = db.session.get(Post, post_id)
        if not post:
            raise ValueError('博文不存在')
        if post.status != 'published':
            raise ValueError('只能评论已发布的博文')

        # 校验 parent_id 只能指向根评论（两级楼）
        if parent_id is not None:
            parent = db.session.get(Comment, parent_id)
            if not parent:
                raise ValueError('父评论不存在')
            if parent.post_id != post_id:
                raise ValueError('父评论不属于该博文')
            if parent.parent_id is not None:
                raise ValueError('评论最多支持两级楼')

        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            parent_id=parent_id,
            content=content.strip()
        )
        db.session.add(comment)

        # 原子更新评论计数（仅根评论 +1），防并发丢失
        if parent_id is None:
            db.session.execute(
                sql_update(Post).where(Post.id == post_id)
                .values(comment_count=Post.comment_count + 1)
            )

        db.session.commit()
        db.session.refresh(comment)

        # 通知：评论通知博文作者，回复通知父评论者（失败静默）
        try:
            from core.services.notification_service import notification_service
            if parent_id is None and post.author_id != user_id:
                notification_service.create(
                    user_id=post.author_id,
                    type_='comment',
                    actor_id=user_id,
                    target_id=post_id
                )
            elif parent_id is not None:
                parent = db.session.get(Comment, parent_id)
                if parent and parent.user_id != user_id:
                    notification_service.create(
                        user_id=parent.user_id,
                        type_='reply',
                        actor_id=user_id,
                        target_id=post_id
                    )
        except Exception:
            pass

        return comment

    @staticmethod
    def delete_comment(comment_id: int, operator_id: int, is_admin: bool = False) -> bool:
        """删除评论"""
        from sqlalchemy import delete as sql_delete

        comment = db.session.get(Comment, comment_id)
        if not comment:
            raise ValueError('评论不存在')

        if not is_admin and comment.user_id != operator_id:
            raise PermissionError('无权删除此评论')

        if comment.parent_id is None:
            # 根评论：先显式 DELETE 所有回复，避免 ORM 将 parent_id 置 NULL
            db.session.execute(
                sql_delete(Comment).where(Comment.parent_id == comment_id)
            )
            # 原子更新评论计数（根评论 -1）
            db.session.execute(
                sql_update(Post).where(Post.id == comment.post_id)
                .values(comment_count=func.greatest(0, Post.comment_count - 1))
            )

        db.session.delete(comment)
        db.session.commit()
        return True

    @staticmethod
    def update_comment(comment_id: int, user_id: int, content: str) -> 'Comment':
        """编辑评论（仅作者）"""
        comment = db.session.get(Comment, comment_id)
        if not comment:
            raise ValueError('评论不存在')
        if comment.user_id != user_id:
            raise PermissionError('无权编辑此评论')
        comment.content = content.strip()
        db.session.commit()
        db.session.refresh(comment)
        return comment

    @staticmethod
    def toggle_comment_like(user_id: int, comment_id: int) -> dict:
        """切换评论点赞"""
        from core.models.comment import CommentLike
        from sqlalchemy import select
        comment = db.session.get(Comment, comment_id)
        if not comment:
            raise ValueError('评论不存在')
        existing = db.session.execute(
            select(CommentLike).where(
                CommentLike.user_id == user_id,
                CommentLike.comment_id == comment_id
            )
        ).scalar_one_or_none()
        if existing:
            db.session.delete(existing)
            db.session.execute(
                sql_update(Comment).where(Comment.id == comment_id)
                .values(like_count=func.greatest(0, Comment.like_count - 1))
            )
            liked = False
        else:
            cl = CommentLike(user_id=user_id, comment_id=comment_id)
            db.session.add(cl)
            db.session.execute(
                sql_update(Comment).where(Comment.id == comment_id)
                .values(like_count=Comment.like_count + 1)
            )
            liked = True
        db.session.flush()
        db.session.expire(comment)
        db.session.commit()
        return {'liked': liked, 'like_count': comment.like_count}


comment_service = CommentService()
