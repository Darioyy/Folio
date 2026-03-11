"""
点赞 / 收藏 API
"""
from flask import Blueprint, request, g, session

from core.services.interaction_service import interaction_service
from core.services.notification_service import notification_service
from core.models.file import File
from db.session import db as db_session
from core.utils.validators import login_required
from core.utils.response import success_response, error_response, pagination_response

bp = Blueprint('interactions_v1', __name__)


@bp.route('/<int:file_id>/like', methods=['POST'])
@login_required
def like_file(file_id: int):
    """POST /api/v1/files/:id/like — 点赞/取消点赞"""
    try:
        result = interaction_service.toggle_like(g.user_id, file_id)
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)

    # 通知文件所有者（点赞时）
    if result['liked']:
        file = db_session.session.get(File, file_id)
        if file:
            try:
                notification_service.create(
                    user_id=file.user_id,
                    type_='like',
                    actor_id=g.user_id,
                    target_id=file_id,
                    extra={'file_title': file.title}
                )
            except Exception:
                pass

    return success_response(result)


@bp.route('/<int:file_id>/collect', methods=['POST'])
@login_required
def collect_file(file_id: int):
    """POST /api/v1/files/:id/collect — 收藏/取消收藏"""
    try:
        result = interaction_service.toggle_collect(g.user_id, file_id)
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)

    return success_response(result)


@bp.route('/batch-status', methods=['GET'])
@login_required
def batch_status():
    """GET /api/v1/files/batch-status?ids=1,2,3"""
    ids_param = request.args.get('ids', '')
    if not ids_param:
        return success_response({})
    try:
        file_ids = [int(x) for x in ids_param.split(',') if x.strip()]
    except ValueError:
        return error_response('INVALID_PARAMS', 'ids 格式错误', 400)

    status = interaction_service.batch_status(g.user_id, file_ids)
    return success_response(status)


@bp.route('/me/collections', methods=['GET'])
@login_required
def my_collections():
    """GET /api/v1/files/me/collections — 获取我的收藏列表"""
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    result = interaction_service.get_user_collections(g.user_id, page, page_size)
    return pagination_response(result['items'], result['page'], result['page_size'], result['total'])
