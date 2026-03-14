"""
统一文件 API 路由 - v1
合并 /media 和 /resources 上传/管理，统一走 files 表
"""
import os
import re
from flask import Blueprint, request, g, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import select

from db.session import db as db_session
from core.models.user import User
from core.models.file import File
from core.schemas.file import FileCreate, FileUpdate
from core.services.file_service import FileService
from core.services.group_service import GroupService
from core.services.system_service import SystemService
from core.utils.validators import login_required
from core.utils.response import success_response, error_response, pagination_response
from core.utils.permissions import require_admin, require_root
from config.default import Config


bp = Blueprint('files_v1', __name__)


def safe_filename(filename: str) -> str:
    """
    保留更多字符的文件名清理函数（替代 werkzeug secure_filename）。
    保留：Unicode 字母/数字/中文、空格、+ - _ . ( ) [ ] { } # @ !
    删除：路径分隔符、控制字符、Windows/Unix 不合法字符
    """
    # 移除控制字符和 null 字节
    filename = ''.join(c for c in filename if ord(c) >= 32 and c != '\x7f')
    # 移除路径分隔符和文件系统不合法字符
    filename = re.sub(r'[/\\:*?"<>|\n\r\t]', '_', filename)
    # 去掉首尾空白和点（避免隐藏文件 / Windows 尾部点问题）
    filename = filename.strip(' ')
    filename = filename.lstrip('.')
    filename = filename.rstrip('.')
    # 合并连续下划线（超过 3 个）
    filename = re.sub(r'_{4,}', '___', filename)
    return filename or 'file'

# 各分类对应的上传子目录
_SUBDIR = {
    'image':    'media/images',
    'video':    'media/videos',
    'document': 'documents',
    'resource': 'resources',
}

# 各分类允许的 MIME 前缀（空 tuple = 不限制）
_CATEGORY_MIME_PREFIX: dict[str, tuple[str, ...]] = {
    'image':    ('image/',),
    'video':    ('video/',),
    'document': ('application/', 'text/'),
    'resource': (),
}


@bp.route('', methods=['GET'])
@login_required
def list_files():
    """
    文件列表
    - admin: 可查所有用户文件；可额外传 user_id 筛选
    - 普通用户: 只查自己的文件

    Query: page, page_size, category(image/video/document/resource)
    """
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)
    category = request.args.get('category')
    # group_id: None=不过滤, -1=未分组(IS NULL), 正整数=指定分组
    group_id_raw = request.args.get('group_id', type=int)

    if category and category not in ('image', 'video', 'document', 'resource'):
        return error_response('INVALID_PARAMS', 'category 无效', 400)

    is_admin_user = require_admin(g.user_id, db_session.session)
    if is_admin_user:
        # admin 可传 user_id 查看指定用户的文件；不传则只看自己（Hub 场景）
        filter_user_id = request.args.get('user_id', g.user_id, type=int)
    else:
        filter_user_id = g.user_id  # 普通用户只能查自己

    result = FileService.list_files(
        page=page,
        page_size=page_size,
        user_id=filter_user_id,
        file_category=category,
        group_id=group_id_raw,
        session=db_session.session,
        include_user=True,
        viewer_id=g.user_id,
        bypass_privacy=require_root(g.user_id, db_session.session),
    )

    items = [f.to_dict(include_user=True) for f in result['items']]
    return pagination_response(items, result['page'], result['page_size'], result['total'])


@bp.route('/<int:file_id>', methods=['GET'])
def get_file(file_id: int):
    """文件详情（仅文件所有者或 Root 可访问）"""
    from flask import session as flask_session
    file = FileService.get_by_id(file_id, db_session.session)
    if not file:
        return error_response('FILE_NOT_FOUND', '文件不存在', 404)

    current_user_id = flask_session.get('user_id')
    if not current_user_id or (current_user_id != file.user_id and not require_root(current_user_id, db_session.session)):
        return error_response('FORBIDDEN', '无权访问此文件', 403)

    return success_response(file.to_dict(include_user=True))


@bp.route('', methods=['POST'])
@login_required
def upload_file():
    """
    上传文件（统一入口）

    Form:
        file: 文件（必需）
        description: 描述（可选）
        category: image / video / document / resource（必需）
        thumbnail: 视频封面（可选，仅 video 类型有效）
    """
    if 'file' not in request.files:
        return error_response('NO_FILE', '没有上传文件', 400)

    file = request.files['file']
    if not file.filename:
        return error_response('NO_FILE', '未选择文件', 400)

    description = request.form.get('description', '').strip() or None
    category = request.form.get('category', '')
    group_id_raw = request.form.get('group_id')
    group_id = int(group_id_raw) if group_id_raw and group_id_raw.isdigit() else None

    if category not in ('image', 'video', 'document', 'resource'):
        return error_response('INVALID_PARAMS', 'category 必须是 image/video/document/resource', 400)

    # 从系统配置读取全局白名单（空列表 = 禁止所有上传）
    sys_cfg = SystemService.load_config()
    allowed_str = sys_cfg.get('allowed_extensions', '').strip()
    if not allowed_str:
        return error_response('UPLOAD_DISABLED', '系统当前未配置允许上传的文件类型，请联系管理员', 403)
    allowed = {ext.strip().lower() for ext in allowed_str.split(',') if ext.strip()}
    if not FileService.allowed_file(file.filename, allowed):
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else '（无后缀）'
        return error_response('INVALID_FILE_TYPE', f'不支持的文件类型 .{ext}，请上传白名单内的格式', 400)

    # MIME 类型与 category 一致性检查（防止扩展名欺骗）
    mime = (file.mimetype or '').lower()
    allowed_prefixes = _CATEGORY_MIME_PREFIX.get(category, ())
    if allowed_prefixes and not any(mime.startswith(p) for p in allowed_prefixes):
        return error_response('INVALID_FILE_TYPE', f'文件 MIME 类型（{mime}）与所选分类（{category}）不符', 400)

    # 重名检查（含后缀精确匹配）
    original_name = safe_filename(file.filename)
    overwrite = request.form.get('overwrite', 'false').lower() == 'true'
    dup_stmt = select(File.id).where(
        File.user_id == g.user_id,
        File.file_name == original_name,
    )
    if group_id is None:
        dup_stmt = dup_stmt.where(File.group_id.is_(None))
    else:
        dup_stmt = dup_stmt.where(File.group_id == group_id)
    existing_id = db_session.session.execute(dup_stmt).scalar_one_or_none()
    if existing_id is not None:
        if not overwrite:
            return error_response('DUPLICATE_FILE', f'当前文件夹中已存在同名文件「{original_name}」', 409)
        # overwrite=true：先删除旧文件（允许失败）
        try:
            FileService.delete(existing_id, g.user_id, db_session.session, Config.UPLOAD_FOLDER)
        except Exception:
            pass

    # ⚠️ 存储配额检查（后端强制，Root 无限制）
    # 重要原则：安全相关的限制必须在后端校验，前端检查可被直接 API 调用绕过
    uploader = db_session.session.get(User, g.user_id)
    if uploader and not uploader.is_root and uploader.storage_quota > 0:
        storage_used = FileService.get_storage_used(g.user_id, db_session.session)
        if storage_used >= uploader.storage_quota:
            return error_response('STORAGE_FULL', '存储空间已满，无法上传文件', 400)

    # 保存文件
    upload_dir = os.path.abspath(os.path.join(Config.UPLOAD_FOLDER, _SUBDIR[category]))
    os.makedirs(upload_dir, exist_ok=True)

    unique_filename = FileService.generate_unique_filename(file.filename)
    full_path = os.path.join(upload_dir, unique_filename)
    file.save(full_path)
    auto_title = safe_filename(file.filename)

    file_size = os.path.getsize(full_path)
    mime_type = file.mimetype or 'application/octet-stream'
    uploads_abs = os.path.abspath(Config.UPLOAD_FOLDER)
    relative_path = os.path.relpath(full_path, uploads_abs)

    # 媒体专属处理（缩略图 / 时长）
    thumbnail_path = None
    duration = None

    if category == 'image':
        thumbnail_path = relative_path  # 图片自身即缩略图
    elif category == 'video':
        duration = FileService.get_video_duration(full_path)
        thumb_dir = os.path.abspath(os.path.join(Config.UPLOAD_FOLDER, 'media', 'thumbnails'))
        os.makedirs(thumb_dir, exist_ok=True)

        thumbnail_file = request.files.get('thumbnail')
        if thumbnail_file and thumbnail_file.filename:
            thumb_full = os.path.join(thumb_dir, FileService.generate_unique_filename(thumbnail_file.filename))
            thumbnail_file.save(thumb_full)
            thumbnail_path = os.path.relpath(thumb_full, uploads_abs)
        else:
            thumb_abs = FileService.generate_video_thumbnail(full_path, thumb_dir)
            if thumb_abs:
                thumbnail_path = os.path.relpath(thumb_abs, uploads_abs)

    try:
        created = FileService.create(
            file_data=FileCreate(
                title=auto_title,
                description=description,
                file_category=category,
                visibility='private',
            ),
            file_path=relative_path,
            file_name=safe_filename(file.filename),
            file_size=file_size,
            mime_type=mime_type,
            user_id=g.user_id,
            session=db_session.session,
            thumbnail_path=thumbnail_path,
            duration=duration,
            group_id=group_id,
        )
        return success_response(created.to_dict(), '上传成功', 201)

    except Exception as e:
        if os.path.exists(full_path):
            os.remove(full_path)
        return error_response('UPLOAD_FAILED', f'上传失败: {e}', 500)


@bp.route('/<int:file_id>', methods=['PUT'])
@login_required
def update_file(file_id: int):
    """更新文件标题 / 描述 / 可见性"""
    try:
        data = FileUpdate(**request.json)
    except Exception as e:
        return error_response('INVALID_PARAMS', str(e), 400)

    try:
        updated = FileService.update(file_id, data, g.user_id, db_session.session)
        return success_response(updated.to_dict(include_user=True), '更新成功')
    except ValueError as e:
        msg = str(e)
        if '不存在' in msg:
            return error_response('NOT_FOUND', msg, 404)
        return error_response('INVALID_PARAMS', msg, 400)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file(file_id: int):
    """删除文件（含物理文件）"""
    try:
        FileService.delete(file_id, g.user_id, db_session.session, Config.UPLOAD_FOLDER)
        return success_response(message='删除成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/<int:file_id>/group', methods=['PATCH'])
@login_required
def update_file_group(file_id: int):
    """修改文件所属分组 - body: { group_id: int | null }"""
    data = request.get_json() or {}
    # group_id 可以是 null（移出分组）或正整数
    group_id = data.get('group_id')  # None or int

    try:
        GroupService.assign_file_group(file_id, group_id, g.user_id, db_session.session)
        return success_response({'group_id': group_id}, '更新成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/<int:file_id>/download', methods=['GET'])
@login_required
def download_file(file_id: int):
    """
    下载或内联预览文件（仅文件所有者或 Root 可访问）

    Query:
        dl=1  强制下载（Content-Disposition: attachment），否则内联预览
    """
    file = FileService.get_by_id(file_id, db_session.session)
    if not file:
        return error_response('FILE_NOT_FOUND', '文件不存在', 404)

    if g.user_id != file.user_id and not require_root(g.user_id, db_session.session):
        return error_response('FORBIDDEN', '无权访问此文件', 403)

    upload_root = os.path.realpath(os.path.abspath(Config.UPLOAD_FOLDER))
    file_abs = os.path.realpath(os.path.join(upload_root, file.file_path))
    if not file_abs.startswith(upload_root + os.sep):
        return error_response('FORBIDDEN', '非法的文件路径', 403)
    if not os.path.exists(file_abs):
        return error_response('FILE_NOT_FOUND', '文件不在磁盘上', 404)

    as_attachment = request.args.get('dl', '0') == '1'
    return send_file(
        file_abs,
        mimetype=file.mime_type or 'application/octet-stream',
        as_attachment=as_attachment,
        download_name=file.file_name,
    )


@bp.route('/<int:file_id>/thumbnail', methods=['GET'])
def view_thumbnail(file_id: int):
    """
    查看缩略图（图片/视频封面）
    - 文件所有者或 Root 可访问
    - 图片：直接返回原图
    - 视频：返回提取的封面图，无封面则返回原文件
    """
    from flask import session as flask_session
    file = FileService.get_by_id(file_id, db_session.session)
    if not file:
        return error_response('FILE_NOT_FOUND', '文件不存在', 404)

    current_user_id = flask_session.get('user_id')
    if not current_user_id or (current_user_id != file.user_id and not require_root(current_user_id, db_session.session)):
        return error_response('FORBIDDEN', '无权访问此文件', 403)

    upload_root = os.path.realpath(os.path.abspath(Config.UPLOAD_FOLDER))
    thumb_rel = file.thumbnail_path or file.file_path
    thumb_abs = os.path.realpath(os.path.join(upload_root, thumb_rel))
    if not thumb_abs.startswith(upload_root + os.sep):
        return error_response('FORBIDDEN', '非法的文件路径', 403)
    if not os.path.exists(thumb_abs):
        return error_response('FILE_NOT_FOUND', '文件不在磁盘上', 404)

    return send_file(thumb_abs, mimetype=file.mime_type or 'image/jpeg')


@bp.route('/sort', methods=['PATCH'])
@login_required
def sort_files():
    """批量更新文件排序 - body: { ids: [1, 2, 3] }（按新顺序排列）"""
    data = request.get_json() or {}
    ordered_ids = data.get('ids', [])
    if not isinstance(ordered_ids, list):
        return error_response('INVALID_PARAMS', 'ids 必须为数组', 400)
    FileService.sort_files(g.user_id, ordered_ids, db_session.session)
    return success_response(message='排序已更新')


