"""
通知 API
"""
from flask import Blueprint, request, g

from core.services.notification_service import notification_service
from core.utils.validators import login_required
from core.utils.response import success_response, error_response, pagination_response

bp = Blueprint('notifications_v1', __name__)


@bp.route('', methods=['GET'])
@login_required
def get_notifications():
    """GET /api/v1/notifications — 获取当前用户通知列表"""
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 50)

    result = notification_service.get_notifications(g.user_id, page, page_size)
    return pagination_response(result['items'], result['page'], result['page_size'], result['total'])


@bp.route('/unread-count', methods=['GET'])
@login_required
def unread_count():
    """GET /api/v1/notifications/unread-count"""
    count = notification_service.get_unread_count(g.user_id)
    return success_response({'count': count})


@bp.route('/read-all', methods=['PUT'])
@login_required
def read_all():
    """PUT /api/v1/notifications/read-all"""
    notification_service.mark_all_read(g.user_id)
    return success_response(message='已全部标为已读')


@bp.route('/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id: int):
    """DELETE /api/v1/notifications/:id"""
    try:
        notification_service.delete_notification(notification_id, g.user_id)
        return success_response(message='删除成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
