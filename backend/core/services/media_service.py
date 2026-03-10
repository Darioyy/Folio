"""
媒体服务层 - 业务逻辑
"""
import os
import uuid
import logging
import cv2
import numpy as np
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from core.models.media import Media
from core.schemas.media import MediaCreate, MediaUpdate
from core.utils.permissions import get_user_role
from core.utils.constants import Role


logger = logging.getLogger(__name__)


class MediaService:
    """媒体服务类"""

    @staticmethod
    def allowed_file(filename: str, file_type: str, allowed_extensions: dict) -> bool:
        """
        检查文件类型是否允许

        Args:
            filename: 文件名
            file_type: 文件类型 (image/video)
            allowed_extensions: 允许的扩展名字典

        Returns:
            是否允许
        """
        if '.' not in filename:
            return False

        ext = filename.rsplit('.', 1)[1].lower()

        if file_type == 'image':
            return ext in allowed_extensions.get('images', set())
        elif file_type == 'video':
            return ext in allowed_extensions.get('videos', set())

        return False

    @staticmethod
    def generate_video_thumbnail(video_path: str, output_dir: str) -> Optional[str]:
        """
        从视频文件中截取第一帧作为缩略图

        Args:
            video_path: 视频文件路径
            output_dir: 输出目录

        Returns:
            缩略图路径或 None
        """
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                logger.error(f"无法打开视频文件: {video_path}")
                return None

            ret, frame = cap.read()

            if not ret or frame is None:
                logger.error(f"无法读取视频帧: {video_path}")
                cap.release()
                return None

            cap.release()

            # 生成缩略图文件名
            thumbnail_filename = f"{uuid.uuid4().hex}_thumb.jpg"
            thumbnail_path = os.path.join(output_dir, thumbnail_filename)

            # 调整缩略图尺寸
            target_width = 320
            height, width = frame.shape[:2]
            if width > target_width:
                scale = target_width / width
                new_width = target_width
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

            # 保存缩略图
            cv2.imwrite(thumbnail_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

            return thumbnail_path

        except Exception as e:
            logger.error(f"生成视频缩略图失败: {e}")
            return None

    @staticmethod
    def get_image_dimensions(file_path: str) -> tuple:
        """
        获取图片尺寸

        Args:
            file_path: 图片文件路径

        Returns:
            (width, height) 或 (None, None)
        """
        try:
            img = cv2.imread(file_path)
            if img is not None:
                height, width = img.shape[:2]
                return width, height
        except Exception as e:
            logger.error(f"获取图片尺寸失败: {e}")
        return None, None

    @staticmethod
    def get_video_duration(video_path: str) -> Optional[int]:
        """
        获取视频时长

        Args:
            video_path: 视频文件路径

        Returns:
            时长（秒）或 None
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                duration = int(frame_count / fps) if fps > 0 else None
                cap.release()
                return duration
        except Exception as e:
            logger.error(f"获取视频时长失败: {e}")
        return None

    @staticmethod
    def get_by_id(media_id: int, session: Session) -> Optional[Media]:
        """
        根据 ID 获取媒体

        Args:
            media_id: 媒体ID
            db_session: 数据库会话

        Returns:
            媒体对象或 None
        """
        return session.get(Media, media_id)

    @staticmethod
    def create(
        media_data: MediaCreate,
        file_path: str,
        file_name: str,
        uploader_id: int,
        thumbnail_path: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[int] = None,
        file_size: Optional[int] = None,
        session: Session = None
    ) -> Media:
        """
        创建媒体记录

        Args:
            media_data: 媒体数据
            file_path: 文件路径（相对）
            file_name: 原始文件名
            uploader_id: 上传者ID
            thumbnail_path: 缩略图路径（相对）
            width: 宽度
            height: 高度
            duration: 视频时长
            file_size: 文件大小（字节）
            session: 数据库会话

        Returns:
            创建的媒体对象
        """
        media = Media(
            title=media_data.title,
            description=media_data.description,
            file_path=file_path,
            file_name=file_name,
            file_type=media_data.file_type,
            thumbnail_path=thumbnail_path,
            width=width,
            height=height,
            duration=duration,
            file_size=file_size,
            uploader_id=uploader_id
        )

        session.add(media)
        session.commit()
        session.refresh(media)

        return media

    @staticmethod
    def update(media_id: int, media_data: MediaUpdate, operator_id: int, session: Session) -> Media:
        """
        更新媒体信息

        Args:
            media_id: 媒体ID
            media_data: 更新数据
            operator_id: 操作者ID
            session: 数据库会话

        Returns:
            更新后的媒体对象
        """
        media = MediaService.get_by_id(media_id, session)
        if not media:
            raise ValueError('媒体不存在')

        # 权限检查：只有管理员或上传者可以修改
        operator_role = get_user_role(operator_id, session)
        if operator_role < Role.ADMIN and media.uploader_id != operator_id:
            raise PermissionError('无权修改此媒体')

        # 更新字段
        if media_data.title is not None:
            media.title = media_data.title
        if media_data.description is not None:
            media.description = media_data.description

        session.commit()
        session.refresh(media)

        return media

    @staticmethod
    def delete(media_id: int, operator_id: int, session: Session, upload_folder: str) -> bool:
        """
        删除媒体

        Args:
            media_id: 媒体ID
            operator_id: 操作者ID
            session: 数据库会话
            upload_folder: 上传目录

        Returns:
            是否删除成功
        """
        media = MediaService.get_by_id(media_id, session)
        if not media:
            raise ValueError('媒体不存在')

        # 权限检查：只有管理员或上传者可以删除
        operator_role = get_user_role(operator_id, session)
        if operator_role < Role.ADMIN and media.uploader_id != operator_id:
            raise PermissionError('无权删除此媒体')

        # 删除物理文件
        file_path = os.path.join(upload_folder, media.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"已删除文件: {file_path}")

        # 删除缩略图
        if media.thumbnail_path:
            thumbnail_path = os.path.join(upload_folder, media.thumbnail_path)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                logger.info(f"已删除缩略图: {thumbnail_path}")

        # 删除数据库记录
        session.delete(media)
        session.commit()

        return True

    @staticmethod
    def list_media(
        page: int = 1,
        page_size: int = 12,
        media_type: Optional[str] = None,
        visibility: Optional[str] = None,
        uploader_id: Optional[int] = None,
        session: Session = None
    ) -> dict:
        """
        获取媒体列表

        Args:
            page: 页码
            page_size: 每页数量
            media_type: 媒体类型筛选 (image/video)
            visibility: 可见性筛选 ('private', 'public', None表示全部)
            uploader_id: 上传者ID筛选
            session: 数据库会话

        Returns:
            媒体列表和分页信息
        """
        # 构建查询
        stmt = select(Media)

        # 类型筛选
        if media_type in ['image', 'video']:
            stmt = stmt.where(Media.file_type == media_type)

        # 可见性筛选
        if visibility in ['private', 'public']:
            stmt = stmt.where(Media.visibility == visibility)

        # 上传者筛选
        if uploader_id is not None:
            stmt = stmt.where(Media.uploader_id == uploader_id)

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = session.execute(count_stmt).scalar()

        # 分页查询
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Media.created_at.desc()).offset(offset).limit(page_size)
        media_list = list(session.execute(stmt).scalars())

        return {
            'items': media_list,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        }
