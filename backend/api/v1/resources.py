"""
学习资源 API 路由 - v1
内部已切换到 FileService（数据来自 files 表），路由路径不变保持向后兼容
"""
import os
from flask import Blueprint, request, g, send_file
from werkzeug.utils import secure_filename

from db.session import db as db_session
from core.schemas.file import FileCreate, FileUpdate
from core.services.file_service import FileService
from core.utils.validators import login_required
from core.utils.permissions import require_root
from core.utils.response import success_response, error_response, pagination_response
from config.default import Config


bp = Blueprint('resources_v1', __name__)


@bp.route('', methods=['GET'])
def list_resources():
    """
    获取资源列表

    Query: page, page_size
    """
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 10, type=int), 100)

    result = FileService.list_files(
        page=page,
        page_size=page_size,
        file_category='resource',
        session=db_session.session,
        include_user=True,
    )

    items = [f.to_dict(include_user=True) for f in result['items']]
    return pagination_response(items, result['page'], result['page_size'], result['total'])


@bp.route('/<int:file_id>', methods=['GET'])
def get_resource(file_id: int):
    """获取资源详情（私有文件仅文件所有者或 Root 可访问）"""
    from flask import session as flask_session
    file = FileService.get_by_id(file_id, db_session.session)
    if not file:
        return error_response('RESOURCE_NOT_FOUND', '资源不存在', 404)
    if file.visibility == 'private':
        uid = flask_session.get('user_id')
        if uid != file.user_id and not (uid and require_root(uid, db_session.session)):
            return error_response('FORBIDDEN', '无权访问此文件', 403)
    return success_response(file.to_dict(include_user=True))


@bp.route('/upload', methods=['POST'])
@login_required
def upload_resource():
    """
    上传资源文件

    Form: file, title, description(可选)
    """
    if 'file' not in request.files:
        return error_response('NO_FILE', '没有上传文件', 400)

    file = request.files['file']
    if not file.filename:
        return error_response('EMPTY_FILENAME', '未选择文件', 400)

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip() or None

    if not title:
        return error_response('MISSING_TITLE', 'title 不能为空', 400)

    allowed = Config.ALLOWED_EXTENSIONS.get('documents', set())
    if not FileService.allowed_file(file.filename, allowed):
        return error_response('INVALID_FILE_TYPE', f'不支持的文件类型，允许: {allowed}', 400)

    # 保存文件
    upload_dir = os.path.abspath(os.path.join(Config.UPLOAD_FOLDER, 'resources'))
    os.makedirs(upload_dir, exist_ok=True)

    unique_filename = FileService.generate_unique_filename(file.filename)
    full_path = os.path.join(upload_dir, unique_filename)
    file.save(full_path)

    file_size = os.path.getsize(full_path)
    mime_type = file.mimetype or 'application/octet-stream'
    uploads_abs = os.path.abspath(Config.UPLOAD_FOLDER)
    relative_path = os.path.relpath(full_path, uploads_abs)

    try:
        created = FileService.create(
            file_data=FileCreate(
                title=title,
                description=description,
                file_category='resource',
                visibility='private',
            ),
            file_path=relative_path,
            file_name=secure_filename(file.filename),
            file_size=file_size,
            mime_type=mime_type,
            user_id=g.user_id,
            session=db_session.session,
        )
        return success_response(created.to_dict(), '文件上传成功', 201)

    except Exception as e:
        if os.path.exists(full_path):
            os.remove(full_path)
        return error_response('UPLOAD_FAILED', f'上传失败: {e}', 500)


@bp.route('/<int:file_id>/download', methods=['GET'])
def download_resource(file_id: int):
    """下载资源文件（私有文件仅文件所有者或 Root 可下载）"""
    from flask import session as flask_session
    file = FileService.get_by_id(file_id, db_session.session)
    if not file:
        return error_response('RESOURCE_NOT_FOUND', '资源不存在', 404)
    if file.visibility == 'private':
        uid = flask_session.get('user_id')
        if uid != file.user_id and not (uid and require_root(uid, db_session.session)):
            return error_response('FORBIDDEN', '无权下载此文件', 403)

    full_path = os.path.join(os.path.abspath(Config.UPLOAD_FOLDER), file.file_path)
    if not os.path.exists(full_path):
        return error_response('FILE_NOT_FOUND', '文件不存在', 404)

    # 增加下载计数
    try:
        file.download_count = (file.download_count or 0) + 1
        db_session.session.commit()
    except Exception:
        pass  # 计数失败不影响下载

    return send_file(full_path, as_attachment=True, download_name=file.file_name)


@bp.route('/<int:file_id>', methods=['PUT'])
@login_required
def update_resource(file_id: int):
    """更新资源信息（title / description / visibility）"""
    try:
        data = FileUpdate(**request.json)
    except Exception as e:
        return error_response('INVALID_PARAMS', str(e), 400)

    try:
        updated = FileService.update(file_id, data, g.user_id, db_session.session)
        return success_response(updated.to_dict(), '更新成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/<int:file_id>', methods=['DELETE'])
@login_required
def delete_resource(file_id: int):
    """删除资源"""
    try:
        FileService.delete(file_id, g.user_id, db_session.session, Config.UPLOAD_FOLDER)
        return success_response(message='资源删除成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)
