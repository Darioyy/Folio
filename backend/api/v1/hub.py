"""
个人工作台 API 路由 - v1
Private Hub: 私有文件管理、可见性切换、存储配额
内部已切换到 FileService，数据来自统一 files 表
"""
from flask import Blueprint, request, g

from db.session import db as db_session
from core.models.user import User
from core.services.file_service import FileService
from core.utils.validators import login_required
from core.utils.response import success_response, error_response, pagination_response


bp = Blueprint('hub_v1', __name__)


@bp.route('/storage', methods=['GET'])
@login_required
def get_storage_info():
    """
    获取用户存储配额信息

    Response: { storage_used, storage_quota, storage_percentage }
    """
    user = db_session.session.get(User, g.user_id)
    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    storage_used = FileService.get_storage_used(g.user_id, db_session.session)
    storage_quota = user.storage_quota or 209715200  # 默认 200MB

    return success_response({
        'storage_used': storage_used,
        'storage_quota': storage_quota,
        'storage_percentage': round(storage_used / storage_quota * 100, 2) if storage_quota > 0 else 0,
    })


@bp.route('/media', methods=['GET'])
@login_required
def get_user_media():
    """
    获取用户媒体文件列表（image + video）

    Query: page, page_size, visibility(private/public), type(image/video)
    """
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)
    visibility = request.args.get('visibility')
    media_type = request.args.get('type')

    if visibility and visibility not in ('private', 'public'):
        return error_response('INVALID_PARAMS', 'visibility 必须是 private 或 public', 400)
    if media_type and media_type not in ('image', 'video'):
        return error_response('INVALID_PARAMS', 'type 必须是 image 或 video', 400)

    category = media_type if media_type else ['image', 'video']
    result = FileService.list_files(
        page=page,
        page_size=page_size,
        user_id=g.user_id,
        file_category=category,
        visibility=visibility,
        session=db_session.session,
        viewer_id=g.user_id,
    )

    items = [f.to_dict() for f in result['items']]
    return pagination_response(items, result['page'], result['page_size'], result['total'])


@bp.route('/resources', methods=['GET'])
@login_required
def get_user_resources():
    """
    获取用户资源文件列表

    Query: page, page_size, visibility(private/public)
    """
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)
    visibility = request.args.get('visibility')

    if visibility and visibility not in ('private', 'public'):
        return error_response('INVALID_PARAMS', 'visibility 必须是 private 或 public', 400)

    result = FileService.list_files(
        page=page,
        page_size=page_size,
        user_id=g.user_id,
        file_category='resource',
        visibility=visibility,
        session=db_session.session,
        viewer_id=g.user_id,
    )

    items = [f.to_dict() for f in result['items']]
    return pagination_response(items, result['page'], result['page_size'], result['total'])


@bp.route('/media/<int:file_id>/visibility', methods=['PATCH'])
@login_required
def toggle_media_visibility(file_id: int):
    """切换媒体文件可见性（private ↔ public）"""
    try:
        new_visibility = FileService.toggle_visibility(file_id, g.user_id, db_session.session)
        return success_response({'visibility': new_visibility}, '切换成功')
    except ValueError as e:
        return error_response('MEDIA_NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/resources/<int:file_id>/visibility', methods=['PATCH'])
@login_required
def toggle_resource_visibility(file_id: int):
    """切换资源文件可见性（private ↔ public）"""
    try:
        new_visibility = FileService.toggle_visibility(file_id, g.user_id, db_session.session)
        return success_response({'visibility': new_visibility}, '切换成功')
    except ValueError as e:
        return error_response('RESOURCE_NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/public/media', methods=['GET'])
def get_public_media():
    """
    获取公共媒体文件列表（供公共大厅，无需登录）

    Query: page, page_size, type(image/video)
    """
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)
    media_type = request.args.get('type')

    if media_type and media_type not in ('image', 'video'):
        return error_response('INVALID_PARAMS', 'type 必须是 image 或 video', 400)

    category = media_type if media_type else ['image', 'video']
    result = FileService.list_files(
        page=page,
        page_size=page_size,
        file_category=category,
        visibility='public',
        session=db_session.session,
        include_user=True,
    )

    items = [f.to_dict(include_user=True) for f in result['items']]
    return pagination_response(items, result['page'], result['page_size'], result['total'])


@bp.route('/public/resources', methods=['GET'])
def get_public_resources():
    """
    获取公共资源文件列表（供公共大厅，无需登录）

    Query: page, page_size
    """
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    result = FileService.list_files(
        page=page,
        page_size=page_size,
        file_category='resource',
        visibility='public',
        session=db_session.session,
        include_user=True,
    )

    items = [f.to_dict(include_user=True) for f in result['items']]
    return pagination_response(items, result['page'], result['page_size'], result['total'])
