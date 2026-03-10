"""
权限检查工具函数
"""
from flask import g
from core.utils.constants import Role


def get_user_role(user_id: int, db_session) -> int:
    """
    获取用户角色等级

    Args:
        user_id: 用户ID
        db_session: 数据库会话

    Returns:
        用户角色等级
    """
    from core.models.user import User

    user = db_session.get(User, user_id)
    if not user:
        return Role.USER

    # 优先返回 ROOT 角色
    if user.is_root:
        return Role.ROOT
    # 其次返回 ADMIN 角色
    if user.is_admin:
        return Role.ADMIN
    return Role.USER


def can_modify_user(operator_id: int, target_id: int, db_session) -> bool:
    """
    判断操作者是否可以修改目标用户

    规则：
    - ROOT 可以修改任何人
    - ADMIN 不能修改 ROOT
    - 用户只能修改自己

    Args:
        operator_id: 操作者ID
        target_id: 目标用户ID
        db_session: 数据库会话

    Returns:
        是否有权限
    """
    from core.models.user import User

    operator = db_session.get(User, operator_id)
    target = db_session.get(User, target_id)

    if not operator or not target:
        return False

    # ROOT 可以修改任何人
    if operator.is_root:
        return True

    # ADMIN 不能修改 ROOT
    if target.is_root:
        return False

    # ADMIN 不能修改其他 ADMIN
    if operator.is_admin and target.is_admin:
        return False

    # 用户只能修改自己
    return operator_id == target_id


def can_delete_user(operator_id: int, target_id: int, db_session) -> bool:
    """
    判断操作者是否可以删除目标用户

    规则：
    - 不能删除自己
    - ROOT 可以删除任何人（除自己）
    - ADMIN 只能删除普通用户

    Args:
        operator_id: 操作者ID
        target_id: 目标用户ID
        db_session: 数据库会话

    Returns:
        是否有权限
    """
    from core.models.user import User

    # 不能删除自己
    if operator_id == target_id:
        return False

    operator = db_session.get(User, operator_id)
    target = db_session.get(User, target_id)

    if not operator or not target:
        return False

    # ROOT 可以删除任何人（除自己）
    if operator.is_root:
        return True

    # ADMIN 只能删除普通用户
    if operator.is_admin and not target.is_admin and not target.is_root:
        return True

    return False


def require_admin(user_id: int, db_session) -> bool:
    """
    检查用户是否是管理员

    Args:
        user_id: 用户ID
        db_session: 数据库会话

    Returns:
        是否是管理员
    """
    from core.models.user import User

    user = db_session.get(User, user_id)
    return user is not None and (user.is_admin or user.is_root)


def require_root(user_id: int, db_session) -> bool:
    """
    检查用户是否是超级管理员

    Args:
        user_id: 用户ID
        db_session: 数据库会话

    Returns:
        是否是超级管理员
    """
    from core.models.user import User

    user = db_session.get(User, user_id)
    return user is not None and user.is_root
