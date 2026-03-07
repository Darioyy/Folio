"""
系统相关API
学习要点：系统信息获取、统计数据
"""
from flask import request, jsonify, g
from api import system_bp
from api.auth import login_required
from app import get_db_connection


@system_bp.route('/info', methods=['GET'])
def get_system_info():
    """
    获取系统信息
    GET /api/v1/system/info
    返回：数据库表统计、版本信息等
    """
    try:
        conn = get_db_connection()
        # 确保连接有效
        conn.ping(reconnect=True)

        with conn.cursor() as cursor:
            # 获取各表记录数
            tables = ['users', 'categories', 'posts', 'resources', 'media']
            stats = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    stats[table] = result['count']
                except Exception:
                    stats[table] = 0

            # 获取数据库大小（可选，如果失败则设为0）
            try:
                cursor.execute("""
                    SELECT
                        table_schema AS 'database',
                        ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'size_mb'
                    FROM information_schema.tables
                    WHERE table_schema = 'ai_web_dev'
                    GROUP BY table_schema
                """)
                db_size = cursor.fetchone()
                database_size_mb = db_size['size_mb'] if db_size else 0
            except Exception:
                database_size_mb = 0

        return jsonify({
            'success': True,
            'data': {
                'version': '1.0.0',
                'database_stats': stats,
                'database_size_mb': database_size_mb
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@system_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    获取所有分类
    GET /api/v1/system/categories
    返回：分类列表，供前端表单使用
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM categories ORDER BY type, name")
            categories = cursor.fetchall()

        return jsonify({
            'success': True,
            'data': categories
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@system_bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    """
    创建新分类（需要登录）
    POST /api/v1/system/categories
    请求体：{ name, type, description }
    """
    try:
        data = request.get_json()

        if not data or not data.get('name') or not data.get('type'):
            return jsonify({
                'success': False,
                'error': '分类名称和类型不能为空'
            }), 400

        name = data['name'].strip()
        category_type = data['type']
        description = data.get('description', '').strip()

        # 验证分类类型
        if category_type not in ['post', 'resource', 'media']:
            return jsonify({
                'success': False,
                'error': '分类类型必须是 post、resource 或 media'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 检查分类名是否已存在
            cursor.execute("SELECT id FROM categories WHERE name = %s AND type = %s", (name, category_type))
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'error': '该分类名称已存在'
                }), 400

            # 创建分类
            cursor.execute("""
                INSERT INTO categories (name, type, description)
                VALUES (%s, %s, %s)
            """, (name, category_type, description))
            conn.commit()

            return jsonify({
                'success': True,
                'message': '分类创建成功',
                'data': {
                    'id': cursor.lastrowid,
                    'name': name
                }
            }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500