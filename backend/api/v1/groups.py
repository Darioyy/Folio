"""
文件分组 API 路由 - v1

GET    /groups                   获取根分组列表（侧边栏，含文件数/子文件夹数）
POST   /groups                   创建分组（body: { name, parent_id? }）
GET    /groups/<id>/children     获取子文件夹列表
GET    /groups/<id>/breadcrumb   获取路径面包屑（根→当前）
PUT    /groups/<id>              重命名分组
DELETE /groups/<id>              删除分组（文件解除关联，子分组上移一级）
PATCH  /groups/sort              更新根分组排序（body: { ids: [1,2,3] }）
"""
from flask import Blueprint, request, g, current_app

from db.session import db as db_session
from core.services.group_service import GroupService
from core.utils.validators import login_required
from core.utils.response import success_response, error_response


groups_bp = Blueprint('groups_v1', __name__)


@groups_bp.route('', methods=['GET'])
@login_required
def list_root_groups():
    """获取用户根分组列表（侧边栏，含各组文件数量和子文件夹数量）"""
    groups = GroupService.get_root_groups(g.user_id, db_session.session)
    return success_response(groups)


@groups_bp.route('', methods=['POST'])
@login_required
def create_group():
    """创建分组 - body: { name, parent_id? }"""
    data = request.get_json() or {}
    name = data.get('name', '')
    parent_id = data.get('parent_id')  # None = 根目录
    merge = bool(data.get('merge', False))
    try:
        group = GroupService.create(g.user_id, name, db_session.session,
                                    parent_id=parent_id, merge=merge)
        return success_response(group.to_dict(), '创建成功', 201)
    except ValueError as e:
        return error_response('INVALID_PARAMS', str(e), 400)


@groups_bp.route('/sort', methods=['PATCH'])
@login_required
def sort_root_groups():
    """更新根分组排序 - body: { ids: [1, 2, 3] }"""
    data = request.get_json() or {}
    ordered_ids = data.get('ids', [])
    if not isinstance(ordered_ids, list):
        return error_response('INVALID_PARAMS', 'ids 必须为数组', 400)
    GroupService.sort_root(g.user_id, ordered_ids, db_session.session)
    return success_response(message='排序已更新')


@groups_bp.route('/<int:group_id>/children', methods=['GET'])
@login_required
def get_children(group_id: int):
    """获取某分组的直接子文件夹"""
    try:
        children = GroupService.get_children(group_id, g.user_id, db_session.session)
        return success_response(children)
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)


@groups_bp.route('/<int:group_id>/breadcrumb', methods=['GET'])
@login_required
def get_breadcrumb(group_id: int):
    """获取从根到当前分组的路径"""
    try:
        path = GroupService.get_breadcrumb(group_id, g.user_id, db_session.session)
        return success_response(path)
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)


@groups_bp.route('/<int:group_id>', methods=['PUT'])
@login_required
def rename_group(group_id: int):
    """更新分组信息 - body: { name, description? }"""
    data = request.get_json() or {}
    name = data.get('name', '')
    description = data.get('description')  # None = 不修改，'' = 清空
    try:
        group = GroupService.rename(group_id, g.user_id, name, db_session.session,
                                    description=description)
        return success_response(group.to_dict(), '更新成功')
    except ValueError as e:
        msg = str(e)
        if '不存在' in msg:
            return error_response('NOT_FOUND', msg, 404)
        return error_response('INVALID_PARAMS', msg, 400)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@groups_bp.route('/<int:group_id>', methods=['DELETE'])
@login_required
def delete_group(group_id: int):
    """删除分组（?force=true 时递归删除全部子分组和文件（含磁盘），否则仅解除关联）"""
    force = request.args.get('force', 'false').lower() == 'true'
    upload_folder = current_app.config.get('UPLOAD_FOLDER') if force else None
    try:
        GroupService.delete(group_id, g.user_id, db_session.session,
                            force=force, upload_folder=upload_folder)
        return success_response(message='删除成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@groups_bp.route('/<int:group_id>/size', methods=['GET'])
@login_required
def get_group_size(group_id: int):
    """获取分组（含子分组）的递归总大小（字节）"""
    try:
        size = GroupService.get_size(group_id, g.user_id, db_session.session)
        return success_response(size)
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)


@groups_bp.route('/<int:group_id>/parent', methods=['PATCH'])
@login_required
def move_group(group_id: int):
    """移动分组到新父级 - body: { parent_id }（null=移到根目录）"""
    data = request.get_json() or {}
    new_parent_id = data.get('parent_id')  # None = 根目录
    try:
        group = GroupService.move(group_id, g.user_id, new_parent_id, db_session.session)
        return success_response(group.to_dict(), '移动成功')
    except ValueError as e:
        return error_response('INVALID_PARAMS', str(e), 400)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)
