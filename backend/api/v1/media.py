"""
媒体 API 路由 - v1
内部已切换到 FileService（数据来自 files 表），路由路径不变保持向后兼容
"""
import os
import mimetypes
from flask import Blueprint, request, g, send_file, Response
from werkzeug.utils import secure_filename

from db.session import db as db_session
from core.schemas.file import FileCreate, FileUpdate
from core.services.file_service import FileService
from core.utils.validators import login_required
from core.utils.permissions import require_root
from core.utils.response import success_response, error_response, pagination_response
from config.default import Config


bp = Blueprint('media_v1', __name__)


@bp.route('', methods=['GET'])
def list_media():
    """
    获取媒体列表（image + video）

    Query: page, page_size, type(image/video)
    """
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 12, type=int), 100)
    media_type = request.args.get('type')

    if media_type and media_type not in ('image', 'video'):
        return error_response('INVALID_PARAMS', 'type 必须是 image 或 video', 400)

    category = media_type if media_type else ['image', 'video']
    result = FileService.list_files(
        page=page,
        page_size=page_size,
        file_category=category,
        session=db_session.session,
        include_user=True,
    )

    items = [f.to_dict(include_user=True) for f in result['items']]
    return pagination_response(items, result['page'], result['page_size'], result['total'])


@bp.route('/<int:file_id>', methods=['GET'])
def get_media_detail(file_id: int):
    """获取媒体详情（私有文件仅文件所有者可访问）"""
    from flask import session as flask_session
    file = FileService.get_by_id(file_id, db_session.session)
    if not file:
        return error_response('MEDIA_NOT_FOUND', '媒体不存在', 404)
    if file.visibility == 'private':
        uid = flask_session.get('user_id')
        if uid != file.user_id and not (uid and require_root(uid, db_session.session)):
            return error_response('FORBIDDEN', '无权访问此文件', 403)
    return success_response(file.to_dict(include_user=True))


@bp.route('/upload', methods=['POST'])
@login_required
def upload_media():
    """
    上传媒体文件

    Form: file, title, description(可选), type(image/video), thumbnail(可选封面，仅 video)
    """
    if 'file' not in request.files:
        return error_response('NO_FILE', '没有上传文件', 400)

    file = request.files['file']
    if not file.filename:
        return error_response('NO_FILE', '未选择文件', 400)

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip() or None
    media_type = request.form.get('type', 'image')

    if not title:
        return error_response('INVALID_PARAMS', 'title 不能为空', 400)
    if media_type not in ('image', 'video'):
        return error_response('INVALID_PARAMS', 'type 必须是 image 或 video', 400)

    ext_key = 'images' if media_type == 'image' else 'videos'
    allowed = Config.ALLOWED_EXTENSIONS.get(ext_key, set())
    if not FileService.allowed_file(file.filename, allowed):
        return error_response('INVALID_FILE_TYPE', f'不支持的文件类型，允许: {allowed}', 400)

    # 保存文件
    subdir = f'media/{"images" if media_type == "image" else "videos"}'
    upload_dir = os.path.abspath(os.path.join(Config.UPLOAD_FOLDER, subdir))
    os.makedirs(upload_dir, exist_ok=True)

    unique_filename = FileService.generate_unique_filename(file.filename)
    full_path = os.path.join(upload_dir, unique_filename)
    file.save(full_path)

    file_size = os.path.getsize(full_path)
    mime_type = file.mimetype or 'application/octet-stream'
    uploads_abs = os.path.abspath(Config.UPLOAD_FOLDER)
    relative_path = os.path.relpath(full_path, uploads_abs)

    # 媒体专属处理
    thumbnail_path = None
    duration = None

    if media_type == 'image':
        thumbnail_path = relative_path
    else:
        duration = FileService.get_video_duration(full_path)
        thumb_dir = os.path.abspath(os.path.join(Config.UPLOAD_FOLDER, 'media', 'thumbnails'))
        os.makedirs(thumb_dir, exist_ok=True)

        thumbnail_file = request.files.get('thumbnail')
        if thumbnail_file and thumbnail_file.filename:
            thumb_full = os.path.join(thumb_dir, FileService.generate_unique_filename(thumbnail_file.filename))
            thumbnail_file.save(thumb_full)
            thumbnail_path = os.path.relpath(thumb_full, uploads_abs)
        else:
            thumb_abs = FileService.generate_video_thumbnail(full_path, thumb_dir)
            if thumb_abs:
                thumbnail_path = os.path.relpath(thumb_abs, uploads_abs)

    try:
        created = FileService.create(
            file_data=FileCreate(
                title=title,
                description=description,
                file_category=media_type,
                visibility='private',
            ),
            file_path=relative_path,
            file_name=secure_filename(file.filename),
            file_size=file_size,
            mime_type=mime_type,
            user_id=g.user_id,
            session=db_session.session,
            thumbnail_path=thumbnail_path,
            duration=duration,
        )
        return success_response(
            {'id': created.id, 'title': created.title, 'type': created.file_category},
            '上传成功', 201
        )

    except Exception as e:
        if os.path.exists(full_path):
            os.remove(full_path)
        return error_response('UPLOAD_FAILED', f'上传失败: {e}', 500)


@bp.route('/<int:file_id>/view', methods=['GET'])
def view_media(file_id: int):
    """查看媒体文件（直接返回文件流，私有文件仅文件所有者可访问）"""
    from flask import session as flask_session
    file = FileService.get_by_id(file_id, db_session.session)
    if not file:
        return Response(status=404)

    if file.visibility == 'private':
        uid = flask_session.get('user_id')
        if uid != file.user_id and not (uid and require_root(uid, db_session.session)):
            return Response(status=403)

    full_path = os.path.join(os.path.abspath(Config.UPLOAD_FOLDER), file.file_path)
    if not os.path.exists(full_path):
        return Response(status=404)

    mime_type, _ = mimetypes.guess_type(full_path)
    if not mime_type:
        mime_type = 'image/jpeg' if file.file_category == 'image' else 'video/mp4'

    return send_file(full_path, mimetype=mime_type)


@bp.route('/<int:file_id>', methods=['PUT'])
@login_required
def update_media(file_id: int):
    """更新媒体信息"""
    try:
        data = FileUpdate(**request.json)
    except Exception as e:
        return error_response('INVALID_PARAMS', str(e), 400)

    try:
        updated = FileService.update(file_id, data, g.user_id, db_session.session)
        return success_response(updated.to_dict(include_user=True), '更新成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/<int:file_id>', methods=['DELETE'])
@login_required
def delete_media(file_id: int):
    """删除媒体"""
    try:
        FileService.delete(file_id, g.user_id, db_session.session, Config.UPLOAD_FOLDER)
        return success_response(message='删除成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/<int:file_id>/thumbnail', methods=['GET'])
def get_thumbnail(file_id: int):
    """获取媒体缩略图（私有文件仅文件所有者可访问）"""
    from flask import session as flask_session
    file = FileService.get_by_id(file_id, db_session.session)
    if not file:
        return Response(status=404)

    if file.visibility == 'private':
        uid = flask_session.get('user_id')
        if uid != file.user_id and not (uid and require_root(uid, db_session.session)):
            return Response(status=403)

    thumb_path = file.thumbnail_path or file.file_path
    full_path = os.path.join(os.path.abspath(Config.UPLOAD_FOLDER), thumb_path)

    if not os.path.exists(full_path):
        return Response(status=404)

    return send_file(full_path)
