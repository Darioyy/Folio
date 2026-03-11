"""
系统 API 路由 - 三层架构版本
"""
from flask import Blueprint, request, g
from sqlalchemy.exc import IntegrityError
from core.services.system_service import SystemService
from core.services.file_service import FileService
from core.models.user import User
from core.utils.response import success_response, error_response
from core.utils.validators import login_required, admin_required, root_required
from core.utils.permissions import require_root
from db.session import db as db_session
from core.models.category import Category

system_bp = Blueprint("system", __name__)


@system_bp.route("/info", methods=["GET"])
def get_system_info():
    """
    获取系统信息
    GET /api/v1/system/info
    返回：数据库表统计、版本信息、数据库大小
    """
    try:
        system_info = SystemService.get_system_info()
        return success_response(system_info.model_dump())
    except Exception as e:
        return error_response("SYSTEM_ERROR", f"获取系统信息失败: {str(e)}", 500)


@system_bp.route("/stats", methods=["GET"])
@login_required
@admin_required
def get_admin_stats():
    """
    获取管理员数据概览
    GET /api/v1/system/stats
    返回：用户总数 / 文件总数 / 各类型文件数 / 全站存储量 / 近7天新增用户
    """
    try:
        stats = SystemService.get_admin_stats()
        return success_response(stats.model_dump())
    except Exception as e:
        return error_response("SYSTEM_ERROR", f"获取统计数据失败: {str(e)}", 500)


@system_bp.route("/files", methods=["GET"])
@login_required
@admin_required
def get_admin_files():
    """
    管理员文件列表查询
    GET /api/v1/system/files?page=&page_size=&category=&username=
    支持按分类和用户名筛选，返回全站文件
    """
    page = int(request.args.get('page', 1))
    page_size = min(int(request.args.get('page_size', 20)), 100)
    category = request.args.get('category')
    username = request.args.get('username', '').strip()

    user_id = None
    if username:
        user = User.query.filter_by(username=username).first()
        if not user:
            return success_response(
                {'items': [], 'total': 0, 'page': page, 'page_size': page_size, 'pages': 0}
            )
        user_id = user.id

    try:
        result = FileService.list_files(
            page=page,
            page_size=page_size,
            user_id=user_id,
            file_category=category if category else None,
            session=db_session.session,
            include_user=True,
            viewer_id=g.user_id,
            bypass_privacy=require_root(g.user_id, db_session.session),
        )
        items = [f.to_dict(include_user=True) for f in result['items']]
        return success_response({
            'items': items,
            'total': result['total'],
            'page': result['page'],
            'page_size': result['page_size'],
            'pages': result['pages'],
        })
    except Exception as e:
        return error_response("SYSTEM_ERROR", f"查询文件列表失败: {str(e)}", 500)


@system_bp.route("/config", methods=["GET"])
@login_required
@admin_required
def get_config():
    """
    获取系统配置（管理员可读）
    GET /api/v1/system/config
    """
    try:
        config = SystemService.load_config()
        # 不返回 invite_codes 列表（由专用接口管理）
        result = {k: v for k, v in config.items() if k != 'invite_codes'}
        return success_response(result)
    except Exception as e:
        return error_response("SYSTEM_ERROR", f"读取配置失败: {str(e)}", 500)


@system_bp.route("/config", methods=["PUT"])
@login_required
@root_required
def update_config():
    """
    更新系统配置（Root 专属）
    PUT /api/v1/system/config
    """
    data = request.get_json() or {}
    allowed_keys = {
        'register_enabled', 'invite_code_required', 'captcha_enabled',
        'storage_quota_root', 'storage_quota_admin', 'storage_quota_user',
        'max_file_size', 'allowed_extensions'
    }
    invalid = set(data.keys()) - allowed_keys
    if invalid:
        return error_response("INVALID_PARAMS", f"不允许修改的字段: {', '.join(invalid)}", 400)

    try:
        config = SystemService.load_config()
        for k, v in data.items():
            config[k] = v
        SystemService.save_config(config)

        # 配额字段变更时同步更新数据库中所有用户的 storage_quota
        quota_keys = {'storage_quota_root', 'storage_quota_admin', 'storage_quota_user'}
        if quota_keys & set(data.keys()):
            from sqlalchemy import update as sql_update
            session = db_session.session
            session.execute(
                sql_update(User).where(User.is_root == 1).values(
                    storage_quota=config['storage_quota_root']
                )
            )
            session.execute(
                sql_update(User).where(User.is_admin == 1, User.is_root == 0).values(
                    storage_quota=config['storage_quota_admin']
                )
            )
            session.execute(
                sql_update(User).where(User.is_admin == 0, User.is_root == 0).values(
                    storage_quota=config['storage_quota_user']
                )
            )
            session.commit()

        result = {k: v for k, v in config.items() if k != 'invite_codes'}
        return success_response(result, "配置更新成功")
    except Exception as e:
        return error_response("SYSTEM_ERROR", f"保存配置失败: {str(e)}", 500)


@system_bp.route("/invite-codes", methods=["GET"])
@login_required
@root_required
def list_invite_codes():
    """
    列出所有内测码
    GET /api/v1/system/invite-codes
    """
    try:
        codes = SystemService.list_invite_codes()
        return success_response(codes)
    except Exception as e:
        return error_response("SYSTEM_ERROR", f"获取内测码失败: {str(e)}", 500)


@system_bp.route("/invite-codes", methods=["POST"])
@login_required
@root_required
def create_invite_code():
    """
    生成新内测码（随机 8 位）
    POST /api/v1/system/invite-codes
    """
    try:
        entry = SystemService.generate_invite_code()
        return success_response(entry, "内测码生成成功", 201)
    except Exception as e:
        return error_response("SYSTEM_ERROR", f"生成内测码失败: {str(e)}", 500)


@system_bp.route("/invite-codes/<string:code>", methods=["DELETE"])
@login_required
@root_required
def delete_invite_code(code: str):
    """
    删除内测码
    DELETE /api/v1/system/invite-codes/:code
    """
    try:
        deleted = SystemService.delete_invite_code(code)
        if not deleted:
            return error_response("NOT_FOUND", "内测码不存在", 404)
        return success_response(message="内测码已删除")
    except Exception as e:
        return error_response("SYSTEM_ERROR", f"删除内测码失败: {str(e)}", 500)


@system_bp.route("/categories", methods=["GET"])
def get_categories():
    """
    获取所有分类列表
    GET /api/v1/system/categories
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
    """
    category = Category.query.get(category_id)
    if not category:
        return error_response("CATEGORY_NOT_FOUND", "分类不存在", 404)

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
