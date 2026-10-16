"""
点赞 / 收藏服务（v3.0：绑定 post_id）
"""
from typing import Dict, List
from sqlalchemy import select, and_, func, update as sql_update
from db.session import db
from core.models.interaction import Like, Collection
from core.models.post import Post


class InteractionService:
    """点赞和收藏服务"""

    # ============================================================
    # 点赞
    # ============================================================

    @staticmethod
    def toggle_like(user_id: int, post_id: int) -> Dict:
        """切换点赞状态，返回 {liked: bool, like_count: int}"""
        with db.session.begin():
            post = db.session.get(Post, post_id)
            if not post:
                raise ValueError('博文不存在')

            existing = db.session.execute(
                select(Like).where(and_(Like.user_id == user_id, Like.post_id == post_id))
            ).scalar_one_or_none()

            if existing:
                db.session.delete(existing)
                db.session.execute(
                    sql_update(Post).where(Post.id == post_id)
                    .values(like_count=func.greatest(0, Post.like_count - 1))
                )
                liked = False
            else:
                db.session.add(Like(user_id=user_id, post_id=post_id))
                db.session.execute(
                    sql_update(Post).where(Post.id == post_id)
                    .values(like_count=Post.like_count + 1)
                )
                liked = True
            db.session.flush()
            db.session.expire(post)

        # 通知/撤销通知（幂等，避免反复点赞重复通知）
        if post.author_id != user_id:
            try:
                from core.services.notification_service import notification_service
                if liked:
                    notification_service.upsert(
                        user_id=post.author_id, type_='like',
                        actor_id=user_id, target_id=post_id
                    )
                else:
                    notification_service.delete_by_actor(
                        user_id=post.author_id, type_='like',
                        actor_id=user_id, target_id=post_id
                    )
            except Exception:
                pass

        return {'liked': liked, 'like_count': post.like_count}

    @staticmethod
    def is_liked(user_id: int, post_id: int) -> bool:
        like = db.session.execute(
            select(Like).where(and_(Like.user_id == user_id, Like.post_id == post_id))
        ).scalar_one_or_none()
        return like is not None

    # ============================================================
    # 收藏
    # ============================================================

    @staticmethod
    def toggle_collect(user_id: int, post_id: int) -> Dict:
        """切换收藏状态，返回 {collected: bool, collect_count: int}"""
        with db.session.begin():
            post = db.session.get(Post, post_id)
            if not post:
                raise ValueError('博文不存在')

            existing = db.session.execute(
                select(Collection).where(and_(Collection.user_id == user_id, Collection.post_id == post_id))
            ).scalar_one_or_none()

            if existing:
                db.session.delete(existing)
                db.session.execute(
                    sql_update(Post).where(Post.id == post_id)
                    .values(collect_count=func.greatest(0, Post.collect_count - 1))
                )
                collected = False
            else:
                db.session.add(Collection(user_id=user_id, post_id=post_id))
                db.session.execute(
                    sql_update(Post).where(Post.id == post_id)
                    .values(collect_count=Post.collect_count + 1)
                )
                collected = True
            db.session.flush()
            db.session.expire(post)

        # 通知/撤销通知（幂等）
        if post.author_id != user_id:
            try:
                from core.services.notification_service import notification_service
                if collected:
                    notification_service.upsert(
                        user_id=post.author_id, type_='collect',
                        actor_id=user_id, target_id=post_id
                    )
                else:
                    notification_service.delete_by_actor(
                        user_id=post.author_id, type_='collect',
                        actor_id=user_id, target_id=post_id
                    )
            except Exception:
                pass

        return {'collected': collected, 'collect_count': post.collect_count}

    @staticmethod
    def is_collected(user_id: int, post_id: int) -> bool:
        coll = db.session.execute(
            select(Collection).where(and_(Collection.user_id == user_id, Collection.post_id == post_id))
        ).scalar_one_or_none()
        return coll is not None

    # ============================================================
    # 批量状态查询
    # ============================================================

    @staticmethod
    def batch_status(user_id: int, post_ids: List[int]) -> Dict:
        """批量查询多篇博文的 liked/collected 状态"""
        if not post_ids:
            return {}

        liked_ids = set(db.session.execute(
            select(Like.post_id).where(and_(Like.user_id == user_id, Like.post_id.in_(post_ids)))
        ).scalars().all())

        collected_ids = set(db.session.execute(
            select(Collection.post_id).where(and_(Collection.user_id == user_id, Collection.post_id.in_(post_ids)))
        ).scalars().all())

        return {
            pid: {'liked': pid in liked_ids, 'collected': pid in collected_ids}
            for pid in post_ids
        }

    # ============================================================
    # 用户收藏列表
    # ============================================================

    @staticmethod
    def get_user_collections(user_id: int, page: int = 1, page_size: int = 20, folder_id=None) -> Dict:
        """获取用户收藏的博文列表
        folder_id=None  → 全部收藏
        folder_id=0     → 未分类（folder_id IS NULL）
        folder_id>0     → 指定收藏夹
        """
        from sqlalchemy import func
        offset = (page - 1) * page_size

        base_where = [Collection.user_id == user_id]
        if folder_id is None:
            pass  # 不过滤 folder_id
        elif folder_id == 0:
            base_where.append(Collection.folder_id.is_(None))
        else:
            base_where.append(Collection.folder_id == folder_id)

        total = db.session.execute(
            select(func.count(Collection.id)).where(*base_where)
        ).scalar() or 0

        rows = db.session.execute(
            select(Collection, Post)
            .join(Post, Collection.post_id == Post.id)
            .where(*base_where)
            .order_by(Collection.created_at.desc())
            .offset(offset).limit(page_size)
        ).all()

        items = []
        for coll, p in rows:
            d = p.to_dict(include_author=True, include_category=True)
            d['collected_at'] = coll.created_at.isoformat()
            d['folder_id'] = coll.folder_id
            items.append(d)

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }


interaction_service = InteractionService()
