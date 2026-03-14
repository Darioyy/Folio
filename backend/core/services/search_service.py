"""
搜索服务
"""
from typing import Dict
from sqlalchemy import select, func, or_
from db.session import db
from core.models.file import File
from core.models.user import User


class SearchService:

    @staticmethod
    def search(q: str, type_: str = 'all', page: int = 1, page_size: int = 20) -> Dict:
        """
        全站搜索
        type_: 'file' | 'user' | 'all'
        仅搜索公开文件
        """
        q = q.strip()[:100]  # P2: 截断超长搜索词，防全表扫描
        if not q:
            return {'files': [], 'users': [], 'total': 0}

        like_q = f'%{q}%'
        offset = (page - 1) * page_size
        result = {}

        if type_ in ('file', 'all'):
            file_total = db.session.execute(
                select(func.count(File.id)).where(
                    File.visibility == 'public',
                    or_(File.title.like(like_q), File.description.like(like_q))
                )
            ).scalar() or 0

            files = db.session.execute(
                select(File)
                .where(
                    File.visibility == 'public',
                    or_(File.title.like(like_q), File.description.like(like_q))
                )
                .order_by(File.created_at.desc())
                .offset(offset).limit(page_size)
            ).scalars().all()

            result['files'] = [f.to_dict(include_user=True) for f in files]
            result['file_total'] = file_total

        if type_ in ('user', 'all'):
            user_total = db.session.execute(
                select(func.count(User.id)).where(
                    or_(User.username.like(like_q), User.nickname.like(like_q))
                )
            ).scalar() or 0

            users = db.session.execute(
                select(User)
                .where(or_(User.username.like(like_q), User.nickname.like(like_q)))
                .order_by(User.created_at.desc())
                .offset(offset).limit(page_size)
            ).scalars().all()

            result['users'] = [SearchService._user_to_dict(u) for u in users]
            result['user_total'] = user_total

        result['page'] = page
        result['page_size'] = page_size
        return result

    @staticmethod
    def _user_to_dict(user: User) -> dict:
        return {
            'id': user.id,
            'uid': user.uid,
            'username': user.username,
            'nickname': user.nickname,
            'avatar': user.avatar,
            'signature': user.signature,
            'is_admin': user.is_admin,
            'is_root': user.is_root,
            'followers_count': user.followers_count,
            'following_count': user.following_count,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }


search_service = SearchService()
