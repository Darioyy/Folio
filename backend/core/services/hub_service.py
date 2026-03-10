"""
个人工作台服务层 - Private Hub 业务逻辑
"""
import os
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func

from core.models.media import Media
from core.models.resource import Resource
from core.models.user import User
from db.session import db as db_session


logger = logging.getLogger(__name__)


class HubService:
    """个人工作台服务类"""

    @staticmethod
    def get_storage_info(user_id: int, db_session: Session) -> Dict[str, Any]:
        """
        获取用户存储配额信息（实时计算）

        Args:
            user_id: 用户ID
            db_session: 数据库会话

        Returns:
            存储配额信息字典
        """
        user = db_session.get(User, user_id)
        if not user:
            raise ValueError('用户不存在')

        # 实时计算存储使用量
        # 计算媒体文件大小
        media_size = db_session.execute(
            select(func.sum(Media.file_size)).where(Media.uploader_id == user_id)
        ).scalar() or 0

        # 计算资源文件大小
        resource_size = db_session.execute(
            select(func.sum(Resource.file_size)).where(Resource.uploader_id == user_id)
        ).scalar() or 0

        storage_used = (media_size or 0) + (resource_size or 0)
        storage_quota = user.storage_quota or 209715200  # 默认 200MB

        return {
            'storage_used': storage_used,
            'storage_quota': storage_quota,
            'storage_percentage': round(storage_used / storage_quota * 100, 2) if storage_quota > 0 else 0
        }

    @staticmethod
    def toggle_media_visibility(user_id: int, media_id: int, db_session: Session) -> str:
        """
        切换媒体文件可见性

        Args:
            user_id: 用户ID
            media_id: 媒体ID
            db_session: 数据库会话

        Returns:
            新的可见性状态 ('private' 或 'public')
        """
        media = db_session.get(Media, media_id)
        if not media:
            raise ValueError('媒体文件不存在')

        # 权限检查：只有所有者可以修改可见性
        if media.uploader_id != user_id:
            raise PermissionError('无权修改此文件')

        # 切换可见性
        new_visibility = 'public' if media.visibility == 'private' else 'private'
        media.visibility = new_visibility
        db_session.commit()

        return new_visibility

    @staticmethod
    def toggle_resource_visibility(user_id: int, resource_id: int, db_session: Session) -> str:
        """
        切换资源文件可见性

        Args:
            user_id: 用户ID
            resource_id: 资源ID
            db_session: 数据库会话

        Returns:
            新的可见性状态 ('private' 或 'public')
        """
        resource = db_session.get(Resource, resource_id)
        if not resource:
            raise ValueError('资源文件不存在')

        # 权限检查：只有所有者可以修改可见性
        if resource.uploader_id != user_id:
            raise PermissionError('无权修改此文件')

        # 切换可见性
        new_visibility = 'public' if resource.visibility == 'private' else 'private'
        resource.visibility = new_visibility
        db_session.commit()

        return new_visibility

    @staticmethod
    def get_user_media(
        user_id: int,
        db_session: Session,
        page: int = 1,
        page_size: int = 20,
        visibility: Optional[str] = None,
        media_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户媒体文件列表（支持按可见性筛选）

        Args:
            user_id: 用户ID
            db_session: 数据库会话
            page: 页码
            page_size: 每页数量
            visibility: 可见性筛选 ('private', 'public', None表示全部)
            media_type: 媒体类型筛选 ('image', 'video', None表示全部)

        Returns:
            媒体列表和分页信息
        """
        # 构建查询
        stmt = select(Media).where(Media.uploader_id == user_id)

        # 可见性筛选
        if visibility in ['private', 'public']:
            stmt = stmt.where(Media.visibility == visibility)

        # 类型筛选
        if media_type in ['image', 'video']:
            stmt = stmt.where(Media.file_type == media_type)

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db_session.execute(count_stmt).scalar()

        # 分页查询
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Media.created_at.desc()).offset(offset).limit(page_size)
        media_list = list(db_session.execute(stmt).scalars())

        return {
            'items': media_list,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }

    @staticmethod
    def get_user_resources(
        user_id: int,
        db_session: Session,
        page: int = 1,
        page_size: int = 20,
        visibility: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户资源文件列表（支持按可见性筛选）

        Args:
            user_id: 用户ID
            db_session: 数据库会话
            page: 页码
            page_size: 每页数量
            visibility: 可见性筛选 ('private', 'public', None表示全部)

        Returns:
            资源列表和分页信息
        """
        # 构建查询
        stmt = select(Resource).where(Resource.uploader_id == user_id)

        # 可见性筛选
        if visibility in ['private', 'public']:
            stmt = stmt.where(Resource.visibility == visibility)

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db_session.execute(count_stmt).scalar()

        # 分页查询
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Resource.created_at.desc()).offset(offset).limit(page_size)
        resource_list = list(db_session.execute(stmt).scalars())

        return {
            'items': resource_list,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }

    @staticmethod
    def get_published_media(
        db_session: Session,
        page: int = 1,
        page_size: int = 20,
        media_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取公共媒体文件列表（供公共大厅使用）

        Args:
            db_session: 数据库会话
            page: 页码
            page_size: 每页数量
            media_type: 媒体类型筛选

        Returns:
            媒体列表和分页信息
        """
        # 构建查询：只返回公共文件，预加载上传者信息
        stmt = select(Media).where(Media.visibility == 'public').options(selectinload(Media.uploader))

        # 类型筛选
        if media_type in ['image', 'video']:
            stmt = stmt.where(Media.file_type == media_type)

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db_session.execute(count_stmt).scalar()

        # 分页查询
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Media.created_at.desc()).offset(offset).limit(page_size)
        media_list = list(db_session.execute(stmt).scalars())

        return {
            'items': media_list,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }

    @staticmethod
    def get_published_resources(
        db_session: Session,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取公共资源文件列表（供公共大厅使用）

        Args:
            db_session: 数据库会话
            page: 页码
            page_size: 每页数量

        Returns:
            资源列表和分页信息
        """
        # 构建查询：只返回公共文件，预加载上传者信息
        stmt = select(Resource).where(Resource.visibility == 'public').options(selectinload(Resource.uploader))

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db_session.execute(count_stmt).scalar()

        # 分页查询
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Resource.created_at.desc()).offset(offset).limit(page_size)
        resource_list = list(db_session.execute(stmt).scalars())

        return {
            'items': resource_list,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }
