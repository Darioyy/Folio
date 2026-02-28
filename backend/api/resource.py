"""
学习资源相关API
学习要点：文件上传、文件类型验证、下载计数
"""
import os
import uuid
from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename
from api import resource_bp
from app import get_db_connection
from config import Config


def allowed_file(filename, file_type):
    """
    检查文件类型是否允许
    学习要点：文件安全验证，防止恶意文件上传
    """
    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()

    if file_type == 'image':
        return ext in Config.ALLOWED_EXTENSIONS['images']
    elif file_type == 'document':
        return ext in Config.ALLOWED_EXTENSIONS['documents']
    return False


def generate_unique_filename(filename):
    """
    生成唯一文件名
    学习要点：防止文件名冲突，同时保留原始扩展名
    """
    ext = filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    return unique_name


@resource_bp.route('/', methods=['GET'])
def get_resources():
    """
    获取资源列表
    GET /api/v1/resources
    查询参数：page, limit, category_id
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        category_id = request.args.get('category_id')
        offset = (page - 1) * limit

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 构建查询条件
            where_conditions = []
            params = []

            if category_id:
                where_conditions.append("category_id = %s")
                params.append(category_id)

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # 获取总数
            count_sql = f"SELECT COUNT(*) as total FROM resources {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']

            # 获取分页数据
            params.extend([limit, offset])
            data_sql = f"""
                SELECT r.*, c.name as category_name, u.username as uploader_name
                FROM resources r
                LEFT JOIN categories c ON r.category_id = c.id
                LEFT JOIN users u ON r.uploader_id = u.id
                {where_clause}
                ORDER BY r.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_sql, params)
            resources = cursor.fetchall()

        return jsonify({
            'success': True,
            'data': resources,
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


@resource_bp.route('/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    """
    获取单个资源详情
    GET /api/v1/resources/{id}
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT r.*, c.name as category_name, u.username as uploader_name
                FROM resources r
                LEFT JOIN categories c ON r.category_id = c.id
                LEFT JOIN users u ON r.uploader_id = u.id
                WHERE r.id = %s
            """, (resource_id,))
            resource = cursor.fetchone()

        if not resource:
            return jsonify({
                'success': False,
                'error': '资源不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': resource
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@resource_bp.route('/upload', methods=['POST'])
def upload_resource():
    """
    上传资源文件
    POST /api/v1/resources/upload
    请求格式：multipart/form-data
    表单字段：file, title, description, category_id, uploader_id
    """
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '未选择文件'
            }), 400

        # 获取表单数据
        title = request.form.get('title')
        description = request.form.get('description', '')
        category_id = request.form.get('category_id')
        uploader_id = request.form.get('uploader_id')

        if not title or not uploader_id:
            return jsonify({
                'success': False,
                'error': 'title 和 uploader_id 不能为空'
            }), 400

        # 验证文件类型
        if not allowed_file(file.filename, 'document'):
            return jsonify({
                'success': False,
                'error': f'不支持的文件类型，允许的类型: {Config.ALLOWED_EXTENSIONS["documents"]}'
            }), 400

        # 确保上传目录存在
        upload_dir = os.path.join(Config.UPLOAD_FOLDER, 'resources')
        os.makedirs(upload_dir, exist_ok=True)

        # 生成唯一文件名并保存
        unique_filename = generate_unique_filename(file.filename)
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # 获取文件信息
        file_size = os.path.getsize(file_path)
        file_type = file.mimetype or 'application/octet-stream'

        # 保存到数据库（保留原始文件名，避免中文乱码）
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO resources (title, description, file_path, file_name, file_size, file_type, category_id, uploader_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                title,
                description,
                file_path,
                file.filename,  # 保留原始文件名
                file_size,
                file_type,
                category_id,
                uploader_id
            ))
            conn.commit()

        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'data': {
                'id': cursor.lastrowid,
                'title': title,
                'original_filename': original_filename
            }
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@resource_bp.route('/<int:resource_id>/download', methods=['GET'])
def download_resource(resource_id):
    """
    下载资源文件
    GET /api/v1/resources/{id}/download
    增加下载计数
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 获取资源信息
            cursor.execute("SELECT * FROM resources WHERE id = %s", (resource_id,))
            resource = cursor.fetchone()

            if not resource:
                return jsonify({
                    'success': False,
                    'error': '资源不存在'
                }), 404

            # 检查文件是否存在
            if not os.path.exists(resource['file_path']):
                return jsonify({
                    'success': False,
                    'error': '文件不存在'
                }), 404

            # 增加下载计数
            cursor.execute("""
                UPDATE resources
                SET download_count = download_count + 1
                WHERE id = %s
            """, (resource_id,))
            conn.commit()

        # 发送文件
        return send_file(
            resource['file_path'],
            as_attachment=True,
            download_name=resource['file_name']
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@resource_bp.route('/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    """
    删除资源
    DELETE /api/v1/resources/{id}
    同时删除服务器上的文件
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 获取资源信息
            cursor.execute("SELECT file_path FROM resources WHERE id = %s", (resource_id,))
            resource = cursor.fetchone()

            if not resource:
                return jsonify({
                    'success': False,
                    'error': '资源不存在'
                }), 404

            # 删除数据库记录
            cursor.execute("DELETE FROM resources WHERE id = %s", (resource_id,))
            conn.commit()

            # 删除物理文件
            if os.path.exists(resource['file_path']):
                os.remove(resource['file_path'])

        return jsonify({
            'success': True,
            'message': '资源删除成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
