"""
权限验证模块（完全重构版）
======================
特性：
- 统一的权限检查接口
- 向后兼容的权限字段处理（布尔值/整数）
- 详细的权限审计日志
- 装饰器支持
- 三级权限系统：ROOT(2) > ADMIN(1) > USER(0)
"""
from functools import wraps
from flask import session, jsonify, g
import logging
from database import get_db_connection

logger = logging.getLogger(__name__)

# ==================== 权限等级常量 ====================

class PermissionLevel:
    """权限等级常量"""
    USER = 0    # 普通用户
    ADMIN = 1   # 管理员
    ROOT = 2    # 超级用户


# ==================== 工具函数 ====================

def normalize_permission_value(value):
    """
    标准化权限字段值为整数
    处理布尔值和整数两种情况，确保兼容性

    Args:
        value: 布尔值(True/False)或整数(0/1)

    Returns:
        int: 0 或 1
    """
    if value is True:
        return 1
    if value is False:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def get_user_info(user_id: int) -> dict:
    """
    从数据库获取用户信息
    返回标准化的用户数据

    Args:
        user_id: 用户ID

    Returns:
        dict: 用户信息，包含标准化的is_admin和is_root字段
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, is_root, is_admin FROM users WHERE id = %s",
                    (user_id,)
                )
                user = cursor.fetchone()
                if user:
                    # 标准化权限字段为整数
                    user['is_root'] = normalize_permission_value(user.get('is_root', 0))
                    user['is_admin'] = normalize_permission_value(user.get('is_admin', 0))
                return user or {}
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return {}


def get_user_permission_level(user_id: int) -> tuple:
    """
    获取用户权限等级

    Args:
        user_id: 用户ID

    Returns:
        tuple: (is_root: int, is_admin: int, level: int)
    """
    user = get_user_info(user_id)
    if not user:
        return (0, 0, PermissionLevel.USER)

    is_root = user.get('is_root', 0)
    is_admin = user.get('is_admin', 0)

    # 计算权限等级
    if is_root:
        level = PermissionLevel.ROOT
    elif is_admin:
        level = PermissionLevel.ADMIN
    else:
        level = PermissionLevel.USER

    return (is_root, is_admin, level)


def check_permission(user_id: int, required_level: int, resource_owner_id: int = None) -> dict:
    """
    统一的权限检查函数

    Args:
        user_id: 当前用户ID
        required_level: 需要的权限等级 (PermissionLevel.USER/ADMIN/ROOT)
        resource_owner_id: 资源所有者ID（可选，用于检查资源所有权）

    Returns:
        dict: {'granted': bool, 'reason': str, 'level': int}
    """
    is_root, is_admin, level = get_user_permission_level(user_id)

    # 资源所有者检查
    if resource_owner_id is not None and user_id == resource_owner_id:
        return {
            'granted': True,
            'reason': '资源所有者',
            'level': level
        }

    # 权限等级检查
    if level >= required_level:
        return {
            'granted': True,
            'reason': f'权限等级 {level} >= {required_level}',
            'level': level
        }

    return {
        'granted': False,
        'reason': f'权限不足，需要等级 {required_level}，当前等级 {level}',
        'level': level
    }


# ==================== 装饰器 ====================

def login_required(f):
    """
    登录验证装饰器
    保护需要登录才能访问的API

    使用方法：
        @user_bp.route('/protected')
        @login_required
        def protected_function():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查session中是否有user_id
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({
                'success': False,
                'error': '请先登录',
                'code': 'UNAUTHORIZED'
            }), 401

        # 将用户信息存储到g对象中，方便后续使用
        g.user_id = user_id
        g.username = session.get('username')

        # 缓存权限信息到g对象
        is_root, is_admin, level = get_user_permission_level(user_id)
        g.is_root = bool(is_root)
        g.is_admin = bool(is_admin)
        g.permission_level = level

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    管理员权限验证装饰器
    需要管理员或root权限才能访问
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': '请先登录',
                'code': 'UNAUTHORIZED'
            }), 401

        result = check_permission(user_id, PermissionLevel.ADMIN)
        if not result['granted']:
            logger.warning(f"用户 {user_id} 尝试访问管理员资源被拒绝: {result['reason']}")
            return jsonify({
                'success': False,
                'error': '需要管理员权限',
                'code': 'FORBIDDEN'
            }), 403

        # 设置g对象
        g.user_id = user_id
        g.username = session.get('username')
        g.is_admin = True
        g.is_root = result['level'] == PermissionLevel.ROOT

        return f(*args, **kwargs)

    return decorated_function


def root_required(f):
    """
    超级用户权限验证装饰器
    需要root权限才能访问
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': '请先登录',
                'code': 'UNAUTHORIZED'
            }), 401

        result = check_permission(user_id, PermissionLevel.ROOT)
        if not result['granted']:
            logger.warning(f"用户 {user_id} 尝试访问ROOT资源被拒绝: {result['reason']}")
            return jsonify({
                'success': False,
                'error': '需要超级用户权限',
                'code': 'FORBIDDEN'
            }), 403

        # 设置g对象
        g.user_id = user_id
        g.username = session.get('username')
        g.is_root = True
        g.is_admin = True

        return f(*args, **kwargs)

    return decorated_function


# ==================== 兼容性函数（供旧代码调用） ====================

def is_root_user(user_id) -> bool:
    """
    检查用户是否是超级用户(root)
    兼容旧代码的函数调用

    Args:
        user_id: 用户ID

    Returns:
        bool: 是否是root用户
    """
    if not user_id:
        return False
    is_root, _, _ = get_user_permission_level(user_id)
    return bool(is_root)


def is_admin_user(user_id) -> bool:
    """
    检查用户是否是管理员
    root 或 admin 都返回 True
    兼容旧代码的函数调用

    Args:
        user_id: 用户ID

    Returns:
        bool: 是否是管理员或root
    """
    if not user_id:
        return False
    is_root, is_admin, _ = get_user_permission_level(user_id)
    return bool(is_root or is_admin)


def can_modify_admin(target_user_id) -> bool:
    """
    检查当前用户是否有权限修改管理员权限
    - root 可以修改任何人的管理员权限（包括其他root）
    - admin 可以修改普通用户的管理员权限
    - admin 不能修改 root 的管理员权限
    - 不能取消自己的管理员权限

    Args:
        target_user_id: 目标用户ID

    Returns:
        bool: 是否可以修改
    """
    current_user_id = g.get('user_id')
    if not current_user_id:
        logger.warning(f"[can_modify_admin] 当前用户ID为空")
        return False

    current_is_root, _, current_level = get_user_permission_level(current_user_id)
    target_is_root, _, target_level = get_user_permission_level(target_user_id)

    logger.info(f"[can_modify_admin] 当前用户ID: {current_user_id}, is_root: {current_is_root}, level: {current_level}")
    logger.info(f"[can_modify_admin] 目标用户ID: {target_user_id}, is_root: {target_is_root}, level: {target_level}")

    # root 可以修改任何人（包括其他root）
    if current_is_root:
        logger.info(f"[can_modify_admin] 当前用户是root，允许修改")
        return True

    # admin 不能修改 root
    if target_is_root:
        logger.warning(f"[can_modify_admin] 目标用户是root，当前用户不是root，拒绝修改")
        return False

    # admin 可以修改普通用户
    if current_level >= PermissionLevel.ADMIN and target_level == PermissionLevel.USER:
        logger.info(f"[can_modify_admin] 当前用户是admin，目标用户是普通用户，允许修改")
        return True

    logger.warning(f"[can_modify_admin] 权限不足，拒绝修改")
    return False


def can_modify_root(target_user_id) -> bool:
    """
    检查当前用户是否有权限修改 root 用户
    root 不能被修改，除了 root 自己可以修改自己的非敏感信息

    Args:
        target_user_id: 目标用户ID

    Returns:
        bool: 是否可以修改
    """
    current_user_id = g.get('user_id')
    if not current_user_id:
        return False

    # 不能修改其他 root 的信息
    if target_user_id != current_user_id:
        target_is_root, _, _ = get_user_permission_level(target_user_id)
        if target_is_root:
            return False

    current_is_root, _, _ = get_user_permission_level(current_user_id)
    return bool(current_is_root)


def can_delete_user(target_user_id) -> bool:
    """
    检查是否可以删除用户
    - root 可以删除任何人（除了自己）
    - admin 可以删除普通用户（不能删除 admin 和 root）

    Args:
        target_user_id: 目标用户ID

    Returns:
        bool: 是否可以删除
    """
    current_user_id = g.get('user_id')
    if not current_user_id:
        return False

    # 不能删除自己
    if current_user_id == target_user_id:
        return False

    current_is_root, _, current_level = get_user_permission_level(current_user_id)
    target_is_root, target_is_admin, target_level = get_user_permission_level(target_user_id)

    # root 可以删除任何人（除了自己）
    if current_is_root:
        return True

    # admin 只能删除普通用户
    if current_level >= PermissionLevel.ADMIN and target_level == PermissionLevel.USER:
        return True

    return False


def can_delete_resource(user_id, resource_user_id) -> bool:
    """
    检查用户是否可以删除资源
    root/admin 可以删除任何资源，普通用户只能删除自己的资源

    Args:
        user_id: 当前用户ID
        resource_user_id: 资源所有者ID

    Returns:
        bool: 是否可以删除
    """
    if not user_id:
        return False

    result = check_permission(user_id, PermissionLevel.ADMIN, resource_user_id)
    return result['granted']


def get_current_user_id():
    """
    获取当前登录用户ID
    返回：用户ID或None
    """
    return session.get('user_id')


def get_current_user():
    """
    获取当前登录用户信息
    返回：用户信息字典或None
    """
    user_id = session.get('user_id')
    if user_id:
        user = get_user_info(user_id)
        if user:
            return {
                'id': user['id'],
                'username': user.get('username'),
                'is_admin': bool(user.get('is_admin', 0)),
                'is_root': bool(user.get('is_root', 0)),
                'permission_level': get_user_permission_level(user_id)[2]
            }
    return None
