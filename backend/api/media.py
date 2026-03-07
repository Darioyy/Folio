"""
媒体文件相关API（游戏视频/截图）
学习要点：多媒体文件处理、图片显示
"""
import os
import uuid
import cv2
import numpy as np
from flask import request, jsonify, send_file, g
from werkzeug.utils import secure_filename
from api import media_bp
from api.auth import login_required, is_admin_user
from app import get_db_connection
from config import Config


def allowed_media_file(filename, media_type):
    """
    检查媒体文件类型是否允许
    """
    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()

    if media_type == 'image':
        return ext in Config.ALLOWED_EXTENSIONS['images']
    elif media_type == 'video':
        return ext in Config.ALLOWED_EXTENSIONS['videos']
    return False


def generate_video_thumbnail(video_path, output_dir):
    """
    从视频文件中截取第一帧作为缩略图
    学习要点：使用OpenCV处理视频
    """
    try:
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"无法打开视频文件: {video_path}")
            return None

        # 读取第一帧
        ret, frame = cap.read()

        if not ret or frame is None:
            print(f"无法读取视频帧: {video_path}")
            cap.release()
            return None

        cap.release()

        # 生成缩略图文件名
        thumbnail_filename = f"{uuid.uuid4().hex}_thumb.jpg"
        thumbnail_path = os.path.join(output_dir, thumbnail_filename)

        # 调整缩略图尺寸
        target_width = 320
        height, width = frame.shape[:2]
        if width > target_width:
            scale = target_width / width
            new_width = target_width
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

        # 保存缩略图
        cv2.imwrite(thumbnail_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        return thumbnail_path

    except Exception as e:
        print(f"生成视频缩略图失败: {e}")
        return None


@media_bp.route('/', methods=['GET'])
def get_media():
    """
    获取媒体列表
    GET /api/v1/media
    查询参数：page, limit, type (image/video)
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 12))
        media_type = request.args.get('type')
        offset = (page - 1) * limit

        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 构建查询条件
            where_conditions = []
            params = []

            if media_type in ['image', 'video']:
                where_conditions.append("file_type = %s")
                params.append(media_type)

            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # 获取总数
            count_sql = f"SELECT COUNT(*) as total FROM media {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']

            # 获取分页数据
            params.extend([limit, offset])
            data_sql = f"""
                SELECT m.*, u.username as uploader_name
                FROM media m
                LEFT JOIN users u ON m.uploader_id = u.id
                {where_clause}
                ORDER BY m.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_sql, params)
            media_list = cursor.fetchall()

        return jsonify({
            'success': True,
            'data': media_list,
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


@media_bp.route('/<int:media_id>', methods=['GET'])
def get_media_detail(media_id):
    """
    获取单个媒体详情
    GET /api/v1/media/{id}
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT m.*, u.username as uploader_name
                FROM media m
                LEFT JOIN users u ON m.uploader_id = u.id
                WHERE m.id = %s
            """, (media_id,))
            media = cursor.fetchone()

        if not media:
            return jsonify({
                'success': False,
                'error': '媒体不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': media
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@media_bp.route('/upload', methods=['POST'])
@login_required
def upload_media():
    """
    上传媒体文件（需要登录）
    POST /api/v1/media/upload
    请求格式：multipart/form-data
    表单字段：file, title, description, type (image/video), thumbnail (可选)
    uploader_id自动从session获取
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
        media_type = request.form.get('type', 'image')
        uploader_id = g.user_id  # 使用当前登录用户
        thumbnail_file = request.files.get('thumbnail')  # 可选封面上传

        if not title:
            return jsonify({
                'success': False,
                'error': 'title 不能为空'
            }), 400

        # 验证文件类型
        if not allowed_media_file(file.filename, media_type):
            allowed = Config.ALLOWED_EXTENSIONS.get(media_type + 's' if media_type == 'image' else 'videos', set())
            return jsonify({
                'success': False,
                'error': f'不支持的文件类型，允许的类型: {allowed}'
            }), 400

        # 确保上传目录存在
        upload_dir = os.path.join(Config.UPLOAD_FOLDER, 'media', media_type + 's')
        upload_dir = os.path.abspath(upload_dir)
        os.makedirs(upload_dir, exist_ok=True)

        # 创建缩略图目录
        thumbnail_dir = os.path.join(Config.UPLOAD_FOLDER, 'media', 'thumbnails')
        thumbnail_dir = os.path.abspath(thumbnail_dir)
        os.makedirs(thumbnail_dir, exist_ok=True)

        # 生成唯一文件名并保存
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        # 处理缩略图
        thumbnail_path = None
        normalized_path = os.path.normpath(file_path)

        if media_type == 'image':
            # 图片直接作为自己的缩略图
            thumbnail_path = normalized_path
        else:
            # 视频处理缩略图
            if thumbnail_file and thumbnail_file.filename:
                # 用户上传了封面图片
                thumb_ext = thumbnail_file.filename.rsplit('.', 1)[1].lower()
                thumb_filename = f"{uuid.uuid4().hex}_thumb.{thumb_ext}"
                thumbnail_path = os.path.join(thumbnail_dir, thumb_filename)
                thumbnail_file.save(thumbnail_path)
                thumbnail_path = os.path.normpath(thumbnail_path)
            else:
                # 没有上传封面，自动截取视频第一帧
                print(f"正在为视频生成缩略图: {file.filename}")
                thumbnail_path = generate_video_thumbnail(file_path, thumbnail_dir)
                if thumbnail_path:
                    thumbnail_path = os.path.normpath(thumbnail_path)

        # 保存到数据库
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO media (title, description, file_path, file_name, file_type, thumbnail_path, uploader_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                title,
                description,
                normalized_path,
                file.filename,
                media_type,
                thumbnail_path,
                uploader_id
            ))
            conn.commit()

        return jsonify({
            'success': True,
            'message': '媒体上传成功',
            'data': {
                'id': cursor.lastrowid,
                'title': title,
                'type': media_type
            }
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@media_bp.route('/<int:media_id>/view', methods=['GET'])
def view_media(media_id):
    """
    查看媒体文件（用于图片显示或视频播放）
    GET /api/v1/media/{id}/view
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM media WHERE id = %s", (media_id,))
            media = cursor.fetchone()

            if not media:
                return jsonify({
                    'success': False,
                    'error': '媒体不存在'
                }), 404

            if not os.path.exists(media['file_path']):
                return jsonify({
                    'success': False,
                    'error': '文件不存在'
                }), 404

        # 发送文件（不作为附件，用于浏览器显示）
        return send_file(media['file_path'])

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@media_bp.route('/<int:media_id>', methods=['DELETE'])
@login_required
def delete_media(media_id):
    """
    删除媒体（需要登录）
    DELETE /api/v1/media/{id}
    权限：只有admin或上传者可以删除
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 获取媒体信息和上传者信息
            cursor.execute("SELECT file_path, uploader_id FROM media WHERE id = %s", (media_id,))
            media = cursor.fetchone()

            if not media:
                return jsonify({
                    'success': False,
                    'error': '媒体不存在'
                }), 404

            # 权限检查：只有admin或上传者可以删除
            if not is_admin_user(g.user_id) and media['uploader_id'] != g.user_id:
                return jsonify({
                    'success': False,
                    'error': '没有权限删除此媒体'
                }), 403

            # 删除数据库记录
            cursor.execute("DELETE FROM media WHERE id = %s", (media_id,))
            conn.commit()

            # 删除物理文件
            if os.path.exists(media['file_path']):
                os.remove(media['file_path'])

        return jsonify({
            'success': True,
            'message': '媒体删除成功'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
