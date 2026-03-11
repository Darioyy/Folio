"""
统一文件服务层 - 业务逻辑
合并 MediaService + ResourceService 的 CRUD，以及 HubService 的文件相关方法
"""
import os
import uuid
import logging
from typing import Optional, List, Union

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func

from core.models.file import File
from core.schemas.file import FileCreate, FileUpdate
from core.utils.permissions import get_user_role
from core.utils.constants import Role


logger = logging.getLogger(__name__)


class FileService:
    """统一文件服务类"""

    # -----------------------------------------------------------------------
    # 文件上传工具方法
    # -----------------------------------------------------------------------

    @staticmethod
    def allowed_file(filename: str, allowed_extensions: set) -> bool:
        """检查文件扩展名是否在白名单中"""
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in allowed_extensions

    @staticmethod
    def generate_unique_filename(filename: str) -> str:
        """生成 UUID 唯一文件名，保留原始扩展名"""
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        return f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

    # -----------------------------------------------------------------------
    # 媒体处理工具方法（迁移自 MediaService）
    # -----------------------------------------------------------------------

    @staticmethod
    def generate_video_thumbnail(video_path: str, output_dir: str) -> Optional[str]:
        """从视频截取第一帧作为缩略图，返回缩略图绝对路径或 None"""
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"无法打开视频文件: {video_path}")
                return None

            ret, frame = cap.read()
            cap.release()

            if not ret or frame is None:
                logger.error(f"无法读取视频帧: {video_path}")
                return None

            thumbnail_filename = f"{uuid.uuid4().hex}_thumb.jpg"
            thumbnail_path = os.path.join(output_dir, thumbnail_filename)

            # 等比缩放到宽度 320px
            target_width = 320
            height, width = frame.shape[:2]
            if width > target_width:
                scale = target_width / width
                frame = cv2.resize(
                    frame,
                    (target_width, int(height * scale)),
                    interpolation=cv2.INTER_AREA
                )

            cv2.imwrite(thumbnail_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return thumbnail_path

        except Exception as e:
            logger.error(f"生成视频缩略图失败: {e}")
            return None

    @staticmethod
    def get_image_dimensions(file_path: str) -> tuple:
        """获取图片尺寸，返回 (width, height) 或 (None, None)"""
        try:
            import cv2
            img = cv2.imread(file_path)
            if img is not None:
                height, width = img.shape[:2]
                return width, height
        except Exception as e:
            logger.error(f"获取图片尺寸失败: {e}")
        return None, None

    @staticmethod
    def get_video_duration(video_path: str) -> Optional[int]:
        """获取视频时长（秒），失败返回 None"""
        try:
            import cv2
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

    # -----------------------------------------------------------------------
    # CRUD
    # -----------------------------------------------------------------------

    @staticmethod
    def get_by_id(file_id: int, session: Session) -> Optional[File]:
        """根据 ID 获取文件，不存在返回 None"""
        return session.get(File, file_id)

    @staticmethod
    def create(
        file_data: FileCreate,
        file_path: str,
        file_name: str,
        file_size: int,
        mime_type: Optional[str],
        user_id: int,
        session: Session,
        thumbnail_path: Optional[str] = None,
        duration: Optional[int] = None,
        group_id: Optional[int] = None,
    ) -> File:
        """
        创建文件记录

        Args:
            file_data: FileCreate 元数据（title, description, file_category, visibility）
            file_path: 文件相对存储路径
            file_name: 原始文件名
            file_size: 文件大小（字节）
            mime_type: MIME 类型
            user_id: 上传者 ID
            session: 数据库会话
            thumbnail_path: 缩略图相对路径（图片/视频专用）
            duration: 视频时长（秒）

        Returns:
            创建的 File 对象
        """
        file = File(
            user_id=user_id,
            title=file_data.title,
            description=file_data.description,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            file_category=file_data.file_category,
            visibility=file_data.visibility or 'private',
            thumbnail_path=thumbnail_path,
            duration=duration,
            group_id=group_id,
        )
        session.add(file)
        session.commit()
        session.refresh(file)
        return file

    @staticmethod
    def update(
        file_id: int,
        file_data: FileUpdate,
        operator_id: int,
        session: Session,
    ) -> File:
        """
        更新文件信息（含权限检查）

        权限：管理员可修改任意文件；普通用户只能修改自己的文件。

        Returns:
            更新后的 File 对象

        Raises:
            ValueError: 文件不存在
            PermissionError: 无权操作
        """
        file = FileService.get_by_id(file_id, session)
        if not file:
            raise ValueError('文件不存在')

        operator_role = get_user_role(operator_id, session)
        if operator_role < Role.ADMIN and file.user_id != operator_id:
            raise PermissionError('无权修改此文件')

        if file_data.title is not None:
            file.title = file_data.title
        if file_data.description is not None:
            file.description = file_data.description
        if file_data.visibility is not None:
            file.visibility = file_data.visibility

        session.commit()
        session.refresh(file)
        return file

    @staticmethod
    def delete(
        file_id: int,
        operator_id: int,
        session: Session,
        upload_folder: str,
    ) -> bool:
        """
        删除文件（含物理文件和缩略图删除、权限检查）

        Returns:
            True

        Raises:
            ValueError: 文件不存在
            PermissionError: 无权操作
        """
        file = FileService.get_by_id(file_id, session)
        if not file:
            raise ValueError('文件不存在')

        operator_role = get_user_role(operator_id, session)
        if operator_role < Role.ADMIN and file.user_id != operator_id:
            raise PermissionError('无权删除此文件')

        # 删除物理文件
        physical_path = os.path.join(upload_folder, file.file_path)
        if os.path.exists(physical_path):
            os.remove(physical_path)
            logger.info(f"已删除文件: {physical_path}")

        # 删除缩略图
        if file.thumbnail_path:
            thumb_physical = os.path.join(upload_folder, file.thumbnail_path)
            if os.path.exists(thumb_physical):
                os.remove(thumb_physical)
                logger.info(f"已删除缩略图: {thumb_physical}")

        session.delete(file)
        session.commit()
        return True

    @staticmethod
    def toggle_visibility(file_id: int, user_id: int, session: Session) -> str:
        """
        切换文件可见性（仅文件所有者可操作）

        Returns:
            新的可见性字符串 ('private' 或 'public')

        Raises:
            ValueError: 文件不存在
            PermissionError: 非文件所有者
        """
        file = FileService.get_by_id(file_id, session)
        if not file:
            raise ValueError('文件不存在')

        if file.user_id != user_id:
            raise PermissionError('无权修改此文件')

        new_visibility = 'public' if file.visibility == 'private' else 'private'
        file.visibility = new_visibility
        session.commit()
        return new_visibility

    @staticmethod
    def list_files(
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[int] = None,
        file_category: Optional[Union[str, List[str]]] = None,
        visibility: Optional[str] = None,
        group_id: Optional[int] = None,
        session: Session = None,
        include_user: bool = False,
        viewer_id: Optional[int] = None,
        bypass_privacy: bool = False,
    ) -> dict:
        """
        统一文件列表查询

        Args:
            page: 页码（从 1 开始）
            page_size: 每页数量
            user_id: 按上传者筛选，None 表示全部
            file_category: 按分类筛选，支持单个字符串或字符串列表
            visibility: 按可见性筛选 ('private'/'public'，None 表示全部）；仅在有权限时生效
            session: 数据库会话
            include_user: 是否预加载 user 关系（公共列表传 True）
            viewer_id: 当前请求者 ID；只有 viewer_id == user_id（所有者自查）时才允许
                       按 visibility 参数过滤；其余情况（含管理员）一律只返回公开文件
            bypass_privacy: True 时跳过隐私限制（专供 Root 使用），可查看全部文件

        Returns:
            {items, total, page, page_size, pages}
        """
        stmt = select(File)

        if include_user:
            stmt = stmt.options(selectinload(File.user))

        if user_id is not None:
            stmt = stmt.where(File.user_id == user_id)

        # group_id=-1 → 未分组（IS NULL）；正整数 → 指定分组
        if group_id is not None:
            if group_id == -1:
                stmt = stmt.where(File.group_id.is_(None))
            else:
                stmt = stmt.where(File.group_id == group_id)

        if file_category is not None:
            if isinstance(file_category, list):
                stmt = stmt.where(File.file_category.in_(file_category))
            else:
                stmt = stmt.where(File.file_category == file_category)

        # 隐私强制：
        # - bypass_privacy=True（Root）：尊重 visibility 过滤参数，可查看全部
        # - 文件所有者自查（viewer_id == user_id）：尊重 visibility 过滤参数
        # - 其余所有情况（含普通管理员）：只能看到公开文件
        is_owner_view = (
            viewer_id is not None
            and user_id is not None
            and viewer_id == user_id
        )
        if bypass_privacy or is_owner_view:
            if visibility in ('private', 'public'):
                stmt = stmt.where(File.visibility == visibility)
        else:
            stmt = stmt.where(File.visibility == 'public')

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = session.execute(count_stmt).scalar()

        offset = (page - 1) * page_size
        stmt = stmt.order_by(File.created_at.desc()).offset(offset).limit(page_size)
        file_list = list(session.execute(stmt).scalars())

        return {
            'items': file_list,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size,
        }

    @staticmethod
    def sort_files(user_id: int, ordered_ids: list, session: Session) -> bool:
        """批量更新文件排序顺序（按 ids 顺序赋 sort_order）"""
        for idx, file_id in enumerate(ordered_ids):
            file = session.get(File, file_id)
            if file and file.user_id == user_id:
                file.sort_order = idx
        session.commit()
        return True

    @staticmethod
    def get_storage_used(user_id: int, session: Session) -> int:
        """
        计算用户已用存储空间（字节），替代 HubService 中的双表 SUM 逻辑

        Returns:
            已用字节数（file_size 为 NULL 的记录计为 0）
        """
        result = session.execute(
            select(func.sum(File.file_size)).where(File.user_id == user_id)
        ).scalar()
        return result or 0
