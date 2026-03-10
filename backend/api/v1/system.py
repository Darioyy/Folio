"""
系统 API 路由 - 三层架构版本
"""
from flask import Blueprint, request, g
from sqlalchemy.exc import IntegrityError
from core.services.system_service import SystemService
from core.utils.response import success_response, error_response
from core.utils.validators import login_required, admin_required
from db.session import db as db_session
from core.models.category import Category

system_bp = Blueprint("system", __name__)


@system_bp.route("/info", methods=["GET"])
def get_system_info():
    """
    获取系统信息
    GET /api/v1/system/info
    返回：数据库表统计、版本信息、数据库大小

    Returns:
        JSON: 系统信息响应
    """
    try:
        system_info = SystemService.get_system_info()
        return success_response(system_info.model_dump())
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {"code": "SYSTEM_ERROR", "message": f"获取系统信息失败: {str(e)}"},
                }
            ),
            500,
        )


@system_bp.route("/categories", methods=["GET"])
def get_categories():
    """
    获取所有分类列表
    GET /api/v1/system/categories
    返回：分类列表

    Returns:
        JSON: 分类列表响应
    """
    try:
        categories = Category.query.order_by(Category.name).all()
        return success_response([cat.to_dict() for cat in categories])
    except Exception as e:
        return error_response("SYSTEM_ERROR", f"获取分类列表失败: {str(e)}", 500)


@system_bp.route("/categories", methods=["POST"])
@login_required
@admin_required
def create_category():
    """
    创建分类
    POST /api/v1/system/categories
    请求体：{"name": "分类名称"}

    Returns:
        JSON: 创建的分类响应
    """
    data = request.get_json()
    name = data.get("name", "").strip()

    if not name:
        return error_response("INVALID_PARAMS", "分类名称不能为空", 400)

    if len(name) > 100:
        return error_response("INVALID_PARAMS", "分类名称最多100个字符", 400)

    try:
        category = Category(name=name)
        db_session.session.add(category)
        db_session.session.commit()
        db_session.session.refresh(category)
        return success_response(category.to_dict(), "分类创建成功", 201)
    except IntegrityError:
        return error_response("CATEGORY_EXISTS", "分类名称已存在", 400)
    except Exception as e:
        return error_response("SYSTEM_ERROR", f"创建分类失败: {str(e)}", 500)


@system_bp.route("/categories/<int:category_id>", methods=["PUT"])
@login_required
@admin_required
def update_category(category_id: int):
    """
    更新分类
    PUT /api/v1/system/categories/:id
    请求体：{"name": "新分类名称"}

    Returns:
        JSON: 更新后的分类响应
    """
    category = Category.query.get(category_id)
    if not category:
        return error_response("CATEGORY_NOT_FOUND", "分类不存在", 404)

    data = request.get_json()
    name = data.get("name", "").strip()

    if not name:
        return error_response("INVALID_PARAMS", "分类名称不能为空", 400)

    if len(name) > 100:
        return error_response("INVALID_PARAMS", "分类名称最多100个字符", 400)

    try:
        category.name = name
        db_session.session.commit()
        db_session.session.refresh(category)
        return success_response(category.to_dict(), "分类更新成功")
    except IntegrityError:
        return error_response("CATEGORY_EXISTS", "分类名称已存在", 400)
    except Exception as e:
        return error_response("SYSTEM_ERROR", f"更新分类失败: {str(e)}", 500)


@system_bp.route("/categories/<int:category_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_category(category_id: int):
    """
    删除分类
    DELETE /api/v1/system/categories/:id

    Returns:
        JSON: 删除成功响应
    """
    category = Category.query.get(category_id)
    if not category:
        return error_response("CATEGORY_NOT_FOUND", "分类不存在", 404)

    # 检查是否有文章使用此分类
    post_count = category.posts.count()
    if post_count > 0:
        return error_response(
            "CATEGORY_IN_USE",
            f"该分类下还有 {post_count} 篇文章，无法删除",
            400
        )

    try:
        db_session.session.delete(category)
        db_session.session.commit()
        return success_response(message="分类删除成功")
    except Exception as e:
        return error_response("SYSTEM_ERROR", f"删除分类失败: {str(e)}", 500)
