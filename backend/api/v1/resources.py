"""
学习资源 API 路由 - v1版本
遵循 RESTful 规范和三层架构
"""

import os
from flask import Blueprint, request, g, send_file
from werkzeug.utils import secure_filename

from db.session import db as db_session
from core.schemas.resource import ResourceCreate, ResourceUpdate
from core.services.resource_service import ResourceService
from core.utils.validators import login_required
from core.utils.response import success_response, error_response, pagination_response
from config.default import Config


# 创建蓝图
bp = Blueprint("resources_v1", __name__)


@bp.route("", methods=["GET"])
def list_resources():
    """
    获取资源列表

    Request:
        GET /api/v1/resources?page=1&page_size=10&category_id=1

    Response:
        {
            "success": true,
            "data": {
                "items": [...],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total": 100,
                    "pages": 10
                }
            }
        }
    """
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 10, type=int), 100)
    category_id = request.args.get("category_id", type=int)

    result = ResourceService.list_resources(
        page=page,
        page_size=page_size,
        category_id=category_id,
        session=db_session.session,
    )

    return pagination_response(
        [
            r.to_dict(include_category=True, include_uploader=True)
            for r in result["items"]
        ],
        result["page"],
        result["page_size"],
        result["total"],
    )


@bp.route("/<int:resource_id>", methods=["GET"])
def get_resource(resource_id: int):
    """
    获取资源详情

    Request:
        GET /api/v1/resources/:id

    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "title": "...",
                ...
            }
        }
    """
    resource = ResourceService.get_with_details(resource_id, db_session.session)

    if not resource:
        return error_response("RESOURCE_NOT_FOUND", "资源不存在", 404)

    return success_response(resource)


@bp.route("/upload", methods=["POST"])
@login_required
def upload_resource():
    """
    上传资源文件

    Request:
        POST /api/v1/resources/upload
        Content-Type: multipart/form-data
        file: <file>
        title: "资源标题"
        description: "资源描述" (可选)
        category_id: 1 (可选)

    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "title": "...",
                ...
            }
        }
    """
    # 检查是否有文件
    if "file" not in request.files:
        return error_response("NO_FILE", "没有上传文件", 400)

    file = request.files["file"]
    if file.filename == "":
        return error_response("EMPTY_FILENAME", "未选择文件", 400)

    # 获取表单数据
    title = request.form.get("title")
    description = request.form.get("description", "")
    category_id = request.form.get("category_id", type=int)

    if not title:
        return error_response("MISSING_TITLE", "title 不能为空", 400)

    # 验证文件类型
    if not ResourceService.allowed_file(
        file.filename, Config.ALLOWED_EXTENSIONS.get("documents", set())
    ):
        return error_response(
            "INVALID_FILE_TYPE",
            f'不支持的文件类型，允许的类型: {Config.ALLOWED_EXTENSIONS.get("documents", set())}',
            400,
        )

    # 确保上传目录存在
    upload_dir = os.path.join(Config.UPLOAD_FOLDER, "resources")
    os.makedirs(upload_dir, exist_ok=True)

    # 生成唯一文件名并保存
    unique_filename = ResourceService.generate_unique_filename(file.filename)
    file_path = os.path.join("resources", unique_filename)
    full_path = os.path.join(Config.UPLOAD_FOLDER, file_path)

    file.save(full_path)

    # 获取文件信息
    file_size = os.path.getsize(full_path)
    file_type = file.mimetype or "application/octet-stream"

    # 创建资源数据
    try:
        resource_data = ResourceCreate(
            title=title,
            description=description if description else None,
            category_id=category_id,
        )
    except Exception as e:
        # 清理已上传的文件
        if os.path.exists(full_path):
            os.remove(full_path)
        return error_response("INVALID_PARAMS", str(e), 400)

    # 保存到数据库
    try:
        resource = ResourceService.create(
            resource_data=resource_data,
            file_path=file_path,
            file_name=secure_filename(file.filename),
            file_size=file_size,
            file_type=file_type,
            uploader_id=g.user_id,
            session=db_session.session,
        )

        return success_response(resource.to_dict(), "文件上传成功", 201)

    except Exception as e:
        # 清理已上传的文件
        if os.path.exists(full_path):
            os.remove(full_path)
        return error_response("UPLOAD_FAILED", f"上传失败: {str(e)}", 500)


@bp.route("/<int:resource_id>/download", methods=["GET"])
def download_resource(resource_id: int):
    """
    下载资源文件

    Request:
        GET /api/v1/resources/:id/download

    Response:
        返回文件流，并增加下载计数
    """
    resource = ResourceService.get_by_id(resource_id, db_session.session)

    if not resource:
        return error_response("RESOURCE_NOT_FOUND", "资源不存在", 404)

    # 构建文件路径
    file_path = os.path.join(Config.UPLOAD_FOLDER, resource.file_path)

    # 检查文件是否存在
    if not os.path.exists(file_path):
        return error_response("FILE_NOT_FOUND", "文件不存在", 404)

    # 增加下载计数
    try:
        ResourceService.increment_download(resource_id, db_session.session)
    except Exception:
        # 计数失败不影响下载
        pass

    # 发送文件
    return send_file(file_path, as_attachment=True, download_name=resource.file_name)


@bp.route("/<int:resource_id>", methods=["PUT"])
@login_required
def update_resource(resource_id: int):
    """
    更新资源信息

    Request:
        PUT /api/v1/resources/:id
        {
            "title": "新标题",
            "description": "新描述",
            "category_id": 1
        }

    Response:
        {
            "success": true,
            "data": {...}
        }
    """
    try:
        data = ResourceUpdate(**request.json)
    except Exception as e:
        return error_response("INVALID_PARAMS", str(e), 400)

    try:
        resource = ResourceService.update(
            resource_id=resource_id,
            resource_data=data,
            operator_id=g.user_id,
            session=db_session.session,
        )

        return success_response(resource.to_dict(), "更新成功")

    except ValueError as e:
        return error_response("NOT_FOUND", str(e), 404)
    except PermissionError as e:
        return error_response("FORBIDDEN", str(e), 403)


@bp.route("/<int:resource_id>", methods=["DELETE"])
@login_required
def delete_resource(resource_id: int):
    """
    删除资源

    Request:
        DELETE /api/v1/resources/:id

    Response:
        {
            "success": true,
            "message": "删除成功"
        }
    """
    try:
        ResourceService.delete(
            resource_id=resource_id,
            operator_id=g.user_id,
            session=db_session.session,
            upload_folder=Config.UPLOAD_FOLDER,
        )

        return success_response(message="资源删除成功")

    except ValueError as e:
        return error_response("NOT_FOUND", str(e), 404)
    except PermissionError as e:
        return error_response("FORBIDDEN", str(e), 403)
