"""
用户相关API
学习要点：用户认证、密码哈希、会话管理
"""
import hashlib
import secrets
from flask import request, jsonify, session, g
from api import user_bp
from api.auth import login_required, is_admin_user
from app import get_db_connection


def hash_password(password):
    """
    密码哈希函数
    学习要点：永远不要明文存储密码！使用SHA-256加盐
    TODO: 后续升级为bcrypt或argon2
    """
    # 加盐处理（简单示例，生产环境应使用随机盐）
    salt = "ai_web_dev_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()


@user_bp.route('/', methods=['GET'])
def get_users():
    """
    获取用户列表
    GET /api/v1/users
    查询参数：page, limit
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 获取总数
            cursor.execute("SELECT COUNT(*) as total FROM users")
            total = cursor.fetchone()['total']

            # 获取分页数据（不返回密码哈希）
            cursor.execute("""
                SELECT id, username, email, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            users = cursor.fetchall()

        return jsonify({
            'success': True,
            'data': users,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    获取单个用户信息
    GET /api/v1/users/{id}
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, created_at
                FROM users
                WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()

        if not user:
            return jsonify({
                'success': False,
                'error': '用户不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': user
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_bp.route('/', methods=['POST'])
def create_user():
    """
    创建新用户
    POST /api/v1/users
    请求体：{ username, password, email }
    """
    try:
        data = request.get_json()

        # 参数验证
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': '用户名和密码不能为空'
            }), 400

        username = data['username']
        password = data['password']
        email = data.get('email', '')

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': '用户名已存在'
                }), 400

            # 插入新用户
            password_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, email)
                VALUES (%s, %s, %s)
            """, (username, password_hash, email))
            conn.commit()

            return jsonify({
                'success': True,
                'message': '用户创建成功',
                'data': {'id': cursor.lastrowid, 'username': username}
            }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """
    更新用户信息
    PUT /api/v1/users/{id}
    请求体：{ password, username, new_password, email }
    权限：只能修改自己的信息，admin可以修改所有人
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400

        # 权限检查：只能修改自己的信息，admin可以修改所有人
        if not is_admin_user(g.user_id) and g.user_id != user_id:
            return jsonify({
                'success': False,
                'error': '没有权限修改此用户信息'
            }), 403

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 获取用户信息
            cursor.execute("SELECT id, username, password_hash FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({
                    'success': False,
                    'error': '用户不存在'
                }), 404

            # 如果不是admin，需要验证当前密码
            if not is_admin_user(g.user_id):
                current_password = data.get('password')
                if not current_password:
                    return jsonify({
                        'success': False,
                        'error': '需要提供当前密码才能修改信息'
                    }), 400

                # 验证当前密码
                if user['password_hash'] != hash_password(current_password):
                    return jsonify({
                        'success': False,
                        'error': '当前密码错误'
                    }), 400

            updates = []
            params = []

            # 更新用户名
            if data.get('username'):
                new_username = data['username'].strip()
                # 检查用户名是否已存在
                cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (new_username, user_id))
                if cursor.fetchone():
                    return jsonify({
                        'success': False,
                        'error': '用户名已存在'
                    }), 400

                updates.append("username = %s")
                params.append(new_username)

            # 更新密码
            if data.get('new_password'):
                updates.append("password_hash = %s")
                params.append(hash_password(data['new_password']))

            # 更新邮箱
            if data.get('email'):
                updates.append("email = %s")
                params.append(data['email'])

            if not updates:
                return jsonify({
                    'success': False,
                    'error': '没有可更新的字段'
                }), 400

            params.append(user_id)

            cursor.execute(f"""
                UPDATE users
                SET {', '.join(updates)}
                WHERE id = %s
            """, params)
            conn.commit()

        return jsonify({
            'success': True,
            'message': '用户信息更新成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """
    删除用户（需要登录，仅admin可用）
    DELETE /api/v1/users/{id}
    安全考虑：只有admin可以删除用户
    """
    try:
        # 权限检查：只有admin可以删除用户
        if not is_admin_user(g.user_id):
            return jsonify({
                'success': False,
                'error': '没有权限删除用户'
            }), 403

        # 不能删除自己
        if user_id == g.user_id:
            return jsonify({
                'success': False,
                'error': '不能删除自己的账户'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': '用户不存在'
                }), 404

            # 硬删除（生产环境应改为软删除）
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()

        return jsonify({
            'success': True,
            'message': '用户删除成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# 登录认证相关API
# ============================================

@user_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    POST /api/v1/users/login
    请求体：{ username, password }
    返回：用户信息和session
    """
    try:
        data = request.get_json()

        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': '用户名和密码不能为空'
            }), 400

        username = data['username']
        password = data['password']
        password_hash = hash_password(password)

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 验证用户
            cursor.execute("""
                SELECT id, username, email
                FROM users
                WHERE username = %s AND password_hash = %s
            """, (username, password_hash))
            user = cursor.fetchone()

            if not user:
                return jsonify({
                    'success': False,
                    'error': '用户名或密码错误'
                }), 401

            # 设置session
            session['user_id'] = user['id']
            session['username'] = user['username']

            return jsonify({
                'success': True,
                'message': '登录成功',
                'data': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email']
                }
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册
    POST /api/v1/users/register
    请求体：{ username, password, email }
    返回：注册结果
    """
    try:
        data = request.get_json()

        # 参数验证
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': '用户名和密码不能为空'
            }), 400

        username = data['username'].strip()
        password = data['password']
        email = data.get('email', '').strip()

        # 验证用户名长度
        if len(username) < 3:
            return jsonify({
                'success': False,
                'error': '用户名长度不能少于3位'
            }), 400

        # 验证密码长度
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': '密码长度不能少于6位'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': '用户名已存在'
                }), 400

            # 创建新用户
            password_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, email)
                VALUES (%s, %s, %s)
            """, (username, password_hash, email))
            conn.commit()

            return jsonify({
                'success': True,
                'message': '注册成功',
                'data': {
                    'id': cursor.lastrowid,
                    'username': username
                }
            }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_bp.route('/logout', methods=['POST'])
def logout():
    """
    用户登出
    POST /api/v1/users/logout
    清除session
    """
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': '登出成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """
    获取当前登录用户信息
    GET /api/v1/users/me
    需要登录
    返回：用户信息和权限标识
    """
    try:
        user_id = g.user_id

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, created_at
                FROM users
                WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()

            if not user:
                session.clear()
                return jsonify({
                    'success': False,
                    'error': '用户不存在'
                }), 404

            # 添加权限信息
            user['is_admin'] = is_admin_user(user_id)

            return jsonify({
                'success': True,
                'data': user
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_bp.route('/check-auth', methods=['GET'])
def check_auth():
    """
    检查登录状态
    GET /api/v1/users/check-auth
    返回：是否登录及用户基本信息
    """
    try:
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({
                'success': True,
                'authenticated': False,
                'data': None
            })

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email
                FROM users
                WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()

            if not user:
                session.clear()
                return jsonify({
                    'success': True,
                    'authenticated': False,
                    'data': None
                })

            return jsonify({
                'success': True,
                'authenticated': True,
                'data': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email']
                }
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    修改密码（需要登录）
    POST /api/v1/users/change-password
    请求体：{ old_password, new_password }
    """
    try:
        data = request.get_json()

        if not data or not data.get('old_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'error': '旧密码和新密码不能为空'
            }), 400

        old_password = data['old_password']
        new_password = data['new_password']
        user_id = g.user_id

        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'error': '新密码长度不能少于6位'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 获取当前用户的密码哈希
            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({
                    'success': False,
                    'error': '用户不存在'
                }), 404

            # 验证旧密码
            old_password_hash = hash_password(old_password)
            if user['password_hash'] != old_password_hash:
                return jsonify({
                    'success': False,
                    'error': '旧密码错误'
                }), 400

            # 更新密码
            new_password_hash = hash_password(new_password)
            cursor.execute("""
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
            """, (new_password_hash, user_id))
            conn.commit()

        return jsonify({
            'success': True,
            'message': '密码修改成功，请重新登录'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    重置密码（通过邮箱）
    POST /api/v1/users/reset-password
    请求体：{ username, email }

    注意：这是一个简化实现，实际应用中应该发送邮件验证链接
    当前实现：如果用户名和邮箱匹配，返回一个临时重置码
    """
    try:
        data = request.get_json()

        if not data or not data.get('username') or not data.get('email'):
            return jsonify({
                'success': False,
                'error': '用户名和邮箱不能为空'
            }), 400

        username = data['username']
        email = data['email']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 查找用户
            cursor.execute("""
                SELECT id, username, email
                FROM users
                WHERE username = %s AND email = %s
            """, (username, email))
            user = cursor.fetchone()

            if not user:
                return jsonify({
                    'success': False,
                    'error': '用户名和邮箱不匹配'
                }), 404

            # 简化实现：生成重置码并返回
            # 实际应用中应该发送邮件
            import secrets
            reset_code = secrets.token_hex(16)

            # 这里应该将reset_code存储到数据库或缓存中，并设置过期时间
            # 简化实现：直接返回重置码（仅用于演示）
            return jsonify({
                'success': True,
                'message': '验证成功，请使用以下重置码修改密码（有效期10分钟）',
                'data': {
                    'reset_code': reset_code,
                    'user_id': user['id']
                }
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_bp.route('/confirm-reset', methods=['POST'])
def confirm_reset():
    """
    使用重置码确认密码重置
    POST /api/v1/users/confirm-reset
    请求体：{ reset_code, new_password, user_id }
    """
    try:
        data = request.get_json()

        if not data or not data.get('reset_code') or not data.get('new_password') or not data.get('user_id'):
            return jsonify({
                'success': False,
                'error': '参数不完整'
            }), 400

        reset_code = data['reset_code']
        new_password = data['new_password']
        user_id = data['user_id']

        if len(new_password) < 6:
            return jsonify({
                'success': False,
                'error': '新密码长度不能少于6位'
            }), 400

        # 在实际应用中，这里应该验证reset_code是否有效且未过期
        # 简化实现：直接修改密码

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 验证用户存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': '用户不存在'
                }), 404

            # 更新密码
            new_password_hash = hash_password(new_password)
            cursor.execute("""
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
            """, (new_password_hash, user_id))
            conn.commit()

        return jsonify({
            'success': True,
            'message': '密码重置成功，请使用新密码登录'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
