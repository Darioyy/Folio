"""
个人工作台 API 路由 - v1版本
Private Hub: 私有文件管理、可见性切换、存储配额
"""
from flask import Blueprint, request, g
from db.session import db as db_session
from core.services.hub_service import HubService
from core.utils.validators import login_required
from core.utils.response import success_response, error_response, pagination_response


# 创建蓝图
bp = Blueprint('hub_v1', __name__)


@bp.route('/storage', methods=['GET'])
@login_required
def get_storage_info():
    """
    获取用户存储配额信息

    Request:
        GET /api/v1/hub/storage

    Response:
        {
            "success": true,
            "data": {
                "storage_used": 1048576,      // 已用存储（字节）
                "storage_quota": 209715200,   // 存储配额（字节）
                "storage_percentage": 0.5     // 使用百分比
            }
        }
    """
    try:
        info = HubService.get_storage_info(g.user_id, db_session.session)
        return success_response(info)
    except ValueError as e:
        return error_response('USER_NOT_FOUND', str(e), 404)


@bp.route('/media', methods=['GET'])
@login_required
def get_user_media():
    """
    获取用户私有媒体文件列表

    Request:
        GET /api/v1/hub/media?page=1&page_size=20&visibility=private&type=image

    Query Params:
        page: 页码（默认1）
        page_size: 每页数量（默认20，最大100）
        visibility: 可见性筛选（private/public，不传则返回全部）
        type: 媒体类型筛选（image/video，不传则返回全部）

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
    page_size = min(request.args.get('page_size', 20, type=int), 100)
    visibility = request.args.get('visibility')
    media_type = request.args.get('type')

    # 验证参数
    if visibility and visibility not in ['private', 'public']:
        return error_response('INVALID_PARAMS', 'visibility 必须是 private 或 public', 400)
    if media_type and media_type not in ['image', 'video']:
        return error_response('INVALID_PARAMS', 'type 必须是 image 或 video', 400)

    result = HubService.get_user_media(
        g.user_id,
        db_session.session,
        page,
        page_size,
        visibility,
        media_type
    )

    items = [m.to_dict(include_uploader=True) for m in result['items']]
    return pagination_response(
        items,
        result['page'],
        result['page_size'],
        result['total']
    )


@bp.route('/resources', methods=['GET'])
@login_required
def get_user_resources():
    """
    获取用户私有资源文件列表

    Request:
        GET /api/v1/hub/resources?page=1&page_size=20&visibility=private

    Query Params:
        page: 页码（默认1）
        page_size: 每页数量（默认20，最大100）
        visibility: 可见性筛选（private/public，不传则返回全部）

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
    page_size = min(request.args.get('page_size', 20, type=int), 100)
    visibility = request.args.get('visibility')

    # 验证参数
    if visibility and visibility not in ['private', 'public']:
        return error_response('INVALID_PARAMS', 'visibility 必须是 private 或 public', 400)

    result = HubService.get_user_resources(
        g.user_id,
        db_session.session,
        page,
        page_size,
        visibility
    )

    items = [r.to_dict() for r in result['items']]
    return pagination_response(
        items,
        result['page'],
        result['page_size'],
        result['total']
    )


@bp.route('/media/<int:media_id>/visibility', methods=['PATCH'])
@login_required
def toggle_media_visibility(media_id: int):
    """
    切换媒体文件可见性（私有 ↔ 公共）

    Request:
        PATCH /api/v1/hub/media/:id/visibility

    Response:
        {
            "success": true,
            "data": {
                "visibility": "public"  // 或 "private"
            }
        }
    """
    try:
        new_visibility = HubService.toggle_media_visibility(g.user_id, media_id, db_session.session)
        return success_response({'visibility': new_visibility}, '切换成功')
    except ValueError as e:
        return error_response('MEDIA_NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/resources/<int:resource_id>/visibility', methods=['PATCH'])
@login_required
def toggle_resource_visibility(resource_id: int):
    """
    切换资源文件可见性（私有 ↔ 公共）

    Request:
        PATCH /api/v1/hub/resources/:id/visibility

    Response:
        {
            "success": true,
            "data": {
                "visibility": "public"  // 或 "private"
            }
        }
    """
    try:
        new_visibility = HubService.toggle_resource_visibility(g.user_id, resource_id, db_session.session)
        return success_response({'visibility': new_visibility}, '切换成功')
    except ValueError as e:
        return error_response('RESOURCE_NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/public/media', methods=['GET'])
def get_public_media():
    """
    获取公共媒体文件列表（供公共大厅使用）

    Request:
        GET /api/v1/hub/public/media?page=1&page_size=20&type=image

    Query Params:
        page: 页码（默认1）
        page_size: 每页数量（默认20，最大100）
        type: 媒体类型筛选（image/video，不传则返回全部）

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
    page_size = min(request.args.get('page_size', 20, type=int), 100)
    media_type = request.args.get('type')

    # 验证参数
    if media_type and media_type not in ['image', 'video']:
        return error_response('INVALID_PARAMS', 'type 必须是 image 或 video', 400)

    result = HubService.get_published_media(
        db_session.session,
        page,
        page_size,
        media_type
    )

    items = [m.to_dict(include_uploader=True) for m in result['items']]
    return pagination_response(
        items,
        result['page'],
        result['page_size'],
        result['total']
    )


@bp.route('/public/resources', methods=['GET'])
def get_public_resources():
    """
    获取公共资源文件列表（供公共大厅使用）

    Request:
        GET /api/v1/hub/public/resources?page=1&page_size=20

    Query Params:
        page: 页码（默认1）
        page_size: 每页数量（默认20，最大100）

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
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    result = HubService.get_published_resources(
        db_session.session,
        page,
        page_size
    )

    items = [r.to_dict(include_uploader=True) for r in result['items']]
    return pagination_response(
        items,
        result['page'],
        result['page_size'],
        result['total']
    )
