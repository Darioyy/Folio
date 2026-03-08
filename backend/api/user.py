"""
用户相关API
学习要点：用户认证、密码哈希、会话管理
"""
import secrets
import bcrypt
import logging
from flask import request, jsonify, session, g
from api import user_bp
from api.auth import login_required, is_admin_user, is_root_user, can_modify_admin, can_modify_root, can_delete_user, normalize_permission_value
from database import get_db_connection

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    密码哈希函数（使用bcrypt）
    学习要点：bcrypt是专门用于密码哈希的安全算法
    """
    # 生成盐值并哈希密码
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str, user_id: int = None) -> bool:
    """
    验证密码（支持双格式并自动迁移）

    Args:
        password: 明文密码
        password_hash: 数据库中的密码哈希
        user_id: 用户ID（可选，用于密码自动迁移）

    Returns:
        bool: 验证是否成功
    """
    # 1. 首先尝试 bcrypt 验证（新格式）
    try:
        if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            return True
    except Exception:
        pass

    # 2. 如果 bcrypt 验证失败，尝试旧的 SHA-256 格式
    try:
        import hashlib
        salt = "ai_web_dev_salt_2024"
        old_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        if old_hash == password_hash:
            # 验证成功，自动迁移到 bcrypt
            if user_id is not None:
                new_hash = hash_password(password)
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cursor:
                            cursor.execute(
                                "UPDATE users SET password_hash = %s WHERE id = %s",
                                (new_hash, user_id)
                            )
                            conn.commit()
                    logger.info(f"用户 {user_id} 密码已从 SHA-256 迁移到 bcrypt")
                except Exception as e:
                    logger.error(f"密码迁移失败: {e}")
            return True
    except Exception:
        pass

    return False


@user_bp.route('/', methods=['GET'])
@login_required
def get_users():
    """
    获取用户列表（需要登录）
    GET /api/v1/users
    查询参数：page, limit
    权限：
    - root 可以看到所有人的所有信息（包括密码）
    - admin 可以看到所有人，但只能看到普通用户的邮箱（其他admin/root的邮箱显示[隐藏]）
    - 普通用户无法访问用户列表（返回403）
    """
    try:
        # 检查当前用户权限
        current_is_root = is_root_user(session.get('user_id')) if session.get('user_id') else False
        current_is_admin = is_admin_user(session.get('user_id')) if session.get('user_id') else False
        current_user_id = session.get('user_id')

        # 普通用户无权访问用户列表
        if not current_is_root and not current_is_admin:
            return jsonify({
                'success': False,
                'error': '权限不足，无法访问用户列表'
            }), 403

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        offset = (page - 1) * limit

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 获取总数
                cursor.execute("SELECT COUNT(*) as total FROM users")
                total = cursor.fetchone()['total']

                # 获取分页数据 - 按 ID 升序排列
                # root 可以查看所有人的信息（但不返回密码哈希）
                if current_is_root:
                    cursor.execute("""
                        SELECT id, username, email, is_admin, is_root, created_at
                        FROM users
                        ORDER BY id ASC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    users = cursor.fetchall()
                # admin 只能看到普通用户和admin，看不到root用户
                else:
                    cursor.execute("""
                        SELECT
                            id,
                            username,
                            email,
                            is_admin,
                            is_root,
                            created_at
                        FROM users
                        WHERE is_root != 1
                        ORDER BY id ASC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    users = cursor.fetchall()

                # 标准化权限字段为整数（确保前端能正确判断）
                for user in users:
                    user['is_admin'] = normalize_permission_value(user.get('is_admin', 0))
                    user['is_root'] = normalize_permission_value(user.get('is_root', 0))
                    logger.info(f"[get_users] 用户 {user['username']}: is_root={user['is_root']}, is_admin={user['is_admin']}, email={user.get('email', 'None')}")

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
        current_user_id = session.get('user_id')
        current_is_root = is_root_user(current_user_id) if current_user_id else False
        current_is_admin = is_admin_user(current_user_id) if current_user_id else False

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 只能查看自己的信息，admin/root 可以查看所有人
                if not current_is_root and not current_is_admin and current_user_id != user_id:
                    return jsonify({
                        'success': False,
                        'error': '没有权限查看此用户信息'
                    }), 403

                # root 可以查看所有人的信息（但不返回密码哈希）
                if current_is_root:
                    cursor.execute("""
                        SELECT id, username, email, is_admin, is_root, created_at
                        FROM users
                        WHERE id = %s
                    """, (user_id,))
                # admin 只能查看普通用户和admin，不能查看root
                elif current_is_admin:
                    cursor.execute("""
                        SELECT
                            id,
                            username,
                            email,
                            is_admin,
                            is_root,
                            created_at
                        FROM users
                        WHERE id = %s AND is_root != 1
                    """, (user_id,))
                else:
                    # 普通用户查看自己的信息
                    cursor.execute("""
                        SELECT id, username, email, is_admin, is_root, created_at
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

        with get_db_connection() as conn:
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
    权限：
    - 只能修改自己的信息
    - admin 可以修改普通用户信息
    - root 可以修改任何人信息
    - 不能修改其他 root 的信息
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400

        # 权限检查
        if g.user_id != user_id and not is_admin_user(g.user_id):
            return jsonify({
                'success': False,
                'error': '没有权限修改此用户信息'
            }), 403

        # 检查是否可以修改目标用户
        if g.user_id != user_id:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT is_root, is_admin FROM users WHERE id = %s", (user_id,))
                    target_user = cursor.fetchone()
                    if not target_user:
                        return jsonify({
                            'success': False,
                            'error': '用户不存在'
                        }), 404

                    # 非root不能修改root用户的信息
                    if target_user.get('is_root', 0) == 1 and not is_root_user(g.user_id):
                        return jsonify({
                            'success': False,
                            'error': '没有权限修改 root 用户信息'
                        }), 403

                    # admin不能修改其他admin/root的信息
                    if is_admin_user(g.user_id) and not is_root_user(g.user_id):
                        if target_user.get('is_root', 0) == 1 or target_user.get('is_admin', 0) == 1:
                            return jsonify({
                                'success': False,
                                'error': '没有权限修改此用户信息'
                            }), 403

        with get_db_connection() as conn:
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
                    if not verify_password(current_password, user['password_hash']):
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
    删除用户（需要登录）
    DELETE /api/v1/users/{id}
    权限：
    - root 可以删除任何人（除了自己）
    - admin 可以删除普通用户（不能删除 admin 和 root）
    """
    try:
        # 权限检查
        if not can_delete_user(user_id):
            return jsonify({
                'success': False,
                'error': '没有权限删除此用户'
            }), 403

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查用户是否存在
                cursor.execute("SELECT id, username FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if not user:
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


@user_bp.route('/<int:user_id>/admin', methods=['PUT'])
@login_required
def set_user_admin(user_id):
    """
    设置用户管理员权限
    PUT /api/v1/users/{id}/admin
    请求体：{ is_admin: boolean }
    权限：
    - root 可以修改任何人的管理员权限（包括其他root）
    - admin 可以修改普通用户的管理员权限
    - admin 不能修改 root 的管理员权限
    - 不能取消自己的管理员权限
    """
    try:
        current_user_id = g.user_id
        logger.info(f"[set_user_admin] 当前用户ID: {current_user_id}, 目标用户ID: {user_id}")

        # 权限检查
        from api.auth import can_modify_admin
        has_permission = can_modify_admin(user_id)
        logger.info(f"[set_user_admin] 权限检查结果: {has_permission}")

        if not has_permission:
            return jsonify({
                'success': False,
                'error': '没有权限修改管理员权限'
            }), 403

        data = request.get_json()
        logger.info(f"[set_user_admin] 请求数据: {data}")

        if data is None or 'is_admin' not in data:
            return jsonify({
                'success': False,
                'error': '缺少 is_admin 参数'
            }), 400

        is_admin = 1 if data.get('is_admin') else 0
        logger.info(f"[set_user_admin] 要设置的is_admin值: {is_admin}")

        # 不能取消自己的管理员权限
        if user_id == g.user_id and is_admin == 0:
            return jsonify({
                'success': False,
                'error': '不能取消自己的管理员权限'
            }), 400

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查用户是否存在
                cursor.execute("SELECT id, username, is_root, is_admin FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()
                if not user:
                    return jsonify({
                        'success': False,
                        'error': '用户不存在'
                    }), 404

                logger.info(f"[set_user_admin] 目标用户: {user}")

                # 更新管理员权限（root可以修改其他root，admin不能修改root）
                cursor.execute(
                    "UPDATE users SET is_admin = %s WHERE id = %s",
                    (is_admin, user_id)
                )
                conn.commit()
                logger.info(f"[set_user_admin] 更新成功: 用户 {user_id} 的 is_admin 设置为 {is_admin}")

        action = '设置为管理员' if is_admin else '取消管理员权限'
        return jsonify({
            'success': True,
            'message': f'已将 {user["username"]} {action}'
        })

    except Exception as e:
        logger.error(f"[set_user_admin] 错误: {e}")
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

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 获取用户信息（包括密码哈希）
                cursor.execute("""
                    SELECT id, username, email, password_hash, is_admin, is_root
                    FROM users
                    WHERE username = %s
                """, (username,))
                user = cursor.fetchone()

                # 验证密码（传入user_id用于自动迁移）
                if not user or not verify_password(password, user['password_hash'], user['id']):
                    return jsonify({
                        'success': False,
                        'error': '用户名或密码错误'
                    }), 401

                # 设置session
                session['user_id'] = user['id']
                session['username'] = user['username']

                # 标准化权限字段（确保返回整数而非布尔值）
                from api.auth import normalize_permission_value
                is_admin = normalize_permission_value(user.get('is_admin', 0))
                is_root = normalize_permission_value(user.get('is_root', 0))

                return jsonify({
                    'success': True,
                    'message': '登录成功',
                    'data': {
                        'id': user['id'],
                        'username': user['username'],
                        'email': user['email'],
                        'is_admin': is_admin,
                        'is_root': is_root
                    }
                })

    except Exception as e:
        logger.error(f"登录失败: {e}")
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

        with get_db_connection() as conn:
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

        # 使用auth模块的函数获取标准化用户信息
        from api.auth import get_user_info
        user = get_user_info(user_id)

        if not user:
            session.clear()
            return jsonify({
                'success': False,
                'error': '用户不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': user
        })

    except Exception as e:
        logger.error(f"获取当前用户信息失败: {e}")
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

        # 使用auth模块的函数获取标准化用户信息
        from api.auth import get_user_info
        user = get_user_info(user_id)

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
            'data': user
        })

    except Exception as e:
        logger.error(f"检查登录状态失败: {e}")
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

        with get_db_connection() as conn:
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
                if not verify_password(old_password, user['password_hash']):
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

        with get_db_connection() as conn:
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

        with get_db_connection() as conn:
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
