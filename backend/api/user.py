"""
用户相关API
学习要点：用户认证、密码哈希、会话管理
"""
import hashlib
from flask import request, jsonify
from api import user_bp
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
def update_user(user_id):
    """
    更新用户信息
    PUT /api/v1/users/{id}
    请求体：{ email, password }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400

        updates = []
        params = []

        # 构建动态更新语句
        if data.get('email'):
            updates.append("email = %s")
            params.append(data['email'])

        if data.get('password'):
            updates.append("password_hash = %s")
            params.append(hash_password(data['password']))

        if not updates:
            return jsonify({
                'success': False,
                'error': '没有可更新的字段'
            }), 400

        params.append(user_id)

        conn = get_db_connection()
        with conn.cursor() as cursor:
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
def delete_user(user_id):
    """
    删除用户
    DELETE /api/v1/users/{id}
    安全考虑：软删除（设置状态）比硬删除更好
    """
    try:
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
