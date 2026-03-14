"""
博文互动 API（点赞 / 收藏 / 评论）
注册在 /api/v1/posts 前缀下
"""
from flask import Blueprint, request, g, session as flask_session
from core.services.interaction_service import InteractionService
from core.services.comment_service import CommentService
from core.utils.validators import login_required
from core.utils.response import success_response, error_response
from core.utils.permissions import get_user_role
from db.session import db as db_session

bp = Blueprint("post_interactions", __name__)


@bp.route("/me/collections", methods=["GET"])
@login_required
def get_my_collections():
    """GET /api/v1/posts/me/collections — 我收藏的博文列表
    folder_id 参数说明：
      未传      → 返回全部收藏
      folder_id=0  → 返回未分类收藏（folder_id IS NULL）
      folder_id=N  → 返回指定收藏夹
    """
    try:
        page = int(request.args.get("page", 1))
        page_size = min(int(request.args.get("page_size", 20)), 100)
        folder_id_raw = request.args.get("folder_id", "")
        # 空字符串 → 不过滤；"0" → 未分类；正整数字符串 → 指定收藏夹
        folder_id = None
        if folder_id_raw != "":
            folder_id = int(folder_id_raw) if (folder_id_raw.isdigit() or folder_id_raw == "0") else None
        result = InteractionService.get_user_collections(
            user_id=g.user_id, page=page, page_size=page_size, folder_id=folder_id
        )
        return success_response(data=result)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@bp.route("/<int:post_id>/status", methods=["GET"])
def get_interaction_status(post_id):
    """GET /api/v1/posts/:id/status"""
    try:
        user_id = flask_session.get('user_id')
        if not user_id:
            return success_response(data={'liked': False, 'collected': False})
        result = InteractionService.batch_status(user_id=user_id, post_ids=[post_id])
        status = result.get(post_id, {'liked': False, 'collected': False})
        return success_response(data=status)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@bp.route("/<int:post_id>/like", methods=["POST"])
@login_required
def toggle_like(post_id):
    """POST /api/v1/posts/:id/like"""
    try:
        result = InteractionService.toggle_like(user_id=g.user_id, post_id=post_id)
        return success_response(data=result)
    except ValueError as e:
        return error_response(code="NOT_FOUND", message=str(e), http_code=404)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@bp.route("/<int:post_id>/collect", methods=["POST"])
@login_required
def toggle_collect(post_id):
    """POST /api/v1/posts/:id/collect"""
    try:
        result = InteractionService.toggle_collect(user_id=g.user_id, post_id=post_id)
        return success_response(data=result)
    except ValueError as e:
        return error_response(code="NOT_FOUND", message=str(e), http_code=404)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@bp.route("/<int:post_id>/comments", methods=["GET"])
def get_comments(post_id):
    """GET /api/v1/posts/:id/comments"""
    try:
        from core.models.post import Post
        post = Post.query.get(post_id)
        if not post:
            return error_response(code="NOT_FOUND", message="博文不存在", http_code=404)
        if post.status != 'published':
            current_user_id = flask_session.get('user_id')
            if not current_user_id or current_user_id != post.author_id:
                return error_response(code="FORBIDDEN", message="无权访问", http_code=403)
        page = int(request.args.get("page", 1))
        page_size = min(int(request.args.get("page_size", 20)), 100)
        viewer_id = flask_session.get('user_id')
        result = CommentService.get_comments(post_id=post_id, page=page, page_size=page_size, viewer_id=viewer_id)
        return success_response(data=result)
    except ValueError as e:
        return error_response(code="NOT_FOUND", message=str(e), http_code=404)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@bp.route("/<int:post_id>/comments", methods=["POST"])
@login_required
def create_comment(post_id):
    """POST /api/v1/posts/:id/comments"""
    try:
        data = request.get_json() or {}
        content = data.get("content", "").strip()
        if not content:
            return error_response(code="BAD_REQUEST", message="评论内容不能为空", http_code=400)
        if len(content) > 500:
            return error_response(code="BAD_REQUEST", message="评论内容不能超过500字", http_code=400)
        parent_id = data.get("parent_id")
        comment = CommentService.create_comment(
            post_id=post_id, user_id=g.user_id, content=content, parent_id=parent_id,
        )
        return success_response(data=comment.to_dict(include_user=True), message="评论成功", code=201)
    except PermissionError as e:
        return error_response(code="FORBIDDEN", message=str(e), http_code=403)
    except ValueError as e:
        return error_response(code="BAD_REQUEST", message=str(e), http_code=400)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@bp.route("/comments/<int:comment_id>", methods=["PATCH"])
@login_required
def update_comment(comment_id):
    """PATCH /api/v1/posts/comments/:comment_id — 编辑评论（仅作者）"""
    try:
        data = request.get_json() or {}
        content = data.get("content", "").strip()
        if not content:
            return error_response(code="BAD_REQUEST", message="评论内容不能为空", http_code=400)
        if len(content) > 500:
            return error_response(code="BAD_REQUEST", message="评论内容不能超过500字", http_code=400)
        comment = CommentService.update_comment(comment_id=comment_id, user_id=g.user_id, content=content)
        return success_response(data=comment.to_dict(include_user=True), message="评论已更新")
    except PermissionError as e:
        return error_response(code="FORBIDDEN", message=str(e), http_code=403)
    except ValueError as e:
        return error_response(code="NOT_FOUND", message=str(e), http_code=404)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@login_required
def delete_comment(comment_id):
    """DELETE /api/v1/posts/comments/:comment_id"""
    try:
        operator_role = get_user_role(g.user_id, db_session.session)
        is_admin = operator_role >= 1
        CommentService.delete_comment(comment_id=comment_id, operator_id=g.user_id, is_admin=is_admin)
        return success_response(message="评论已删除")
    except PermissionError as e:
        return error_response(code="FORBIDDEN", message=str(e), http_code=403)
    except ValueError as e:
        return error_response(code="NOT_FOUND", message=str(e), http_code=404)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@bp.route("/comments/<int:comment_id>/like", methods=["POST"])
@login_required
def toggle_comment_like(comment_id):
    """POST /api/v1/posts/comments/:comment_id/like"""
    try:
        result = CommentService.toggle_comment_like(user_id=g.user_id, comment_id=comment_id)
        return success_response(data=result)
    except ValueError as e:
        return error_response(code="NOT_FOUND", message=str(e), http_code=404)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


# ============================================================
# 收藏夹管理
# ============================================================

@bp.route("/me/collections/folders", methods=["GET"])
@login_required
def get_collection_folders():
    """GET /api/v1/posts/me/collections/folders — 获取我的收藏夹列表"""
    try:
        from core.models.interaction import CollectionFolder
        folders = CollectionFolder.query.filter_by(user_id=g.user_id).order_by(CollectionFolder.created_at.asc()).all()
        return success_response(data=[f.to_dict() for f in folders])
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@bp.route("/me/collections/folders", methods=["POST"])
@login_required
def create_collection_folder():
    """POST /api/v1/posts/me/collections/folders — 新建收藏夹"""
    try:
        from core.models.interaction import CollectionFolder
        data = request.get_json() or {}
        name = str(data.get("name", "")).strip()
        if not name:
            return error_response(code="BAD_REQUEST", message="收藏夹名称不能为空", http_code=400)
        if len(name) > 100:
            return error_response(code="BAD_REQUEST", message="收藏夹名称不能超过100字", http_code=400)
        folder = CollectionFolder(user_id=g.user_id, name=name)
        db_session.session.add(folder)
        db_session.session.commit()
        db_session.session.refresh(folder)
        return success_response(data=folder.to_dict(), message="收藏夹创建成功", code=201)
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@bp.route("/me/collections/folders/<int:folder_id>", methods=["PUT"])
@login_required
def update_collection_folder(folder_id):
    """PUT /api/v1/posts/me/collections/folders/:id — 重命名收藏夹"""
    try:
        from core.models.interaction import CollectionFolder
        folder = CollectionFolder.query.get(folder_id)
        if not folder:
            return error_response(code="NOT_FOUND", message="收藏夹不存在", http_code=404)
        if folder.user_id != g.user_id:
            return error_response(code="FORBIDDEN", message="没有权限操作此收藏夹", http_code=403)
        data = request.get_json() or {}
        name = str(data.get("name", "")).strip()
        if not name:
            return error_response(code="BAD_REQUEST", message="收藏夹名称不能为空", http_code=400)
        if len(name) > 100:
            return error_response(code="BAD_REQUEST", message="收藏夹名称不能超过100字", http_code=400)
        folder.name = name
        db_session.session.commit()
        return success_response(data=folder.to_dict(), message="收藏夹已更新")
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@bp.route("/me/collections/folders/<int:folder_id>", methods=["DELETE"])
@login_required
def delete_collection_folder(folder_id):
    """DELETE /api/v1/posts/me/collections/folders/:id — 删除收藏夹（收藏记录保留，folder_id 置 NULL）"""
    try:
        from core.models.interaction import CollectionFolder
        folder = CollectionFolder.query.get(folder_id)
        if not folder:
            return error_response(code="NOT_FOUND", message="收藏夹不存在", http_code=404)
        if folder.user_id != g.user_id:
            return error_response(code="FORBIDDEN", message="没有权限操作此收藏夹", http_code=403)
        db_session.session.delete(folder)
        db_session.session.commit()
        return success_response(message="收藏夹已删除")
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)


@bp.route("/<int:post_id>/collect/folder", methods=["PUT"])
@login_required
def move_collection_to_folder(post_id):
    """PUT /api/v1/posts/:post_id/collect/folder — 将已收藏的博文移入指定收藏夹"""
    try:
        from core.models.interaction import Collection, CollectionFolder
        data = request.get_json() or {}
        folder_id = data.get("folder_id")  # None = 移出收藏夹

        collection = Collection.query.filter_by(user_id=g.user_id, post_id=post_id).first()
        if not collection:
            return error_response(code="NOT_FOUND", message="您尚未收藏此博文", http_code=404)

        if folder_id is not None:
            folder = CollectionFolder.query.get(folder_id)
            if not folder or folder.user_id != g.user_id:
                return error_response(code="NOT_FOUND", message="收藏夹不存在", http_code=404)

        collection.folder_id = folder_id
        db_session.session.commit()
        return success_response(data=collection.to_dict(), message="已移动到指定收藏夹")
    except Exception as e:
        return error_response(code="INTERNAL_ERROR", message=str(e), http_code=500)
