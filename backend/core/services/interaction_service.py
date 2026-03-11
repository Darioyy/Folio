"""
点赞 / 收藏服务
"""
from typing import Dict, List
from sqlalchemy import select, and_
from db.session import db
from core.models.interaction import Like, Collection
from core.models.file import File


class InteractionService:
    """点赞和收藏服务"""

    # ============================================================
    # 点赞
    # ============================================================

    @staticmethod
    def toggle_like(user_id: int, file_id: int) -> Dict:
        """切换点赞状态，返回 {liked: bool, like_count: int}"""
        with db.session.begin():
            existing = db.session.execute(
                select(Like).where(and_(Like.user_id == user_id, Like.file_id == file_id))
            ).scalar_one_or_none()

            file = db.session.get(File, file_id)
            if not file:
                raise ValueError('文件不存在')

            if existing:
                db.session.delete(existing)
                file.like_count = max(0, (file.like_count or 0) - 1)
                liked = False
            else:
                db.session.add(Like(user_id=user_id, file_id=file_id))
                file.like_count = (file.like_count or 0) + 1
                liked = True

        return {'liked': liked, 'like_count': file.like_count}

    @staticmethod
    def is_liked(user_id: int, file_id: int) -> bool:
        like = db.session.execute(
            select(Like).where(and_(Like.user_id == user_id, Like.file_id == file_id))
        ).scalar_one_or_none()
        return like is not None

    # ============================================================
    # 收藏
    # ============================================================

    @staticmethod
    def toggle_collect(user_id: int, file_id: int) -> Dict:
        """切换收藏状态，返回 {collected: bool, collect_count: int}"""
        with db.session.begin():
            existing = db.session.execute(
                select(Collection).where(and_(Collection.user_id == user_id, Collection.file_id == file_id))
            ).scalar_one_or_none()

            file = db.session.get(File, file_id)
            if not file:
                raise ValueError('文件不存在')

            if existing:
                db.session.delete(existing)
                file.collect_count = max(0, (file.collect_count or 0) - 1)
                collected = False
            else:
                db.session.add(Collection(user_id=user_id, file_id=file_id))
                file.collect_count = (file.collect_count or 0) + 1
                collected = True

        return {'collected': collected, 'collect_count': file.collect_count}

    @staticmethod
    def is_collected(user_id: int, file_id: int) -> bool:
        coll = db.session.execute(
            select(Collection).where(and_(Collection.user_id == user_id, Collection.file_id == file_id))
        ).scalar_one_or_none()
        return coll is not None

    # ============================================================
    # 批量状态查询
    # ============================================================

    @staticmethod
    def batch_status(user_id: int, file_ids: List[int]) -> Dict:
        """批量查询一批文件的 liked/collected 状态"""
        if not file_ids:
            return {}

        liked_ids = set(db.session.execute(
            select(Like.file_id).where(and_(Like.user_id == user_id, Like.file_id.in_(file_ids)))
        ).scalars().all())

        collected_ids = set(db.session.execute(
            select(Collection.file_id).where(and_(Collection.user_id == user_id, Collection.file_id.in_(file_ids)))
        ).scalars().all())

        return {
            fid: {'liked': fid in liked_ids, 'collected': fid in collected_ids}
            for fid in file_ids
        }

    # ============================================================
    # 用户收藏列表
    # ============================================================

    @staticmethod
    def get_user_collections(user_id: int, page: int = 1, page_size: int = 20) -> Dict:
        """获取用户收藏的文件列表"""
        from sqlalchemy import func
        offset = (page - 1) * page_size

        total = db.session.execute(
            select(func.count(Collection.id)).where(Collection.user_id == user_id)
        ).scalar() or 0

        rows = db.session.execute(
            select(Collection, File)
            .join(File, Collection.file_id == File.id)
            .where(Collection.user_id == user_id)
            .order_by(Collection.created_at.desc())
            .offset(offset).limit(page_size)
        ).all()

        items = []
        for coll, f in rows:
            d = f.to_dict(include_user=True)
            d['collected_at'] = coll.created_at.isoformat()
            items.append(d)

        return {
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }


interaction_service = InteractionService()
