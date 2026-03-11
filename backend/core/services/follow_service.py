"""
关注服务 - 处理关注/取消关注逻辑
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_
from db.session import db
from core.models.user import User
from core.models.follow import Follow


class FollowService:
    """关注服务类"""

    @staticmethod
    def get_user_by_id(user_id: int, session: Optional[Session] = None) -> Optional[User]:
        """根据ID获取用户"""
        s = session or db.session
        return s.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    @staticmethod
    def is_following(follower_id: int, following_id: int, session: Optional[Session] = None) -> bool:
        """检查是否已关注"""
        s = session or db.session
        follow = s.execute(
            select(Follow).where(
                and_(
                    Follow.follower_id == follower_id,
                    Follow.following_id == following_id
                )
            )
        ).scalar_one_or_none()
        return follow is not None

    @staticmethod
    def follow_user(follower_id: int, following_id: int) -> Tuple[bool, str]:
        """关注用户"""
        # 不能关注自己
        if follower_id == following_id:
            return False, "不能关注自己"

        with db.session.begin():
            # 检查被关注用户是否存在
            following_user = FollowService.get_user_by_id(following_id)
            if not following_user:
                return False, "用户不存在"

            # 检查是否允许关注
            if following_user.privacy_follow == 0:
                return False, "该用户不允许被关注"

            # 检查是否已关注
            if FollowService.is_following(follower_id, following_id):
                return False, "已经关注过了"

            # 创建关注关系
            follow = Follow(
                follower_id=follower_id,
                following_id=following_id
            )
            db.session.add(follow)

            # 更新关注数
            follower = FollowService.get_user_by_id(follower_id)
            following = FollowService.get_user_by_id(following_id)

            if follower:
                follower.following_count += 1
            if following:
                following.followers_count += 1

        # 通知被关注者
        try:
            from core.services.notification_service import notification_service
            notification_service.create(
                user_id=following_id,
                type_='follow',
                actor_id=follower_id
            )
        except Exception:
            pass

        return True, "关注成功"

    @staticmethod
    def unfollow_user(follower_id: int, following_id: int) -> Tuple[bool, str]:
        """取消关注"""
        with db.session.begin():
            # 查找关注关系
            follow = db.session.execute(
                select(Follow).where(
                    and_(
                        Follow.follower_id == follower_id,
                        Follow.following_id == following_id
                    )
                )
            ).scalar_one_or_none()

            if not follow:
                return False, "未关注该用户"

            # 删除关注关系
            db.session.delete(follow)

            # 更新关注数
            follower = FollowService.get_user_by_id(follower_id)
            following = FollowService.get_user_by_id(following_id)

            if follower and follower.following_count > 0:
                follower.following_count -= 1
            if following and following.followers_count > 0:
                following.followers_count -= 1

        return True, "取消关注成功"

    @staticmethod
    def get_followers(user_id: int, page: int = 1, page_size: int = 20) -> Tuple[List[dict], int]:
        """获取粉丝列表"""
        count_stmt = select(func.count(Follow.id)).where(Follow.following_id == user_id)
        total = db.session.execute(count_stmt).scalar()

        query = (
            select(Follow, User)
            .join(User, Follow.follower_id == User.id)
            .where(Follow.following_id == user_id)
            .order_by(Follow.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        results = db.session.execute(query).all()

        followers = []
        for follow, user in results:
            user_dict = user.to_dict()
            user_dict['followed_at'] = follow.created_at.isoformat()
            followers.append(user_dict)

        return followers, total

    @staticmethod
    def get_following(user_id: int, page: int = 1, page_size: int = 20) -> Tuple[List[dict], int]:
        """获取关注列表"""
        count_stmt = select(func.count(Follow.id)).where(Follow.follower_id == user_id)
        total = db.session.execute(count_stmt).scalar()

        query = (
            select(Follow, User)
            .join(User, Follow.following_id == User.id)
            .where(Follow.follower_id == user_id)
            .order_by(Follow.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        results = db.session.execute(query).all()

        following = []
        for follow, user in results:
            user_dict = user.to_dict()
            user_dict['followed_at'] = follow.created_at.isoformat()
            following.append(user_dict)

        return following, total

    @staticmethod
    def check_follow_status(user_id: int, target_ids: List[int]) -> dict[int, bool]:
        """批量检查关注状态"""
        if not target_ids:
            return {}

        results = db.session.execute(
            select(Follow.following_id)
            .where(
                and_(
                    Follow.follower_id == user_id,
                    Follow.following_id.in_(target_ids)
                )
            )
        ).scalars().all()

        following_set = set(results)
        return {tid: tid in following_set for tid in target_ids}


# 全局实例
follow_service = FollowService()
