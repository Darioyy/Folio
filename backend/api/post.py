"""
文章相关API
学习要点：CRUD完整实现、分页查询、搜索过滤
"""
from flask import request, jsonify, g
from api import post_bp
from api.auth import login_required, is_admin_user
from database import get_db_connection


@post_bp.route('/', methods=['GET'])
def get_posts():
    """
    获取文章列表
    GET /api/v1/posts
    查询参数：page, limit, status, category_id, search
    status可选值：published, draft, all（默认all，返回所有文章）
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        status = request.args.get('status', 'all')
        category_id = request.args.get('category_id')
        search = request.args.get('search', '')
        offset = (page - 1) * limit

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 构建查询条件
                where_conditions = []
                params = []

                # 如果指定了status且不是all，则添加过滤条件
                if status and status != 'all':
                    where_conditions.append("status = %s")
                    params.append(status)

                if category_id:
                    where_conditions.append("category_id = %s")
                    params.append(category_id)

                if search:
                    where_conditions.append("(title LIKE %s OR content LIKE %s)")
                    search_pattern = f"%{search}%"
                    params.extend([search_pattern, search_pattern])

                # 如果没有条件，查询所有文章
                if where_conditions:
                    where_clause = " AND ".join(where_conditions)
                else:
                    where_clause = "1=1"

                # 获取总数
                count_sql = f"SELECT COUNT(*) as total FROM posts WHERE {where_clause}"
                cursor.execute(count_sql, params)
                total = cursor.fetchone()['total']

                # 获取分页数据
                params.extend([limit, offset])
                data_sql = f"""
                    SELECT p.*, c.name as category_name, u.username as author_name
                    FROM posts p
                    LEFT JOIN categories c ON p.category_id = c.id
                    LEFT JOIN users u ON p.author_id = u.id
                    WHERE {where_clause}
                    ORDER BY p.created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(data_sql, params)
                posts = cursor.fetchall()

        return jsonify({
            'success': True,
            'data': posts,
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


@post_bp.route('/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """
    获取单篇文章详情
    GET /api/v1/posts/{id}
    同时增加浏览次数
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 获取文章
                cursor.execute("""
                    SELECT p.*, c.name as category_name, u.username as author_name
                    FROM posts p
                    LEFT JOIN categories c ON p.category_id = c.id
                    LEFT JOIN users u ON p.author_id = u.id
                    WHERE p.id = %s
                """, (post_id,))
                post = cursor.fetchone()

                if not post:
                    return jsonify({
                        'success': False,
                        'error': '文章不存在'
                    }), 404

                # 增加浏览次数
                cursor.execute("""
                    UPDATE posts
                    SET view_count = view_count + 1
                    WHERE id = %s
                """, (post_id,))
                conn.commit()

        return jsonify({
            'success': True,
            'data': post
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@post_bp.route('/', methods=['POST'])
@login_required
def create_post():
    """
    创建新文章（需要登录）
    POST /api/v1/posts
    请求体：{ title, content, summary, category_id, status }
    author_id自动从session获取
    """
    try:
        data = request.get_json()

        # 参数验证
        required_fields = ['title', 'content']
        for field in required_fields:
            if not data or not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} 不能为空'
                }), 400

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 使用当前登录用户作为作者
                author_id = g.user_id

                # 获取status，默认为draft
                status = data.get('status', 'draft')
                # 验证status值
                if status not in ['draft', 'published', 'archived']:
                    status = 'draft'

                # 插入文章
                cursor.execute("""
                    INSERT INTO posts (title, content, summary, category_id, author_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    data['title'],
                    data['content'],
                    data.get('summary', ''),
                    data.get('category_id'),
                    author_id,
                    status
                ))
                conn.commit()

                return jsonify({
                    'success': True,
                    'message': '文章创建成功',
                    'data': {'id': cursor.lastrowid}
                }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@post_bp.route('/<int:post_id>', methods=['PUT'])
@login_required
def update_post(post_id):
    """
    更新文章（需要登录）
    PUT /api/v1/posts/{id}
    请求体：{ title, content, summary, category_id, status }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400

        # 可更新字段白名单（防止SQL注入）
        updatable_fields = {
            'title': '%s',
            'content': '%s',
            'summary': '%s',
            'category_id': '%s',
            'status': '%s'
        }

        updates = []
        params = []

        for field in updatable_fields:
            if field in data:
                updates.append(f"{field} = {updatable_fields[field]}")
                params.append(data[field])

        if not updates:
            return jsonify({
                'success': False,
                'error': '没有可更新的字段'
            }), 400

        params.append(post_id)

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查文章是否存在并获取作者信息
                cursor.execute("SELECT id, author_id FROM posts WHERE id = %s", (post_id,))
                post = cursor.fetchone()

                if not post:
                    return jsonify({
                        'success': False,
                        'error': '文章不存在'
                    }), 404

                # 权限检查：只有admin或文章作者可以更新
                if not is_admin_user(g.user_id) and post['author_id'] != g.user_id:
                    return jsonify({
                        'success': False,
                        'error': '没有权限更新此文章'
                    }), 403

                # 更新文章（使用安全的SQL构建方式）
                sql = f"UPDATE posts SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(sql, params)
                conn.commit()

        return jsonify({
            'success': True,
            'message': '文章更新成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@post_bp.route('/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    """
    删除文章（需要登录）
    DELETE /api/v1/posts/{id}
    权限：只有admin或文章作者可以删除
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查文章是否存在并获取作者信息
                cursor.execute("SELECT id, author_id FROM posts WHERE id = %s", (post_id,))
                post = cursor.fetchone()

                if not post:
                    return jsonify({
                        'success': False,
                        'error': '文章不存在'
                    }), 404

                # 权限检查：只有admin或文章作者可以删除
                if not is_admin_user(g.user_id) and post['author_id'] != g.user_id:
                    return jsonify({
                        'success': False,
                        'error': '没有权限删除此文章'
                    }), 403

                # 删除文章
                cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
                conn.commit()

        return jsonify({
            'success': True,
            'message': '文章删除成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
