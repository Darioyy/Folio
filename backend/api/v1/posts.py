"""
文章 API 路由 - RESTful API
"""

import os
from flask import Blueprint, request, g, send_file, session as flask_session
from pydantic import ValidationError
from core.services.post_service import PostService
from core.schemas.post import PostCreate, PostUpdate, PostListQuery, PostAttachmentAdd
from core.utils.validators import login_required
from core.utils.response import success_response, error_response
from config.default import Config

posts_bp = Blueprint("posts", __name__)


@posts_bp.route("", methods=["GET"])
def get_posts():
    """获取文章列表 GET /api/v1/posts"""
    try:
        query_schema = PostListQuery(
            page=int(request.args.get("page", 1)),
            limit=int(request.args.get("limit", 10)),
            status=request.args.get("status", "published"),
            category_id=(int(request.args.get("category_id")) if request.args.get("category_id") else None),
            search=request.args.get("search", ""),
        )
        sort = request.args.get("sort", "latest")
        result = PostService.get_posts(
            page=query_schema.page, limit=query_schema.limit,
            status=query_schema.status, category_id=query_schema.category_id,
            search=query_schema.search, sort=sort,
        )
        return success_response(data=result)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@posts_bp.route("/my", methods=["GET"])
@login_required
def get_my_posts():
    """获取我的博文列表 GET /api/v1/posts/my"""
    try:
        status = request.args.get("status", "all")
        page = int(request.args.get("page", 1))
        page_size = min(int(request.args.get("page_size", 20)), 100)
        result = PostService.get_my_posts(author_id=g.user_id, page=page, page_size=page_size, status=status)
        return success_response(data=result)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@posts_bp.route("/admin/all", methods=["GET"])
@login_required
def admin_get_all_posts():
    """管理员获取所有博文列表 GET /api/v1/posts/admin/all"""
    if not (flask_session.get('is_admin') or flask_session.get('is_root')):
        return error_response(code="FORBIDDEN", message="需要管理员权限", http_code=403)

    page = int(request.args.get("page", 1))
    page_size = min(int(request.args.get("page_size", 20)), 100)
    username = request.args.get("username", "").strip()
    category_id = request.args.get("category_id", None, type=int)
    status = request.args.get("status", "").strip()

    author_id = None
    if username:
        from core.models.user import User as UserModel
        user_obj = UserModel.query.filter_by(username=username).first()
        if not user_obj:
            return success_response({"items": [], "total": 0, "page": page, "page_size": page_size, "pages": 0})
        author_id = user_obj.id

    result = PostService.get_posts(
        page=page,
        limit=page_size,
        status=status if status else "published",
        category_id=category_id,
        author_id=author_id,
        admin_view=True,
    )

    pagination = result.get("pagination", {})
    return success_response({
        "items": result.get("items", []),
        "total": pagination.get("total", 0),
        "page": pagination.get("page", page),
        "page_size": pagination.get("page_size", page_size),
        "pages": pagination.get("pages", 1),
    })


@posts_bp.route("/following", methods=["GET"])
@login_required
def get_following_posts():
    """获取关注用户的博文 GET /api/v1/posts/following"""
    try:
        page = int(request.args.get("page", 1))
        page_size = min(int(request.args.get("page_size", 20)), 50)
        result = PostService.get_following_posts(user_id=g.user_id, page=page, page_size=page_size)
        return success_response(data=result)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@posts_bp.route("/<int:post_id>", methods=["GET"])
def get_post(post_id):
    """获取文章详情 GET /api/v1/posts/:id"""
    try:
        # 构造 viewer_key 用于浏览量去重
        user_id = flask_session.get("user_id")
        if user_id:
            viewer_key = f"user:{user_id}"
        else:
            # 匿名用户用 session 标识
            if "_vk" not in flask_session:
                import uuid
                flask_session["_vk"] = str(uuid.uuid4())[:16]
            viewer_key = f"anon:{flask_session['_vk']}"
        post = PostService.get_post_by_id(post_id, increment_view=True, viewer_key=viewer_key)
        return success_response(data=post)
    except ValueError as e:
        return error_response(code="NOT_FOUND", message=str(e), http_code=404)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@posts_bp.route("", methods=["POST"])
@login_required
def create_post():
    """创建文章 POST /api/v1/posts"""
    try:
        data = request.get_json()
        if not data:
            return error_response(code="BAD_REQUEST", message="请求体不能为空", http_code=400)
        schema = PostCreate(**data)
        post = PostService.create_post(
            author_id=g.user_id,
            title=schema.title, content=schema.content, summary=schema.summary,
            category_id=schema.category_id, cover_image_id=schema.cover_image_id,
            status=schema.status,
        )
        return success_response(data=post, message="文章创建成功", code=201)
    except (ValidationError, ValueError) as e:
        return error_response(code="BAD_REQUEST", message=str(e), http_code=400)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@posts_bp.route("/<int:post_id>", methods=["PUT"])
@login_required
def update_post(post_id):
    """更新文章 PUT /api/v1/posts/:id"""
    try:
        data = request.get_json()
        if not data:
            return error_response(code="BAD_REQUEST", message="请求体不能为空", http_code=400)
        schema = PostUpdate(**data)
        update_data = schema.model_dump(exclude_unset=True)
        if not update_data:
            return error_response(code="BAD_REQUEST", message="没有可更新的字段", http_code=400)
        post = PostService.update_post(post_id=post_id, operator_id=g.user_id, **update_data)
        return success_response(data=post, message="文章更新成功")
    except PermissionError as e:
        return error_response(code="FORBIDDEN", message=str(e), http_code=403)
    except (ValidationError, ValueError) as e:
        return error_response(code="BAD_REQUEST", message=str(e), http_code=400)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@posts_bp.route("/<int:post_id>/publish", methods=["POST"])
@login_required
def publish_post(post_id):
    """发布博文 POST /api/v1/posts/:id/publish"""
    try:
        post = PostService.publish_post(post_id=post_id, operator_id=g.user_id)
        return success_response(data=post, message="博文发布成功")
    except PermissionError as e:
        return error_response(code="FORBIDDEN", message=str(e), http_code=403)
    except ValueError as e:
        return error_response(code="BAD_REQUEST", message=str(e), http_code=400)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@posts_bp.route("/<int:post_id>", methods=["DELETE"])
@login_required
def delete_post(post_id):
    """删除文章 DELETE /api/v1/posts/:id"""
    try:
        PostService.delete_post(post_id=post_id, operator_id=g.user_id)
        return success_response(message="文章删除成功")
    except PermissionError as e:
        return error_response(code="FORBIDDEN", message=str(e), http_code=403)
    except ValueError as e:
        return error_response(code="NOT_FOUND", message=str(e), http_code=404)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


# ============================================================
# 附件端点
# ============================================================

@posts_bp.route("/<int:post_id>/attachments", methods=["GET"])
def get_attachments(post_id):
    """获取附件列表 GET /api/v1/posts/:id/attachments"""
    try:
        attachments = PostService.get_attachments(post_id)
        return success_response(data=attachments)
    except ValueError as e:
        return error_response(code="NOT_FOUND", message=str(e), http_code=404)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@posts_bp.route("/<int:post_id>/attachments", methods=["POST"])
@login_required
def add_attachment(post_id):
    """添加附件 POST /api/v1/posts/:id/attachments"""
    try:
        data = request.get_json()
        if not data:
            return error_response(code="BAD_REQUEST", message="请求体不能为空", http_code=400)
        schema = PostAttachmentAdd(**data)
        attachment = PostService.add_attachment(post_id=post_id, file_id=schema.file_id, operator_id=g.user_id)
        return success_response(data=attachment, message="附件添加成功", code=201)
    except PermissionError as e:
        return error_response(code="FORBIDDEN", message=str(e), http_code=403)
    except (ValidationError, ValueError) as e:
        return error_response(code="BAD_REQUEST", message=str(e), http_code=400)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@posts_bp.route("/<int:post_id>/attachments/<int:file_id>", methods=["DELETE"])
@login_required
def remove_attachment(post_id, file_id):
    """移除附件 DELETE /api/v1/posts/:id/attachments/:file_id"""
    try:
        PostService.remove_attachment(post_id=post_id, file_id=file_id, operator_id=g.user_id)
        return success_response(message="附件已移除")
    except PermissionError as e:
        return error_response(code="FORBIDDEN", message=str(e), http_code=403)
    except ValueError as e:
        return error_response(code="NOT_FOUND", message=str(e), http_code=404)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


# ============================================================
# 可见性管理（管理员）
# ============================================================

@posts_bp.route("/<int:post_id>/visibility", methods=["PUT"])
@login_required
def set_post_visibility(post_id):
    """PUT /api/v1/posts/:id/visibility — 管理员设置博文可见性"""
    from core.models.post import Post
    from core.models.notification import Notification as NotifModel
    from db.session import db as db_session

    if not (flask_session.get('is_admin') or flask_session.get('is_root')):
        return error_response('FORBIDDEN', '无权操作', 403)

    post = db_session.session.get(Post, post_id)
    if not post or post.status != 'published':
        return error_response('NOT_FOUND', '博文不存在', 404)

    data = request.get_json() or {}
    hidden = bool(data.get('hidden', False))
    reason = str(data.get('reason', '')).strip()

    post.is_hidden = 1 if hidden else 0
    if hidden:
        post.hide_reason = reason or '违反社区规范'
        post.review_status = 'none'
        post.appeal_reason = None
    else:
        # 恢复公开时清除审核状态
        post.hide_reason = None
        post.review_status = 'none'
        post.appeal_reason = None

    db_session.session.commit()

    # 隐藏时发通知给作者
    if hidden and post.author_id != g.user_id:
        notif = NotifModel(
            user_id=post.author_id,
            type='admin',
            actor_id=g.user_id,
            target_id=post_id,
            extra={'action': 'hide', 'reason': post.hide_reason, 'post_title': post.title}
        )
        db_session.session.add(notif)
        db_session.session.commit()

    return success_response({'is_hidden': post.is_hidden}, message='操作成功')


# ============================================================
# 申诉系统（作者申诉 + 管理员审核）
# ============================================================

@posts_bp.route("/<int:post_id>/appeal", methods=["POST"])
@login_required
def appeal_post(post_id):
    """POST /api/v1/posts/:id/appeal — 作者提交申诉"""
    from core.models.post import Post
    from core.models.notification import Notification as NotifModel
    from db.session import db as db_session

    post = db_session.session.get(Post, post_id)
    if not post:
        return error_response('NOT_FOUND', '博文不存在', 404)
    if post.author_id != g.user_id:
        return error_response('FORBIDDEN', '只有作者可以申诉', 403)
    if not post.is_hidden:
        return error_response('BAD_REQUEST', '博文未被隐藏，无需申诉', 400)
    if post.review_status == 'pending':
        return error_response('BAD_REQUEST', '申诉已提交，正在审核中', 400)

    data = request.get_json() or {}
    appeal_reason = str(data.get('reason', '')).strip()
    if not appeal_reason:
        return error_response('BAD_REQUEST', '请填写申诉理由', 400)

    post.review_status = 'pending'
    post.appeal_reason = appeal_reason
    db_session.session.commit()

    # 通知所有管理员/root（取第一个 admin）
    try:
        from core.models.user import User as UserModel
        admins = UserModel.query.filter(
            (UserModel.is_admin == 1) | (UserModel.is_root == 1)
        ).all()
        for admin in admins:
            if admin.id != g.user_id:
                notif = NotifModel(
                    user_id=admin.id,
                    type='appeal',
                    actor_id=g.user_id,
                    target_id=post_id,
                    extra={'post_title': post.title, 'appeal_reason': appeal_reason}
                )
                db_session.session.add(notif)
        db_session.session.commit()
    except Exception:
        pass

    return success_response({'review_status': post.review_status}, message='申诉已提交，等待审核')


@posts_bp.route("/<int:post_id>/review", methods=["PUT"])
@login_required
def review_appeal(post_id):
    """PUT /api/v1/posts/:id/review — 管理员审核申诉"""
    from core.models.post import Post
    from core.models.notification import Notification as NotifModel
    from db.session import db as db_session

    if not (flask_session.get('is_admin') or flask_session.get('is_root')):
        return error_response('FORBIDDEN', '无权操作', 403)

    post = db_session.session.get(Post, post_id)
    if not post:
        return error_response('NOT_FOUND', '博文不存在', 404)
    if post.review_status != 'pending':
        return error_response('BAD_REQUEST', '该博文没有待审核的申诉', 400)

    data = request.get_json() or {}
    action = data.get('action', '')  # 'approve' | 'reject'
    reject_reason = str(data.get('reason', '')).strip()

    if action == 'approve':
        post.is_hidden = 0
        post.review_status = 'none'
        post.hide_reason = None
        post.appeal_reason = None
        db_session.session.commit()
        # 通知作者：申诉通过
        notif = NotifModel(
            user_id=post.author_id,
            type='review_result',
            actor_id=g.user_id,
            target_id=post_id,
            extra={'action': 'approved', 'post_title': post.title}
        )
        db_session.session.add(notif)
        db_session.session.commit()
        return success_response({'review_status': 'none', 'is_hidden': 0}, message='已批准申诉，博文已恢复')

    elif action == 'reject':
        post.review_status = 'rejected'
        if reject_reason:
            post.hide_reason = reject_reason
        db_session.session.commit()
        # 通知作者：申诉被拒绝
        notif = NotifModel(
            user_id=post.author_id,
            type='review_result',
            actor_id=g.user_id,
            target_id=post_id,
            extra={'action': 'rejected', 'reason': reject_reason or post.hide_reason, 'post_title': post.title}
        )
        db_session.session.add(notif)
        db_session.session.commit()
        return success_response({'review_status': 'rejected', 'is_hidden': 1}, message='已拒绝申诉')

    else:
        return error_response('BAD_REQUEST', 'action 必须为 approve 或 reject', 400)


# ============================================================
# 附件下载
# ============================================================

@posts_bp.route("/<int:post_id>/attachments/<int:file_id>/download", methods=["GET"])
def download_attachment(post_id, file_id):
    """下载附件 GET /api/v1/posts/:id/attachments/:file_id/download"""
    try:
        from core.models.post import Post

        post = Post.query.get(post_id)
        if not post:
            return error_response(code="NOT_FOUND", message="文章不存在", http_code=404)

        if post.status != 'published':
            current_user_id = flask_session.get('user_id')
            if not current_user_id or current_user_id != post.author_id:
                return error_response(code="FORBIDDEN", message="无权访问", http_code=403)

        f = PostService.get_attachment_file(post_id, file_id)
        if not f:
            return error_response(code="NOT_FOUND", message="附件不存在", http_code=404)

        uploads_dir = os.path.abspath(Config.UPLOAD_FOLDER)
        file_abs = os.path.join(uploads_dir, f.file_path)
        if not os.path.exists(file_abs):
            return error_response(code="NOT_FOUND", message="文件不存在", http_code=404)

        return send_file(file_abs, as_attachment=True, download_name=f.file_name)

    except ValueError as e:
        return error_response(code="NOT_FOUND", message=str(e), http_code=404)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)
