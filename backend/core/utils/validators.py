"""
自定义验证器
"""
from functools import wraps
from flask import jsonify, g
from db.session import db as db_session


def login_required(f):
    """
    登录验证装饰器

    Usage:
        @login_required
        def some_endpoint():
            # 可以通过 g.user_id 获取当前用户ID
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session

        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': '请先登录'
                }
            }), 401

        g.user_id = session['user_id']
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    管理员权限验证装饰器

    Usage:
        @admin_required
        def admin_endpoint():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session
        from core.utils.permissions import require_admin

        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': '请先登录'
                }
            }), 401

        user_id = session['user_id']

        if not require_admin(user_id, db_session.session):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': '需要管理员权限'
                }
            }), 403

        g.user_id = user_id
        return f(*args, **kwargs)

    return decorated_function


def root_required(f):
    """
    超级管理员权限验证装饰器

    Usage:
        @root_required
        def root_endpoint():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session
        from core.utils.permissions import require_root

        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': '请先登录'
                }
            }), 401

        user_id = session['user_id']

        if not require_root(user_id, db_session.session):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': '需要超级管理员权限'
                }
            }), 403

        g.user_id = user_id
        return f(*args, **kwargs)

    return decorated_function
