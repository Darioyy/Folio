"""
反馈/建议 API
POST /api/v1/feedback  — 登录用户提交反馈
GET  /api/v1/feedback  — Root 查看反馈列表
"""
from flask import Blueprint, request, g
from sqlalchemy import select, func
from core.models.feedback import Feedback
from core.utils.validators import login_required, root_required
from core.utils.response import success_response, error_response
from db.session import db as db_session

feedback_bp = Blueprint("feedback", __name__)

_VALID_TYPES = {"suggestion", "bug", "other"}


@feedback_bp.route("", methods=["POST"])
@login_required
def submit_feedback():
    """POST /api/v1/feedback — 提交建议/反馈"""
    data = request.get_json() or {}
    type_ = data.get("type", "suggestion")
    content = str(data.get("content", "")).strip()

    if type_ not in _VALID_TYPES:
        type_ = "other"
    if not content:
        return error_response("BAD_REQUEST", "反馈内容不能为空", 400)
    if len(content) > 2000:
        return error_response("BAD_REQUEST", "反馈内容不能超过 2000 字", 400)

    fb = Feedback(user_id=g.user_id, type=type_, content=content)
    db_session.session.add(fb)
    db_session.session.commit()

    # 通知所有 Root 用户
    try:
        from core.models.user import User
        from core.models.notification import Notification
        roots = db_session.session.execute(
            select(User).where(User.is_root == 1)
        ).scalars().all()
        for root in roots:
            if root.id != g.user_id:
                notif = Notification(
                    user_id=root.id,
                    type="admin",
                    actor_id=g.user_id,
                    target_id=fb.id,
                    extra={"action": "new_feedback", "feedback_type": type_},
                )
                db_session.session.add(notif)
        db_session.session.commit()
    except Exception:
        pass

    return success_response(data={"id": fb.id}, message="反馈已提交，感谢您的建议", code=201)


@feedback_bp.route("", methods=["GET"])
@root_required
def list_feedback():
    """GET /api/v1/feedback — Root 查看反馈列表"""
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 20, type=int), 100)
    status = request.args.get("status", "")

    where_clauses = []
    if status in ("pending", "resolved"):
        where_clauses.append(Feedback.status == status)

    total = db_session.session.execute(
        select(func.count(Feedback.id)).where(*where_clauses)
    ).scalar() or 0

    items = db_session.session.execute(
        select(Feedback)
        .where(*where_clauses)
        .order_by(Feedback.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    return success_response({
        "items": [fb.to_dict() for fb in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    })


@feedback_bp.route("/<int:feedback_id>", methods=["PATCH"])
@root_required
def update_feedback_status(feedback_id):
    """PATCH /api/v1/feedback/:id — Root 标记处理状态"""
    data = request.get_json() or {}
    status = data.get("status", "")
    if status not in ("pending", "resolved"):
        return error_response("BAD_REQUEST", "status 必须为 pending 或 resolved", 400)

    fb = db_session.session.get(Feedback, feedback_id)
    if not fb:
        return error_response("NOT_FOUND", "反馈不存在", 404)

    fb.status = status
    db_session.session.commit()
    return success_response({"id": fb.id, "status": fb.status}, message="状态已更新")
