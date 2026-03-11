"""
评论 API
"""
from flask import Blueprint, request, g, session

from core.services.comment_service import comment_service
from core.services.notification_service import notification_service
from core.models.file import File
from core.models.comment import Comment
from db.session import db as db_session
from core.utils.validators import login_required
from core.utils.response import success_response, error_response, pagination_response

bp = Blueprint('comments_v1', __name__)


@bp.route('/files/<int:file_id>/comments', methods=['GET'])
def get_comments(file_id: int):
    """GET /api/v1/files/:id/comments — 获取评论列表"""
    file = db_session.session.get(File, file_id)
    if not file:
        return error_response('NOT_FOUND', '文件不存在', 404)
    # 私有文件：仅所有者或管理员可查看评论
    if file.visibility == 'private':
        current_user_id = getattr(g, 'user_id', None)
        is_admin = bool(session.get('is_admin') or session.get('is_root'))
        if not is_admin and current_user_id != file.user_id:
            return error_response('FORBIDDEN', '无权访问此文件的评论', 403)

    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    result = comment_service.get_comments(file_id, page, page_size)
    return pagination_response(result['items'], result['page'], result['page_size'], result['total'])


@bp.route('/files/<int:file_id>/comments', methods=['POST'])
@login_required
def create_comment(file_id: int):
    """POST /api/v1/files/:id/comments — 发表评论"""
    body = request.get_json() or {}
    content = body.get('content', '').strip()
    parent_id = body.get('parent_id')

    if not content:
        return error_response('INVALID_PARAMS', '评论内容不能为空', 400)
    if len(content) > 500:
        return error_response('INVALID_PARAMS', '评论内容不能超过 500 字', 400)

    try:
        comment = comment_service.create_comment(file_id, g.user_id, content, parent_id)
    except ValueError as e:
        return error_response('INVALID_PARAMS', str(e), 400)

    # 发通知
    file = db_session.session.get(File, file_id)
    if file:
        try:
            if parent_id is not None:
                # 回复：通知父评论作者
                parent_comment = db_session.session.get(Comment, parent_id)
                if parent_comment:
                    notification_service.create(
                        user_id=parent_comment.user_id,
                        type_='reply',
                        actor_id=g.user_id,
                        target_id=comment.id,
                        extra={'file_id': file_id, 'file_title': file.title, 'content': content[:50]}
                    )
            else:
                # 根评论：通知文件所有者
                notification_service.create(
                    user_id=file.user_id,
                    type_='comment',
                    actor_id=g.user_id,
                    target_id=comment.id,
                    extra={'file_id': file_id, 'file_title': file.title, 'content': content[:50]}
                )
        except Exception:
            pass

    return success_response(comment.to_dict(include_user=True), '评论成功', 201)


@bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id: int):
    """DELETE /api/v1/comments/:id — 删除评论"""
    is_admin = bool(session.get('is_admin') or session.get('is_root'))
    try:
        comment_service.delete_comment(comment_id, g.user_id, is_admin)
        return success_response(message='删除成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)
