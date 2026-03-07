"""
权限验证装饰器
学习要点：装饰器、权限控制、会话管理
"""
from functools import wraps
from flask import session, jsonify, g
from app import get_db_connection


def login_required(f):
    """
    登录验证装饰器
    保护需要登录才能访问的API
    使用方法：@login_required
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

        # 检查是否是管理员
        g.is_admin = is_admin_user(user_id)

        return f(*args, **kwargs)

    return decorated_function


def is_admin_user(user_id):
    """
    检查用户是否是管理员
    管理员定义为用户名为 'admin' 的用户
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            return user and user.get('username') == 'admin'
    except Exception:
        return False


def can_delete_resource(user_id, resource_user_id):
    """
    检查用户是否可以删除资源
    管理员可以删除任何资源，普通用户只能删除自己的资源
    """
    return is_admin_user(user_id) or user_id == resource_user_id


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
        return {
            'id': user_id,
            'username': session.get('username'),
            'is_admin': is_admin_user(user_id)
        }
    return None
