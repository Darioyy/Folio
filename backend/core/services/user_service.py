"""
用户服务层 - 业务逻辑
"""
import bcrypt
import os
import random
import string
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from core.models.user import User
from core.models.post import Post
from core.models.file import File
from core.schemas.user import UserCreate, UserUpdate, ProfileUpdate
from core.utils.permissions import can_modify_user, can_delete_user, get_user_role
from core.utils.constants import Role
from core.services.system_service import SystemService


class UserService:
    """用户服务类"""

    @staticmethod
    def _generate_uid(db_session: Session) -> str:
        """生成唯一的 8 位数字 uid"""
        for _ in range(20):
            uid = ''.join(random.choices(string.digits, k=8))
            existing = db_session.execute(select(User).where(User.uid == uid)).scalar_one_or_none()
            if not existing:
                return uid
        raise ValueError('生成 uid 失败，请重试')

    @staticmethod
    def hash_password(password: str) -> str:
        """
        对密码进行哈希

        Args:
            password: 明文密码

        Returns:
            哈希后的密码
        """
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码
            password_hash: 哈希密码

        Returns:
            是否匹配
        """
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    @staticmethod
    def get_by_id(user_id: int, db_session: Session) -> Optional[User]:
        """
        根据 ID 获取用户

        Args:
            user_id: 用户ID
            db_session: 数据库会话

        Returns:
            用户对象或 None
        """
        return db_session.get(User, user_id)

    @staticmethod
    def get_by_username(username: str, db_session: Session) -> Optional[User]:
        """
        根据用户名获取用户

        Args:
            username: 用户名
            db_session: 数据库会话

        Returns:
            用户对象或 None
        """
        stmt = select(User).where(User.username == username)
        return db_session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(user_data: UserCreate, db_session: Session) -> User:
        """
        创建新用户

        Args:
            user_data: 用户数据
            db_session: 数据库会话

        Returns:
            创建的用户对象
        """
        # 检查用户名是否已存在
        existing = UserService.get_by_username(user_data.username, db_session)
        if existing:
            raise ValueError('用户名已存在')

        # 根据系统配置和角色确定存储配额
        config = SystemService.load_config()
        is_root = getattr(user_data, 'is_root', 0) or 0
        is_admin = getattr(user_data, 'is_admin', 0) or 0
        if is_root:
            storage_quota = config.get('storage_quota_root', 10737418240)
        elif is_admin:
            storage_quota = config.get('storage_quota_admin', 5368709120)
        else:
            storage_quota = config.get('storage_quota_user', 1073741824)

        # 生成唯一 uid
        uid = UserService._generate_uid(db_session)

        # 创建用户
        user = User(
            uid=uid,
            username=user_data.username,
            password_hash=UserService.hash_password(user_data.password),
            email=user_data.email,
            nickname=getattr(user_data, 'nickname', None),
            storage_quota=storage_quota,
            is_admin=is_admin,
            is_root=0
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return user

    @staticmethod
    def update(user_id: int, user_data: UserUpdate, operator_id: int, db_session: Session) -> User:
        """
        更新用户信息

        Args:
            user_id: 用户ID
            user_data: 更新数据
            operator_id: 操作者ID
            db_session: 数据库会话

        Returns:
            更新后的用户对象
        """
        user = UserService.get_by_id(user_id, db_session)
        if not user:
            raise ValueError('用户不存在')

        # 权限检查
        if not can_modify_user(operator_id, user_id, db_session):
            raise PermissionError('无权修改此用户')

        # 修改 uid（仅 Root 可操作）
        if getattr(user_data, 'uid', None) is not None and user_data.uid.strip():
            operator_role = get_user_role(operator_id, db_session)
            if operator_role < Role.ROOT:
                raise PermissionError('只有超级管理员可以修改用户 uid')
            new_uid = user_data.uid.strip()
            if new_uid != user.uid:
                if len(new_uid) != 8 or not new_uid.isdigit():
                    raise ValueError('uid 必须为 8 位数字字符串')
                existing = db_session.execute(select(User).where(User.uid == new_uid)).scalar_one_or_none()
                if existing:
                    raise ValueError('该 uid 已被占用')
                user.uid = new_uid

        # 修改用户名（仅 Root 可操作）
        if user_data.username is not None and user_data.username.strip():
            operator_role = get_user_role(operator_id, db_session)
            if operator_role < Role.ROOT:
                raise PermissionError('只有超级管理员可以修改用户名')
            new_username = user_data.username.strip()
            if new_username != user.username:
                existing = UserService.get_by_username(new_username, db_session)
                if existing:
                    raise ValueError('用户名已被占用')
                user.username = new_username

        # 更新字段
        if user_data.email is not None and user_data.email != '':
            user.email = user_data.email

        if user_data.password is not None:
            user.password_hash = UserService.hash_password(user_data.password)

        # 更新管理员/超级管理员权限
        role_changed = False
        if user_data.is_admin is not None:
            user.is_admin = user_data.is_admin
            role_changed = True

        if user_data.is_root is not None:
            user.is_root = user_data.is_root
            role_changed = True

        # 角色变更时同步更新存储配额
        if role_changed:
            config = SystemService.load_config()
            if user.is_root:
                user.storage_quota = config.get('storage_quota_root', 10737418240)
            elif user.is_admin:
                user.storage_quota = config.get('storage_quota_admin', 5368709120)
            else:
                user.storage_quota = config.get('storage_quota_user', 1073741824)

        db_session.commit()
        db_session.refresh(user)

        return user

    @staticmethod
    def delete(user_id: int, operator_id: int, db_session: Session) -> bool:
        """
        删除用户（级联清理所有关联数据）

        Args:
            user_id: 用户ID
            operator_id: 操作者ID
            db_session: 数据库会话

        Returns:
            是否删除成功
        """
        from sqlalchemy import delete as sa_delete, select as sa_select, or_, text
        from core.models.notification import Notification as NotifModel
        from core.models.follow import Follow
        from core.models.interaction import Like, Collection
        from core.models.comment import Comment, CommentLike
        from core.models.post import Post as PostModel
        from core.models.post_attachment import PostAttachment

        user = UserService.get_by_id(user_id, db_session)
        if not user:
            raise ValueError('用户不存在')

        # 权限检查
        if not can_delete_user(operator_id, user_id, db_session):
            raise PermissionError('无权删除此用户')

        # 1. 删除关注关系（Follow 无 FK 约束，必须手动清理）
        db_session.execute(sa_delete(Follow).where(
            or_(Follow.follower_id == user_id, Follow.following_id == user_id)
        ))

        # 2. 获取该用户所有博文 ID，级联清理博文相关数据
        post_ids = list(db_session.execute(
            sa_select(PostModel.id).where(PostModel.author_id == user_id)
        ).scalars())

        if post_ids:
            comment_ids = list(db_session.execute(
                sa_select(Comment.id).where(Comment.post_id.in_(post_ids))
            ).scalars())
            if comment_ids:
                db_session.execute(sa_delete(CommentLike).where(CommentLike.comment_id.in_(comment_ids)))
            db_session.execute(sa_delete(Comment).where(Comment.post_id.in_(post_ids)))
            db_session.execute(sa_delete(Like).where(Like.post_id.in_(post_ids)))
            db_session.execute(sa_delete(Collection).where(Collection.post_id.in_(post_ids)))
            db_session.execute(sa_delete(PostAttachment).where(PostAttachment.post_id.in_(post_ids)))

        # 3. 清理该用户在他人博文下的评论点赞、评论、点赞、收藏
        user_comment_ids = list(db_session.execute(
            sa_select(Comment.id).where(Comment.user_id == user_id)
        ).scalars())
        if user_comment_ids:
            db_session.execute(sa_delete(CommentLike).where(CommentLike.comment_id.in_(user_comment_ids)))
        db_session.execute(sa_delete(CommentLike).where(CommentLike.user_id == user_id))
        db_session.execute(sa_delete(Comment).where(Comment.user_id == user_id))
        db_session.execute(sa_delete(Like).where(Like.user_id == user_id))
        db_session.execute(sa_delete(Collection).where(Collection.user_id == user_id))

        # 4. 删除通知（actor_id/user_id 的通知）
        db_session.execute(sa_delete(NotifModel).where(
            or_(NotifModel.user_id == user_id, NotifModel.actor_id == user_id)
        ))

        # 5. 删除博文
        db_session.execute(sa_delete(PostModel).where(PostModel.author_id == user_id))

        # 6. flush 后通过 raw SQL 删除用户，绕开 ORM 关系拦截（files 有 ondelete=CASCADE 由 DB 处理）
        db_session.flush()
        db_session.execute(text('DELETE FROM users WHERE id = :uid'), {'uid': user_id})
        db_session.commit()

        return True

    @staticmethod
    def list_users(db_session: Session, page: int = 1, page_size: int = 20) -> dict:
        """
        获取用户列表

        Args:
            page: 页码
            page_size: 每页数量
            db_session: 数据库会话

        Returns:
            用户列表和分页信息
        """
        # 计算偏移量
        offset = (page - 1) * page_size

        # 查询总数
        total = db_session.execute(select(func.count(User.id))).scalar() or 0

        # 查询用户（ROOT 置顶）
        stmt = select(User).order_by(User.is_root.desc(), User.id.asc()).offset(offset).limit(page_size)
        users = list(db_session.execute(stmt).scalars())

        return {
            'items': [user.to_dict(show_email=True) for user in users],
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }

    @staticmethod
    def authenticate(username: str, password: str, db_session: Session) -> Optional[User]:
        """
        用户认证

        Args:
            username: 用户名
            password: 密码
            db_session: 数据库会话

        Returns:
            认证成功返回用户对象，失败返回 None
        """
        user = UserService.get_by_username(username, db_session)
        if not user:
            return None

        if UserService.verify_password(password, user.password_hash):
            return user

        return None

    @staticmethod
    def update_profile(user_id: int, profile_data: ProfileUpdate, db_session: Session) -> User:
        """
        更新个人资料

        Args:
            user_id: 用户ID
            profile_data: 个人资料数据
            db_session: 数据库会话

        Returns:
            更新后的用户对象
        """
        user = UserService.get_by_id(user_id, db_session)
        if not user:
            raise ValueError('用户不存在')

        # 更新字段
        if profile_data.nickname is not None:
            user.nickname = profile_data.nickname

        if profile_data.signature is not None:
            user.signature = profile_data.signature

        if profile_data.email is not None and profile_data.email != '':
            user.email = profile_data.email

        db_session.commit()
        db_session.refresh(user)

        return user

    @staticmethod
    def update_avatar(user_id: int, avatar_path: str, db_session: Session) -> User:
        """
        更新用户头像

        Args:
            user_id: 用户ID
            avatar_path: 头像文件相对路径
            db_session: 数据库会话

        Returns:
            更新后的用户对象
        """
        user = UserService.get_by_id(user_id, db_session)
        if not user:
            raise ValueError('用户不存在')

        # 删除旧头像文件
        if user.avatar:
            from config.default import Config
            uploads_dir = os.path.abspath(Config.UPLOAD_FOLDER)
            old_avatar_path = os.path.join(uploads_dir, user.avatar)
            if os.path.exists(old_avatar_path):
                try:
                    os.remove(old_avatar_path)
                except Exception:
                    pass  # 忽略删除失败

        user.avatar = avatar_path
        db_session.commit()
        db_session.refresh(user)

        return user

    @staticmethod
    def get_user_stats(user_id: int, db_session: Session) -> Dict[str, Any]:
        """
        获取用户统计数据

        Args:
            user_id: 用户ID
            db_session: 数据库会话

        Returns:
            统计数据字典
        """
        # 统计文章数量
        post_count = db_session.execute(
            select(func.count(Post.id)).where(Post.author_id == user_id)
        ).scalar() or 0

        # 统计媒体数量（image + video）
        media_count = db_session.execute(
            select(func.count(File.id)).where(
                File.user_id == user_id,
                File.file_category.in_(['image', 'video'])
            )
        ).scalar() or 0

        # 统计资源数量
        resource_count = db_session.execute(
            select(func.count(File.id)).where(
                File.user_id == user_id,
                File.file_category == 'resource'
            )
        ).scalar() or 0

        # 计算总存储大小
        total_size = db_session.execute(
            select(func.sum(File.file_size)).where(File.user_id == user_id)
        ).scalar() or 0

        return {
            'posts': post_count,
            'media': media_count,
            'resources': resource_count,
            'total_size': total_size
        }

    @staticmethod
    def get_storage_categories(user_id: int, db_session: Session) -> List[Dict[str, Any]]:
        """
        获取用户存储分类统计

        Args:
            user_id: 用户ID
            db_session: 数据库会话

        Returns:
            分类统计列表
        """
        categories = []

        # 统计图片（files 表 file_category=image）
        image_count = db_session.execute(
            select(func.count(File.id)).where(
                File.user_id == user_id,
                File.file_category == 'image'
            )
        ).scalar() or 0

        image_size = db_session.execute(
            select(func.sum(File.file_size)).where(
                File.user_id == user_id,
                File.file_category == 'image'
            )
        ).scalar() or 0

        if image_count > 0:
            categories.append({
                'type': 'image',
                'name': '图片',
                'count': image_count,
                'size': image_size
            })

        # 统计视频（files 表 file_category=video）
        video_count = db_session.execute(
            select(func.count(File.id)).where(
                File.user_id == user_id,
                File.file_category == 'video'
            )
        ).scalar() or 0

        video_size = db_session.execute(
            select(func.sum(File.file_size)).where(
                File.user_id == user_id,
                File.file_category == 'video'
            )
        ).scalar() or 0

        if video_count > 0:
            categories.append({
                'type': 'video',
                'name': '视频',
                'count': video_count,
                'size': video_size
            })

        # 统计文章（Post）- 实际计算大小
        posts = db_session.execute(
            select(Post).where(Post.author_id == user_id)
        ).scalars().all()

        post_count = len(posts)
        post_size = 0

        for post in posts:
            # 计算每篇文章的实际大小（标题 + 内容 + 摘要的字节数）
            size = len(post.title.encode('utf-8'))
            if post.content:
                size += len(post.content.encode('utf-8'))
            if post.summary:
                size += len(post.summary.encode('utf-8'))
            post_size += size

        if post_count > 0:
            categories.append({
                'type': 'document',
                'name': '文章',
                'count': post_count,
                'size': post_size
            })

        # 统计资源（files 表 file_category=resource）
        resource_count = db_session.execute(
            select(func.count(File.id)).where(
                File.user_id == user_id,
                File.file_category == 'resource'
            )
        ).scalar() or 0

        resource_size = db_session.execute(
            select(func.sum(File.file_size)).where(
                File.user_id == user_id,
                File.file_category == 'resource'
            )
        ).scalar() or 0

        if resource_count > 0:
            categories.append({
                'type': 'resource',
                'name': '资源',
                'count': resource_count,
                'size': resource_size
            })

        # 按大小降序排序
        categories.sort(key=lambda x: x['size'], reverse=True)

        return categories
