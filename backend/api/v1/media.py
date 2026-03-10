"""
媒体 API 路由 - v1版本
遵循 RESTful 规范和三层架构
"""
import os
import mimetypes
from flask import Blueprint, request, g, send_file, jsonify
from werkzeug.utils import secure_filename

from db.session import db as db_session
from core.schemas.media import MediaCreate, MediaUpdate
from core.services.media_service import MediaService
from core.utils.validators import login_required, admin_required
from core.utils.response import success_response, error_response, pagination_response
from config.default import Config


# 创建蓝图
bp = Blueprint('media_v1', __name__)


@bp.route('', methods=['GET'])
def list_media():
    """
    获取媒体列表

    Request:
        GET /api/v1/media?page=1&page_size=12&type=image

    Query Params:
        page: 页码（默认1）
        page_size: 每页数量（默认12，最大100）
        type: 媒体类型筛选（image/video）

    Response:
        {
            "success": true,
            "data": {
                "items": [...],
                "pagination": {...}
            }
        }
    """
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 12, type=int), 100)
    media_type = request.args.get('type')

    if media_type and media_type not in ['image', 'video']:
        return error_response('INVALID_PARAMS', 'type 必须是 image 或 video', 400)

    result = MediaService.list_media(page, page_size, media_type, None, None, db_session.session)

    items = [m.to_dict(include_uploader=True) for m in result['items']]
    return pagination_response(
        items,
        result['page'],
        result['page_size'],
        result['total']
    )


@bp.route('/<int:media_id>', methods=['GET'])
def get_media_detail(media_id: int):
    """
    获取媒体详情

    Request:
        GET /api/v1/media/:id

    Response:
        {
            "success": true,
            "data": {...}
        }
    """
    media = MediaService.get_by_id(media_id, db_session.session)
    if not media:
        return error_response('MEDIA_NOT_FOUND', '媒体不存在', 404)

    return success_response(media.to_dict(include_uploader=True))


@bp.route('/upload', methods=['POST'])
@login_required
def upload_media():
    """
    上传媒体文件

    Request:
        POST /api/v1/media/upload
        Content-Type: multipart/form-data

    Form Data:
        file: 文件（必需）
        title: 标题（必需）
        description: 描述（可选）
        type: 类型 image/video（必需，默认image）
        thumbnail: 封面图片（可选，仅视频）

    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "title": "...",
                "type": "image"
            }
        }
    """
    # 检查文件
    if 'file' not in request.files:
        return error_response('NO_FILE', '没有上传文件', 400)

    file = request.files['file']
    if file.filename == '':
        return error_response('NO_FILE', '未选择文件', 400)

    # 获取表单数据
    title = request.form.get('title')
    description = request.form.get('description', '')
    media_type = request.form.get('type', 'image')
    thumbnail_file = request.files.get('thumbnail')

    if not title:
        return error_response('INVALID_PARAMS', 'title 不能为空', 400)

    if media_type not in ['image', 'video']:
        return error_response('INVALID_PARAMS', 'type 必须是 image 或 video', 400)

    # 验证文件类型
    if not MediaService.allowed_file(file.filename, media_type, Config.ALLOWED_EXTENSIONS):
        allowed = Config.ALLOWED_EXTENSIONS.get(media_type + 's' if media_type == 'image' else 'videos', set())
        return error_response(
            'INVALID_FILE_TYPE',
            f'不支持的文件类型，允许的类型: {allowed}',
            400
        )

    # 创建上传目录
    upload_dir = os.path.join(Config.UPLOAD_FOLDER, 'media', media_type + 's')
    upload_dir = os.path.abspath(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)

    # 创建缩略图目录
    thumbnail_dir = os.path.join(Config.UPLOAD_FOLDER, 'media', 'thumbnails')
    thumbnail_dir = os.path.abspath(thumbnail_dir)
    os.makedirs(thumbnail_dir, exist_ok=True)

    # 保存文件
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{os.urandom(16).hex()}.{ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)

    # 计算文件大小
    file_size = os.path.getsize(file_path)

    # 计算相对路径
    uploads_dir = os.path.abspath(Config.UPLOAD_FOLDER)
    relative_file_path = os.path.relpath(file_path, uploads_dir)

    # 处理缩略图
    thumbnail_path = None
    width = None
    height = None
    duration = None

    if media_type == 'image':
        # 图片直接作为自己的缩略图
        thumbnail_path = relative_file_path
        width, height = MediaService.get_image_dimensions(file_path)
    else:
        # 视频处理
        duration = MediaService.get_video_duration(file_path)

        # 用户上传封面或自动生成
        if thumbnail_file and thumbnail_file.filename:
            thumb_ext = thumbnail_file.filename.rsplit('.', 1)[1].lower()
            thumb_filename = f"{os.urandom(16).hex}_thumb.{thumb_ext}"
            thumbnail_abs_path = os.path.join(thumbnail_dir, thumb_filename)
            thumbnail_file.save(thumbnail_abs_path)
            thumbnail_path = os.path.relpath(thumbnail_abs_path, uploads_dir)
        else:
            # 自动截取视频第一帧
            thumbnail_abs_path = MediaService.generate_video_thumbnail(file_path, thumbnail_dir)
            if thumbnail_abs_path:
                thumbnail_path = os.path.relpath(thumbnail_abs_path, uploads_dir)

    # 创建数据库记录
    media_data = MediaCreate(
        title=title,
        description=description,
        file_type=media_type
    )

    media = MediaService.create(
        media_data,
        relative_file_path,
        file.filename,
        g.user_id,
        thumbnail_path,
        width,
        height,
        duration,
        file_size,
        db_session.session
    )

    return success_response({
        'id': media.id,
        'title': media.title,
        'type': media.file_type
    }, '上传成功', 201)


@bp.route('/<int:media_id>/view', methods=['GET'])
def view_media(media_id: int):
    """
    查看媒体文件

    Request:
        GET /api/v1/media/:id/view

    Response:
        返回文件内容（直接在浏览器中显示）
    """
    media = MediaService.get_by_id(media_id, db_session.session)
    if not media:
        return error_response('MEDIA_NOT_FOUND', '媒体不存在', 404)

    # 转换为绝对路径
    uploads_dir = os.path.abspath(Config.UPLOAD_FOLDER)
    file_path = os.path.join(uploads_dir, media.file_path)

    if not os.path.exists(file_path):
        return error_response('FILE_NOT_FOUND', '文件不存在', 404)

    # 根据文件扩展名获取 MIME 类型
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        # 默认 MIME 类型
        mime_type = 'image/jpeg' if media.file_type == 'image' else 'video/mp4'

    return send_file(file_path, mimetype=mime_type)


@bp.route('/<int:media_id>', methods=['PUT'])
@login_required
def update_media(media_id: int):
    """
    更新媒体信息

    Request:
        PUT /api/v1/media/:id
        {
            "title": "新标题",
            "description": "新描述"
        }

    Response:
        {
            "success": true,
            "data": {...}
        }
    """
    try:
        data = MediaUpdate(**request.json)
    except Exception as e:
        return error_response('INVALID_PARAMS', str(e), 400)

    try:
        media = MediaService.update(media_id, data, g.user_id, db_session.session)
        return success_response(media.to_dict(include_uploader=True), '更新成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/<int:media_id>', methods=['DELETE'])
@login_required
def delete_media(media_id: int):
    """
    删除媒体

    Request:
        DELETE /api/v1/media/:id

    Response:
        {
            "success": true,
            "message": "删除成功"
        }
    """
    try:
        MediaService.delete(media_id, g.user_id, db_session.session, Config.UPLOAD_FOLDER)
        return success_response(message='删除成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/<int:media_id>/thumbnail', methods=['GET'])
def get_thumbnail(media_id: int):
    """
    获取媒体缩略图

    Request:
        GET /api/v1/media/:id/thumbnail

    Response:
        返回缩略图文件
    """
    media = MediaService.get_by_id(media_id, db_session.session)
    if not media:
        return error_response('MEDIA_NOT_FOUND', '媒体不存在', 404)

    if not media.thumbnail_path:
        # 没有缩略图，返回原图
        return view_media(media_id)

    uploads_dir = os.path.abspath(Config.UPLOAD_FOLDER)
    thumbnail_path = os.path.join(uploads_dir, media.thumbnail_path)

    if not os.path.exists(thumbnail_path):
        return error_response('FILE_NOT_FOUND', '缩略图不存在', 404)

    return send_file(thumbnail_path)
