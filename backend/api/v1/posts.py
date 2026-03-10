"""
文章 API 路由 - RESTful API
"""

from flask import Blueprint, request, g
from core.services.post_service import PostService
from core.schemas.post import PostCreate, PostUpdate, PostListQuery
from core.utils.validators import login_required
from core.utils.response import success_response, error_response

posts_bp = Blueprint("posts", __name__)


@posts_bp.route("", methods=["GET"])
def get_posts():
    """
    获取文章列表
    GET /api/v1/posts
    查询参数：page, limit, status, category_id, search
    """
    try:
        # 解析查询参数
        query_schema = PostListQuery(
            page=int(request.args.get("page", 1)),
            limit=int(request.args.get("limit", 10)),
            status=request.args.get("status", "all"),
            category_id=(
                int(request.args.get("category_id"))
                if request.args.get("category_id")
                else None
            ),
            search=request.args.get("search", ""),
        )

        result = PostService.get_posts(
            page=query_schema.page,
            limit=query_schema.limit,
            status=query_schema.status,
            category_id=query_schema.category_id,
            search=query_schema.search,
        )

        return success_response(data=result)

    except Exception as e:
        return error_response(message=str(e), status_code=500)


@posts_bp.route("/<int:post_id>", methods=["GET"])
def get_post(post_id):
    """
    获取文章详情
    GET /api/v1/posts/:id
    """
    try:
        post = PostService.get_post_by_id(post_id, increment_view=True)
        return success_response(data=post)

    except ValueError as e:
        return error_response(message=str(e), status_code=404)
    except Exception as e:
        return error_response(message=str(e), status_code=500)


@posts_bp.route("", methods=["POST"])
@login_required
def create_post():
    """
    创建文章
    POST /api/v1/posts
    请求体：{ title, content, summary, category_id, status }
    """
    try:
        data = request.get_json()
        if not data:
            return error_response(message="请求体不能为空", status_code=400)

        # 验证请求数据
        schema = PostCreate(**data)

        post = PostService.create_post(
            author_id=g.user_id,
            title=schema.title,
            content=schema.content,
            summary=schema.summary,
            category_id=schema.category_id,
            status=schema.status,
        )

        return success_response(data=post, message="文章创建成功", status_code=201)

    except ValueError as e:
        return error_response(message=str(e), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)


@posts_bp.route("/<int:post_id>", methods=["PUT"])
@login_required
def update_post(post_id):
    """
    更新文章
    PUT /api/v1/posts/:id
    请求体：{ title, content, summary, category_id, status }
    """
    try:
        data = request.get_json()
        if not data:
            return error_response(message="请求体不能为空", status_code=400)

        # 验证请求数据（所有字段可选）
        schema = PostUpdate(**data)

        # 获取非空字段
        update_data = schema.model_dump(exclude_unset=True)

        if not update_data:
            return error_response(message="没有可更新的字段", status_code=400)

        post = PostService.update_post(
            post_id=post_id, operator_id=g.user_id, **update_data
        )

        return success_response(data=post, message="文章更新成功")

    except ValueError as e:
        return error_response(
            message=str(e), status_code=403 if "权限" in str(e) else 404
        )
    except Exception as e:
        return error_response(message=str(e), status_code=500)


@posts_bp.route("/<int:post_id>", methods=["DELETE"])
@login_required
def delete_post(post_id):
    """
    删除文章
    DELETE /api/v1/posts/:id
    """
    try:
        PostService.delete_post(post_id=post_id, operator_id=g.user_id)

        return success_response(message="文章删除成功")

    except ValueError as e:
        return error_response(
            message=str(e), status_code=403 if "权限" in str(e) else 404
        )
    except Exception as e:
        return error_response(message=str(e), status_code=500)
