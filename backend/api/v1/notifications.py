"""
通知 API
"""
from flask import Blueprint, request, g

from db.session import db as db_session
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


@bp.route('/<int:notification_id>/read', methods=['PUT'])
@login_required
def read_one(notification_id: int):
    """PUT /api/v1/notifications/:id/read — 标记单条通知为已读"""
    from core.models.notification import Notification as NotifModel
    notif = db_session.session.get(NotifModel, notification_id)
    if notif and notif.user_id == g.user_id and not notif.is_read:
        notif.is_read = 1
        db_session.session.commit()
    return success_response(message='已读')


@bp.route('/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id: int):
    """DELETE /api/v1/notifications/:id"""
    try:
        notification_service.delete_notification(notification_id, g.user_id)
        return success_response(message='删除成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)


@bp.route('', methods=['DELETE'])
@login_required
def clear_all_notifications():
    """DELETE /api/v1/notifications — 清除当前用户所有通知"""
    from core.models.notification import Notification as NotifModel
    from sqlalchemy import delete as sql_delete
    try:
        db_session.session.execute(
            sql_delete(NotifModel).where(NotifModel.user_id == g.user_id)
        )
        db_session.session.commit()
        return success_response(message='通知已清除')
    except Exception as e:
        return error_response('INTERNAL_ERROR', str(e), 500)
