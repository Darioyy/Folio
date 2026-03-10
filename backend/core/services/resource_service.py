"""
学习资源服务层 - 业务逻辑
"""

import os
import uuid
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from core.models.resource import Resource
from core.schemas.resource import ResourceCreate, ResourceUpdate
from core.utils.permissions import get_user_role
from core.utils.constants import Role


logger = logging.getLogger(__name__)


class ResourceService:
    """学习资源服务类"""

    @staticmethod
    def allowed_file(filename: str, allowed_extensions: set) -> bool:
        """
        检查文件类型是否允许

        Args:
            filename: 文件名
            allowed_extensions: 允许的扩展名集合

        Returns:
            是否允许
        """
        if "." not in filename:
            return False

        ext = filename.rsplit(".", 1)[1].lower()
        return ext in allowed_extensions

    @staticmethod
    def generate_unique_filename(filename: str) -> str:
        """
        生成唯一文件名

        Args:
            filename: 原始文件名

        Returns:
            唯一文件名
        """
        ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
        unique_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
        return unique_name

    @staticmethod
    def get_by_id(resource_id: int, session: Session) -> Optional[Resource]:
        """
        根据 ID 获取资源

        Args:
            resource_id: 资源ID
            db_session: 数据库会话

        Returns:
            资源对象或 None
        """
        return session.get(Resource, resource_id)

    @staticmethod
    def get_with_details(resource_id: int, session: Session) -> Optional[dict]:
        """
        根据 ID 获取资源详情（包含分类和上传者信息）

        Args:
            resource_id: 资源ID
            db_session: 数据库会话

        Returns:
            资源详情字典或 None
        """
        stmt = select(
            Resource.id,
            Resource.title,
            Resource.description,
            Resource.file_path,
            Resource.file_name,
            Resource.file_size,
            Resource.file_type,
            Resource.category_id,
            Resource.uploader_id,
            Resource.download_count,
            Resource.created_at,
        ).where(Resource.id == resource_id)

        result = session.execute(stmt).first()

        if not result:
            return None

        # 转换为字典
        resource_dict = {
            "id": result[0],
            "title": result[1],
            "description": result[2],
            "file_path": result[3],
            "file_name": result[4],
            "file_size": result[5],
            "file_type": result[6],
            "category_id": result[7],
            "uploader_id": result[8],
            "download_count": result[9],
            "created_at": result[10].isoformat() if result[10] else None,
        }

        # 获取分类名称（通过原生SQL查询）
        try:
            from sqlalchemy import text

            category_stmt = text("SELECT name FROM categories WHERE id = :cid")
            category_result = session.execute(
                category_stmt, {"cid": result[7]}
            ).first()
            resource_dict["category_name"] = (
                category_result[0] if category_result else None
            )
        except Exception:
            resource_dict["category_name"] = None

        # 获取上传者名称
        try:
            from core.models.user import User

            uploader = session.get(User, result[8])
            resource_dict["uploader_name"] = uploader.username if uploader else None
        except Exception:
            resource_dict["uploader_name"] = None

        return resource_dict

    @staticmethod
    def create(
        resource_data: ResourceCreate,
        file_path: str,
        file_name: str,
        file_size: int,
        file_type: str,
        uploader_id: int,
        session: Session,
    ) -> Resource:
        """
        创建资源记录

        Args:
            resource_data: 资源数据
            file_path: 文件路径（相对）
            file_name: 原始文件名
            file_size: 文件大小
            file_type: 文件MIME类型
            uploader_id: 上传者ID
            db_session: 数据库会话

        Returns:
            创建的资源对象
        """
        resource = Resource(
            title=resource_data.title,
            description=resource_data.description,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            category_id=resource_data.category_id,
            uploader_id=uploader_id,
            download_count=0,
        )

        session.add(resource)
        session.commit()
        session.refresh(resource)

        return resource

    @staticmethod
    def update(
        resource_id: int,
        resource_data: ResourceUpdate,
        operator_id: int,
        session: Session,
    ) -> Resource:
        """
        更新资源信息

        Args:
            resource_id: 资源ID
            resource_data: 更新数据
            operator_id: 操作者ID
            db_session: 数据库会话

        Returns:
            更新后的资源对象
        """
        resource = ResourceService.get_by_id(resource_id, session)
        if not resource:
            raise ValueError("资源不存在")

        # 权限检查：只有管理员或上传者可以修改
        operator_role = get_user_role(operator_id, session)
        if operator_role < Role.ADMIN and resource.uploader_id != operator_id:
            raise PermissionError("无权修改此资源")

        # 更新字段
        if resource_data.title is not None:
            resource.title = resource_data.title
        if resource_data.description is not None:
            resource.description = resource_data.description
        if resource_data.category_id is not None:
            resource.category_id = resource_data.category_id

        session.commit()
        session.refresh(resource)

        return resource

    @staticmethod
    def delete(
        resource_id: int, operator_id: int, session: Session, upload_folder: str
    ) -> bool:
        """
        删除资源

        Args:
            resource_id: 资源ID
            operator_id: 操作者ID
            db_session: 数据库会话
            upload_folder: 上传目录

        Returns:
            是否删除成功
        """
        resource = ResourceService.get_by_id(resource_id, session)
        if not resource:
            raise ValueError("资源不存在")

        # 权限检查：只有管理员或上传者可以删除
        operator_role = get_user_role(operator_id, session)
        if operator_role < Role.ADMIN and resource.uploader_id != operator_id:
            raise PermissionError("无权删除此资源")

        # 删除物理文件
        file_path = os.path.join(upload_folder, resource.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"已删除文件: {file_path}")

        # 删除数据库记录
        session.delete(resource)
        session.commit()

        return True

    @staticmethod
    def increment_download(resource_id: int, session: Session) -> bool:
        """
        增加下载计数

        Args:
            resource_id: 资源ID
            db_session: 数据库会话

        Returns:
            是否成功
        """
        resource = ResourceService.get_by_id(resource_id, session)
        if not resource:
            raise ValueError("资源不存在")

        resource.download_count = (resource.download_count or 0) + 1
        session.commit()

        return True

    @staticmethod
    def list_resources(
        page: int = 1,
        page_size: int = 10,
        category_id: Optional[int] = None,
        visibility: Optional[str] = None,
        uploader_id: Optional[int] = None,
        session: Session = None,
    ) -> dict:
        """
        获取资源列表（带分页）

        Args:
            page: 页码
            page_size: 每页数量
            category_id: 分类ID筛选
            visibility: 可见性筛选 ('private', 'public', None表示全部)
            uploader_id: 上传者ID筛选
            db_session: 数据库会话

        Returns:
            资源列表和分页信息
        """
        # 构建查询
        stmt = select(Resource)

        # 分类筛选
        if category_id is not None:
            stmt = stmt.where(Resource.category_id == category_id)

        # 可见性筛选
        if visibility in ['private', 'public']:
            stmt = stmt.where(Resource.visibility == visibility)

        # 上传者筛选
        if uploader_id is not None:
            stmt = stmt.where(Resource.uploader_id == uploader_id)

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = session.execute(count_stmt).scalar()

        # 分页查询
        offset = (page - 1) * page_size
        stmt = stmt.order_by(Resource.created_at.desc()).offset(offset).limit(page_size)
        resource_list = list(session.execute(stmt).scalars())

        # 获取关联的分类和用户名称
        from sqlalchemy import text

        category_ids = [r.category_id for r in resource_list if r.category_id]
        uploader_ids = [r.uploader_id for r in resource_list]

        # 批量获取分类名称
        category_names = {}
        if category_ids:
            try:
                category_stmt = text(
                    "SELECT id, name FROM categories WHERE id IN :cids"
                )
                # 使用 IN 子句的方式
                placeholders = ",".join([str(cid) for cid in set(category_ids)])
                category_stmt = text(
                    f"SELECT id, name FROM categories WHERE id IN ({placeholders})"
                )
                category_results = session.execute(category_stmt).fetchall()
                category_names = {r[0]: r[1] for r in category_results}
            except Exception:
                pass

        # 批量获取用户名称
        uploader_names = {}
        if uploader_ids:
            try:
                from core.models.user import User

                user_stmt = select(User.id, User.username).where(
                    User.id.in_(set(uploader_ids))
                )
                user_results = session.execute(user_stmt).fetchall()
                uploader_names = {r[0]: r[1] for r in user_results}
            except Exception:
                pass

        # 添加名称到结果
        for resource in resource_list:
            if resource.category_id:
                resource.category_name = category_names.get(resource.category_id)
            if resource.uploader_id:
                resource.uploader_name = uploader_names.get(resource.uploader_id)

        return {
            "items": resource_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }
