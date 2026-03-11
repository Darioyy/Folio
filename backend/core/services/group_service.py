"""
文件分组服务层 - 业务逻辑
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, delete, case

from core.models.file_group import FileGroup
from core.models.file import File


logger = logging.getLogger(__name__)

ROOT_LIMIT = 20  # 根目录最大分组数


class GroupService:
    """文件分组服务"""

    @staticmethod
    def get_root_groups(user_id: int, session: Session) -> list:
        """
        获取用户根分组列表（侧边栏，仅 parent_id=NULL）
        含各组直接文件数量和直接子文件夹数量。
        """
        stmt = (
            select(FileGroup)
            .where(FileGroup.user_id == user_id, FileGroup.parent_id.is_(None))
            .order_by(FileGroup.sort_order, FileGroup.created_at)
        )
        groups = list(session.execute(stmt).scalars())
        if not groups:
            return []

        group_ids = [g.id for g in groups]

        # 批量获取直接文件数（1 次查询）
        file_counts = dict(session.execute(
            select(File.group_id, func.count(File.id))
            .where(File.group_id.in_(group_ids))
            .group_by(File.group_id)
        ).all())

        # 批量获取直接子文件夹数（1 次查询）
        children_counts = dict(session.execute(
            select(FileGroup.parent_id, func.count(FileGroup.id))
            .where(FileGroup.parent_id.in_(group_ids), FileGroup.user_id == user_id)
            .group_by(FileGroup.parent_id)
        ).all())

        return [
            g.to_dict(
                file_count=file_counts.get(g.id, 0),
                children_count=children_counts.get(g.id, 0),
            )
            for g in groups
        ]

    @staticmethod
    def get_children(group_id: int, user_id: int, session: Session) -> list:
        """
        获取某分组的直接子文件夹（内容区用）

        Raises:
            ValueError: 分组不存在或无权访问
        """
        parent = session.get(FileGroup, group_id)
        if not parent or parent.user_id != user_id:
            raise ValueError('分组不存在')

        stmt = (
            select(FileGroup)
            .where(FileGroup.parent_id == group_id, FileGroup.user_id == user_id)
            .order_by(FileGroup.sort_order, FileGroup.created_at)
        )
        children = list(session.execute(stmt).scalars())
        if not children:
            return []

        child_ids = [g.id for g in children]

        # 批量获取直接文件数（1 次查询）
        file_counts = dict(session.execute(
            select(File.group_id, func.count(File.id))
            .where(File.group_id.in_(child_ids))
            .group_by(File.group_id)
        ).all())

        # 批量获取直接子文件夹数（1 次查询）
        children_counts = dict(session.execute(
            select(FileGroup.parent_id, func.count(FileGroup.id))
            .where(FileGroup.parent_id.in_(child_ids), FileGroup.user_id == user_id)
            .group_by(FileGroup.parent_id)
        ).all())

        return [
            g.to_dict(
                file_count=file_counts.get(g.id, 0),
                children_count=children_counts.get(g.id, 0),
            )
            for g in children
        ]

    @staticmethod
    def get_breadcrumb(group_id: int, user_id: int, session: Session) -> list:
        """
        从当前分组向上遍历到根，返回路径列表（根→当前）

        Returns:
            [{'id': 1, 'name': '设计'}, {'id': 5, 'name': 'UI设计'}, ...]
        """
        # 一次性获取用户所有分组，在 Python 中完成路径遍历（1 次查询替代 N 次）
        all_groups = {
            g.id: g
            for g in session.execute(
                select(FileGroup).where(FileGroup.user_id == user_id)
            ).scalars()
        }

        result = []
        current_id = group_id
        visited = set()

        while current_id is not None:
            if current_id in visited:
                break
            visited.add(current_id)
            group = all_groups.get(current_id)
            if not group:
                break
            result.append({'id': group.id, 'name': group.name})
            current_id = group.parent_id

        result.reverse()  # 根在前
        return result

    @staticmethod
    def create(user_id: int, name: str, session: Session, parent_id: Optional[int] = None) -> FileGroup:
        """
        创建分组。根目录（parent_id=None）最多 ROOT_LIMIT 个。

        Raises:
            ValueError: 名称无效 / 超出根目录限制 / 父分组不存在或无权
        """
        name = name.strip()
        if not name:
            raise ValueError('分组名不能为空')
        if len(name) > 100:
            raise ValueError('分组名不能超过100字符')

        if parent_id is None:
            root_count = session.execute(
                select(func.count()).select_from(FileGroup)
                .where(FileGroup.user_id == user_id, FileGroup.parent_id.is_(None))
            ).scalar() or 0
            if root_count >= ROOT_LIMIT:
                raise ValueError(f'根目录最多 {ROOT_LIMIT} 个分组，请整理后再新建')
        else:
            parent = session.get(FileGroup, parent_id)
            if not parent or parent.user_id != user_id:
                raise ValueError('父分组不存在')

        group = FileGroup(user_id=user_id, name=name, parent_id=parent_id)
        session.add(group)
        session.commit()
        session.refresh(group)
        return group

    @staticmethod
    def rename(group_id: int, user_id: int, name: str, session: Session) -> FileGroup:
        """
        重命名分组

        Raises:
            ValueError: 分组不存在或名称无效
            PermissionError: 非分组所有者
        """
        group = session.get(FileGroup, group_id)
        if not group:
            raise ValueError('分组不存在')
        if group.user_id != user_id:
            raise PermissionError('无权修改此分组')

        name = name.strip()
        if not name:
            raise ValueError('分组名不能为空')

        group.name = name
        session.commit()
        session.refresh(group)
        return group

    @staticmethod
    def delete(group_id: int, user_id: int, session: Session, force: bool = False) -> bool:
        """
        删除分组：
        - force=False（默认）：直接文件解除关联（group_id=NULL），子分组上移
        - force=True：递归删除所有子分组和文件记录（物理文件不删，仅数据库记录）

        Raises:
            ValueError: 分组不存在
            PermissionError: 非分组所有者
        """
        group = session.get(FileGroup, group_id)
        if not group:
            raise ValueError('分组不存在')
        if group.user_id != user_id:
            raise PermissionError('无权删除此分组')

        if force:
            GroupService._delete_recursive(group_id, user_id, session)
        else:
            parent_id = group.parent_id
            # 将文件移出分组
            session.execute(
                update(File).where(File.group_id == group_id).values(group_id=None)
            )
            # 将直接子分组上移一级
            session.execute(
                update(FileGroup)
                .where(FileGroup.parent_id == group_id, FileGroup.user_id == user_id)
                .values(parent_id=parent_id)
            )
            session.delete(group)

        session.commit()
        return True

    @staticmethod
    def _delete_recursive(group_id: int, user_id: int, session: Session) -> None:
        """BFS 收集完整子树 ID，然后批量删除文件记录和分组（不删物理文件）"""
        # BFS 逐层收集所有后代分组 ID
        levels = [[group_id]]
        all_group_ids = [group_id]
        while True:
            current_level = levels[-1]
            children = list(session.execute(
                select(FileGroup.id).where(
                    FileGroup.parent_id.in_(current_level),
                    FileGroup.user_id == user_id,
                )
            ).scalars())
            if not children:
                break
            levels.append(children)
            all_group_ids.extend(children)

        # 批量删除所有分组中的文件记录
        session.execute(
            delete(File).where(File.group_id.in_(all_group_ids), File.user_id == user_id)
        )

        # 逆序逐级删除分组（叶→根），避免 FK 约束冲突
        for level in reversed(levels):
            session.execute(
                delete(FileGroup).where(
                    FileGroup.id.in_(level),
                    FileGroup.user_id == user_id,
                )
            )

    @staticmethod
    def sort_root(user_id: int, ordered_ids: list, session: Session) -> bool:
        """
        更新根分组排序顺序（侧边栏拖拽后调用）

        Args:
            ordered_ids: 排序后的根分组 ID 列表（从上到下）
        """
        if not ordered_ids:
            return True
        # 单次 bulk UPDATE，用 CASE WHEN 替代 N 次逐行写入
        session.execute(
            update(FileGroup)
            .where(
                FileGroup.user_id == user_id,
                FileGroup.parent_id.is_(None),
                FileGroup.id.in_(ordered_ids),
            )
            .values(sort_order=case(
                *[(FileGroup.id == gid, idx) for idx, gid in enumerate(ordered_ids)]
            ))
        )
        session.commit()
        return True

    @staticmethod
    def move(group_id: int, user_id: int, new_parent_id: Optional[int], session: Session) -> FileGroup:
        """
        移动分组到新父级（new_parent_id=None 表示移到根目录）

        Raises:
            ValueError: 分组不存在/目标不存在/循环引用
            PermissionError: 非分组所有者
        """
        group = session.get(FileGroup, group_id)
        if not group:
            raise ValueError('分组不存在')
        if group.user_id != user_id:
            raise PermissionError('无权移动此分组')

        if new_parent_id is not None:
            parent = session.get(FileGroup, new_parent_id)
            if not parent or parent.user_id != user_id:
                raise ValueError('目标分组不存在')
            # 防止移动到自身或子孙节点（循环引用检查）
            cur = parent
            while cur is not None:
                if cur.id == group_id:
                    raise ValueError('不能将文件夹移动到其子文件夹中')
                if cur.parent_id is None:
                    break
                cur = session.get(FileGroup, cur.parent_id)

        group.parent_id = new_parent_id
        session.commit()
        session.refresh(group)
        return group

    @staticmethod
    def assign_file_group(
        file_id: int,
        group_id: Optional[int],
        user_id: int,
        session: Session,
    ) -> bool:
        """
        修改文件所属分组（group_id=None 表示移出分组到未分组）

        Raises:
            ValueError: 文件或分组不存在
            PermissionError: 无权操作
        """
        file = session.get(File, file_id)
        if not file:
            raise ValueError('文件不存在')
        if file.user_id != user_id:
            raise PermissionError('无权修改此文件')

        if group_id is not None:
            group = session.get(FileGroup, group_id)
            if not group:
                raise ValueError('分组不存在')
            if group.user_id != user_id:
                raise PermissionError('无权使用此分组')

        file.group_id = group_id
        session.commit()
        return True
