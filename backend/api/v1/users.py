"""
用户 API 路由 - v1版本
遵循 RESTful 规范和三层架构
"""
import os
from flask import Blueprint, request, session, g, send_file
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError

from db.session import db as db_session
from core.models.user import User
from core.schemas.user import UserCreate, UserUpdate, UserLogin, UserChangePassword, ProfileUpdate
from core.services.user_service import UserService
from core.services.follow_service import follow_service
from core.utils.validators import login_required, admin_required, root_required
from core.utils.response import success_response, error_response, pagination_response
from core.utils.permissions import get_user_role
from config.default import Config


# 创建蓝图
bp = Blueprint('users_v1', __name__)


@bp.route('/login', methods=['POST'])
def login():
    """
    用户登录

    Request:
        POST /api/v1/users/login
        {
            "username": "admin",
            "password": "password123"
        }

    Response:
        {
            "success": true,
            "data": {
                "user": {...},
                "token": "..."
            }
        }
    """
    try:
        data = UserLogin(**request.json)
    except Exception as e:
        return error_response('INVALID_PARAMS', str(e), 400)

    user = UserService.authenticate(data.username, data.password, db_session.session)

    if not user:
        return error_response('LOGIN_FAILED', '用户名或密码错误', 401)

    # 设置 session
    session['user_id'] = user.id
    session['username'] = user.username
    session['is_admin'] = user.is_admin
    session['is_root'] = user.is_root

    # 兼容服务器端 session（如 Flask-Session）
    response_data = {'user': user.to_dict()}
    if hasattr(session, 'sid'):
        response_data['session_id'] = session.sid
    return success_response(response_data, '登录成功')


@bp.route('/register', methods=['POST'])
def register():
    """
    用户注册

    Request:
        POST /api/v1/users/register
        {
            "username": "newuser",
            "password": "password123",
            "email": "user@example.com"
        }

    Response:
        {
            "success": true,
            "data": {
                "user": {...}
            },
            "message": "注册成功"
        }
    """
    # 检查是否允许注册（这里可以加内测码检查）
    try:
        data = UserCreate(**request.json)
    except Exception as e:
        return error_response('INVALID_PARAMS', str(e), 400)

    try:
        user = UserService.create(data, db_session.session)
        # 返回格式与登录一致：{data: {user: {...}}}
        return success_response({'user': user.to_dict()}, '注册成功', 201)
    except ValueError as e:
        return error_response('REGISTER_FAILED', str(e), 400)
    except IntegrityError:
        return error_response('USERNAME_EXISTS', '用户名已存在', 400)


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    用户登出

    Request:
        POST /api/v1/users/logout

    Response:
        {
            "success": true,
            "message": "登出成功"
        }
    """
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    session.pop('is_root', None)

    return success_response(message='登出成功')


@bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """
    获取当前登录用户信息

    Request:
        GET /api/v1/users/me

    Response:
        {
            "success": true,
            "data": {
                "user": {...}
            }
        }
    """
    user = UserService.get_by_id(g.user_id, db_session.session)
    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    return success_response(user.to_dict())


@bp.route('/me/password', methods=['PUT'])
@login_required
def change_password():
    """
    修改当前用户密码

    Request:
        PUT /api/v1/users/me/password
        {
            "old_password": "oldpass",
            "new_password": "newpass"
        }

    Response:
        {
            "success": true,
            "message": "密码修改成功"
        }
    """
    try:
        data = UserChangePassword(**request.json)
    except Exception as e:
        return error_response('INVALID_PARAMS', str(e), 400)

    user = UserService.get_by_id(g.user_id, db_session.session)
    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    # 验证旧密码
    if not UserService.verify_password(data.old_password, user.password_hash):
        return error_response('INVALID_PASSWORD', '原密码错误', 400)

    # 更新密码
    user.password_hash = UserService.hash_password(data.new_password)
    db_session.session.commit()

    return success_response(message='密码修改成功')


@bp.route('/me/storage/categories', methods=['GET'])
@login_required
def get_storage_categories():
    """
    获取用户存储分类统计

    Request:
        GET /api/v1/users/me/storage/categories

    Response:
        {
            "success": true,
            "data": [
                {
                    "type": "image",
                    "name": "图片",
                    "count": 10,
                    "size": 1048576
                },
                ...
            ]
        }
    """
    try:
        categories = UserService.get_storage_categories(g.user_id, db_session.session)
        return success_response(categories)
    except Exception as e:
        return error_response('INTERNAL_ERROR', str(e), 500)


@bp.route('', methods=['GET'])
@login_required
def list_users():
    """
    获取用户列表（管理员权限）

    Request:
        GET /api/v1/users?page=1&page_size=20

    Response:
        {
            "success": true,
            "data": {
                "items": [...],
                "pagination": {...}
            }
        }
    """
    # 检查管理员权限
    operator_role = get_user_role(g.user_id, db_session.session)
    if operator_role < 1:  # 不是管理员
        return error_response('FORBIDDEN', '需要管理员权限', 403)

    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    result = UserService.list_users(db_session.session, page, page_size)
    return pagination_response(
        result['items'],
        result['page'],
        result['page_size'],
        result['total']
    )


@bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id: int):
    """
    获取用户详情

    Request:
        GET /api/v1/users/:id

    Response:
        {
            "success": true,
            "data": {
                "user": {...}
            }
        }
    """
    user = UserService.get_by_id(user_id, db_session.session)
    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    return success_response(user.to_dict())


@bp.route('/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id: int):
    """
    更新用户信息

    Request:
        PUT /api/v1/users/:id
        {
            "email": "new@example.com"
        }

    Response:
        {
            "success": true,
            "data": {
                "user": {...}
            }
        }
    """
    try:
        data = UserUpdate(**request.json)
    except Exception as e:
        return error_response('INVALID_PARAMS', str(e), 400)

    try:
        user = UserService.update(user_id, data, g.user_id, db_session.session)
        return success_response(user.to_dict(), '更新成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id: int):
    """
    删除用户（管理员权限）

    Request:
        DELETE /api/v1/users/:id

    Response:
        {
            "success": true,
            "message": "删除成功"
        }
    """
    try:
        UserService.delete(user_id, g.user_id, db_session.session)
        return success_response(message='删除成功')
    except ValueError as e:
        return error_response('NOT_FOUND', str(e), 404)
    except PermissionError as e:
        return error_response('FORBIDDEN', str(e), 403)


@bp.route('/<int:user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id: int):
    """
    更新用户角色（管理员权限）

    Request:
        PUT /api/v1/users/:id/role
        {
            "is_admin": 1,
            "is_root": 0
        }

    Response:
        {
            "success": true,
            "data": {
                "user": {...}
            }
        }
    """
    data = request.json
    user = UserService.get_by_id(user_id, db_session.session)

    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    # 只有 ROOT 可以设置 ROOT 角色
    if data.get('is_root', 0) and not session.get('is_root'):
        return error_response('FORBIDDEN', '只有超级管理员可以设置超级管理员', 403)

    # ADMIN 不能将自己设置为 ROOT
    if user_id == g.user_id and data.get('is_root', 0):
        return error_response('FORBIDDEN', '不能将自己设置为超级管理员', 403)

    # ADMIN 不能修改其他 ADMIN 的角色
    if user.is_admin and not session.get('is_root'):
        return error_response('FORBIDDEN', '无权修改管理员角色', 403)

    user.is_admin = data.get('is_admin', user.is_admin)
    user.is_root = data.get('is_root', user.is_root)

    db_session.session.commit()
    db_session.session.refresh(user)

    return success_response(user.to_dict(), '角色更新成功')


@bp.route('/me/profile', methods=['PUT'])
@login_required
def update_profile():
    """
    更新个人资料

    Request:
        PUT /api/v1/users/me/profile
        {
            "nickname": "新昵称",
            "signature": "个性签名",
            "email": "user@example.com"
        }

    Response:
        {
            "success": true,
            "data": {
                "user": {...}
            },
            "message": "个人资料更新成功"
        }
    """
    try:
        data = ProfileUpdate(**request.json)
    except Exception as e:
        return error_response('INVALID_PARAMS', str(e), 400)

    user = UserService.update_profile(g.user_id, data, db_session.session)
    return success_response(user.to_dict(), '个人资料更新成功')


@bp.route('/me/avatar', methods=['POST'])
@login_required
def upload_avatar():
    """
    上传头像

    Request:
        POST /api/v1/users/me/avatar
        Content-Type: multipart/form-data

    Form Data:
        file: 图片文件

    Response:
        {
            "success": true,
            "data": {
                "user": {...}
            },
            "message": "头像上传成功"
        }
    """
    # 检查文件
    if 'file' not in request.files:
        return error_response('NO_FILE', '没有上传文件', 400)

    file = request.files['file']
    if file.filename == '':
        return error_response('NO_FILE', '未选择文件', 400)

    # 验证文件类型
    allowed_extensions = Config.ALLOWED_EXTENSIONS.get('images', set())
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return error_response(
            'INVALID_FILE_TYPE',
            f'不支持的文件类型，允许的类型: {allowed_extensions}',
            400
        )

    # 创建上传目录
    upload_dir = os.path.join(Config.UPLOAD_FOLDER, 'avatars')
    upload_dir = os.path.abspath(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)

    # 保存文件
    unique_filename = f"{os.urandom(16).hex()}.{ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)

    # 计算相对路径
    uploads_dir = os.path.abspath(Config.UPLOAD_FOLDER)
    relative_path = os.path.relpath(file_path, uploads_dir)

    # 更新用户头像
    user = UserService.update_avatar(g.user_id, relative_path, db_session.session)

    return success_response(user.to_dict(), '头像上传成功')


@bp.route('/me/avatar/view', methods=['GET'])
@login_required
def view_avatar():
    """
    获取当前用户头像

    Request:
        GET /api/v1/users/me/avatar/view

    Response:
        返回头像文件
    """
    user = UserService.get_by_id(g.user_id, db_session.session)
    if not user or not user.avatar:
        # 返回默认头像
        default_avatar = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'default_avatar.png')
        if os.path.exists(default_avatar):
            return send_file(default_avatar)
        return error_response('AVATAR_NOT_FOUND', '头像不存在', 404)

    uploads_dir = os.path.abspath(Config.UPLOAD_FOLDER)
    avatar_path = os.path.join(uploads_dir, user.avatar)

    if not os.path.exists(avatar_path):
        return error_response('FILE_NOT_FOUND', '头像文件不存在', 404)

    return send_file(avatar_path)


@bp.route('/username/<username>/avatar/view', methods=['GET'])
def view_user_avatar(username: str):
    """
    通过用户名获取用户头像（无需登录）

    Request:
        GET /api/v1/users/username/:username/avatar/view

    Response:
        返回头像文件
    """
    from sqlalchemy import select

    stmt = select(User).where(User.username == username)
    user = db_session.session.execute(stmt).scalar_one_or_none()

    if not user or not user.avatar:
        # 返回默认头像
        default_avatar = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'default_avatar.png')
        if os.path.exists(default_avatar):
            return send_file(default_avatar)
        return error_response('AVATAR_NOT_FOUND', '头像不存在', 404)

    uploads_dir = os.path.abspath(Config.UPLOAD_FOLDER)
    avatar_path = os.path.join(uploads_dir, user.avatar)

    if not os.path.exists(avatar_path):
        return error_response('FILE_NOT_FOUND', '头像文件不存在', 404)

    return send_file(avatar_path)


@bp.route('/me/stats', methods=['GET'])
@login_required
def get_user_stats():
    """
    获取当前用户统计数据

    Request:
        GET /api/v1/users/me/stats

    Response:
        {
            "success": true,
            "data": {
                "posts": 10,
                "media": 25,
                "resources": 5,
                "total_size": 1048576
            }
        }
    """
    stats = UserService.get_user_stats(g.user_id, db_session.session)
    return success_response(stats)


# ==================== 用户主页相关 API ====================

@bp.route('/username/<username>', methods=['GET'])
def get_user_by_username(username: str):
    """
    通过用户名获取用户公开信息

    Request:
        GET /api/v1/users/username/:username

    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "username": "admin",
                "nickname": "管理员",
                "signature": "这是个性签名",
                "avatar": "avatars/xxx.jpg",
                "followers_count": 10,
                "following_count": 5,
                "is_admin": 1,
                "is_root": 0,
                "created_at": "2026-03-09T00:00:00"
            }
        }
    """
    from sqlalchemy import select

    stmt = select(User).where(User.username == username)
    user = db_session.session.execute(stmt).scalar_one_or_none()

    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    # 检查隐私设置
    show_stats = user.privacy_stats == 1
    show_follow = user.privacy_follow == 1

    # 返回公开信息
    public_info = {
        'id': user.id,
        'username': user.username,
        'nickname': user.nickname,
        'signature': user.signature,
        'avatar': user.avatar,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }

    # 添加角色信息
    public_info['is_admin'] = user.is_admin
    public_info['is_root'] = user.is_root

    # 根据隐私设置添加关注信息
    if show_follow:
        public_info['followers_count'] = user.followers_count
        public_info['following_count'] = user.following_count
    else:
        public_info['followers_count'] = 0
        public_info['following_count'] = 0

    return success_response(public_info)


@bp.route('/username/<username>/public-content', methods=['GET'])
def get_user_public_content(username: str):
    """
    获取用户公开内容（文章、媒体、资源）

    Request:
        GET /api/v1/users/username/:username/public-content?type=all&page=1&page_size=20

    Query Params:
        type: 内容类型 (all|posts|media|resources)，默认 all
        page: 页码，默认 1
        page_size: 每页数量，默认 20

    Response:
        {
            "success": true,
            "data": {
                "posts": [...],
                "media": [...],
                "resources": [...]
            }
        }
    """
    from sqlalchemy import select

    # 获取用户
    stmt = select(User).where(User.username == username)
    user = db_session.session.execute(stmt).scalar_one_or_none()

    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    content_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    result = {}

    # 获取公开文章
    if content_type in ['all', 'posts']:
        from core.models.post import Post
        post_stmt = select(Post).where(
            Post.author_id == user.id,
            Post.status == 'published'
        ).order_by(Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        posts = list(db_session.session.execute(post_stmt).scalars())
        result['posts'] = [post.to_dict() for post in posts]

    # 获取公开媒体
    if content_type in ['all', 'media']:
        from core.models.media import Media
        media_stmt = select(Media).where(
            Media.uploader_id == user.id,
            Media.visibility == 'public'
        ).order_by(Media.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        media_list = list(db_session.session.execute(media_stmt).scalars())
        result['media'] = [item.to_dict() for item in media_list]

    # 获取公开资源
    if content_type in ['all', 'resources']:
        from core.models.resource import Resource
        resource_stmt = select(Resource).where(
            Resource.uploader_id == user.id,
            Resource.visibility == 'public'
        ).order_by(Resource.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        resources = list(db_session.session.execute(resource_stmt).scalars())
        result['resources'] = [resource.to_dict() for resource in resources]

    return success_response(result)


@bp.route('/username/<username>/stats', methods=['GET'])
def get_user_public_stats(username: str):
    """
    获取用户公开统计数据

    Request:
        GET /api/v1/users/username/:username/stats

    Response:
        {
            "success": true,
            "data": {
                "posts": 10,
                "media": 25,
                "resources": 5
            }
        }
    """
    from sqlalchemy import select, func

    # 获取用户
    stmt = select(User).where(User.username == username)
    user = db_session.session.execute(stmt).scalar_one_or_none()

    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    stats = {}

    # 统计公开文章数量
    from core.models.post import Post
    post_count = db_session.session.execute(
        select(func.count(Post.id)).where(
            Post.author_id == user.id,
            Post.status == 'published'
        )
    ).scalar() or 0
    stats['posts'] = post_count

    # 统计公开媒体数量
    from core.models.media import Media
    media_count = db_session.session.execute(
        select(func.count(Media.id)).where(
            Media.uploader_id == user.id,
            Media.visibility == 'public'
        )
    ).scalar() or 0
    stats['media'] = media_count

    # 统计公开资源数量
    from core.models.resource import Resource
    resource_count = db_session.session.execute(
        select(func.count(Resource.id)).where(
            Resource.uploader_id == user.id,
            Resource.visibility == 'public'
        )
    ).scalar() or 0
    stats['resources'] = resource_count

    return success_response(stats)


# ==================== 关注相关 API ====================

@bp.route('/<int:user_id>/follow', methods=['POST'])
@login_required
def follow_user(user_id: int):
    """
    关注用户

    Request:
        POST /api/v1/users/:id/follow

    Response:
        {
            "success": true,
            "message": "关注成功"
        }
    """
    success, message = follow_service.follow_user(g.user_id, user_id)

    if success:
        return success_response(message=message)
    else:
        return error_response('FOLLOW_FAILED', message, 400)


@bp.route('/<int:user_id>/follow', methods=['DELETE'])
@login_required
def unfollow_user(user_id: int):
    """
    取消关注用户

    Request:
        DELETE /api/v1/users/:id/follow

    Response:
        {
            "success": true,
            "message": "取消关注成功"
        }
    """
    success, message = follow_service.unfollow_user(g.user_id, user_id)

    if success:
        return success_response(message=message)
    else:
        return error_response('UNFOLLOW_FAILED', message, 400)


@bp.route('/<int:user_id>/followers', methods=['GET'])
def get_followers(user_id: int):
    """
    获取用户粉丝列表

    Request:
        GET /api/v1/users/:id/followers?page=1&page_size=20

    Response:
        {
            "success": true,
            "data": {
                "items": [...],
                "pagination": {...}
            }
        }
    """
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    followers, total = follow_service.get_followers(user_id, page, page_size)

    # 检查当前用户的关注状态
    is_logged_in = 'user_id' in session
    if is_logged_in:
        follower_ids = [f['id'] for f in followers]
        follow_status = follow_service.check_follow_status(session['user_id'], follower_ids)
        for follower in followers:
            follower['is_following'] = follow_status.get(follower['id'], False)

    return pagination_response(followers, page, page_size, total)


@bp.route('/<int:user_id>/following', methods=['GET'])
def get_following(user_id: int):
    """
    获取用户关注列表

    Request:
        GET /api/v1/users/:id/following?page=1&page_size=20

    Response:
        {
            "success": true,
            "data": {
                "items": [...],
                "pagination": {...}
            }
        }
    """
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    following, total = follow_service.get_following(user_id, page, page_size)

    # 检查当前用户的关注状态
    is_logged_in = 'user_id' in session
    if is_logged_in:
        following_ids = [f['id'] for f in following]
        follow_status = follow_service.check_follow_status(session['user_id'], following_ids)
        for user in following:
            user['is_following'] = follow_status.get(user['id'], False)

    return pagination_response(following, page, page_size, total)


@bp.route('/me/follow-status', methods=['GET'])
@login_required
def check_follow_status():
    """
    批量检查关注状态

    Request:
        GET /api/v1/users/me/follow-status?ids=1,2,3

    Response:
        {
            "success": true,
            "data": {
                "1": true,
                "2": false,
                "3": true
            }
        }
    """
    ids_param = request.args.get('ids', '')
    if not ids_param:
        return error_response('INVALID_PARAMS', '缺少 ids 参数', 400)

    try:
        target_ids = [int(id_str) for id_str in ids_param.split(',') if id_str.strip()]
    except ValueError:
        return error_response('INVALID_PARAMS', 'ids 参数格式错误', 400)

    follow_status = follow_service.check_follow_status(g.user_id, target_ids)
    return success_response(follow_status)


@bp.route('/me/privacy', methods=['PUT'])
@login_required
def update_privacy_settings():
    """
    更新隐私设置

    Request:
        PUT /api/v1/users/me/privacy
        {
            "privacy_avatar": 1,
            "privacy_stats": 1,
            "privacy_content": 1,
            "privacy_follow": 1
        }

    Response:
        {
            "success": true,
            "message": "隐私设置更新成功"
        }
    """
    user = db_session.session.get(User, g.user_id)
    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    # 允许部分更新
    if 'privacy_avatar' in request.json:
        user.privacy_avatar = int(request.json['privacy_avatar'])
    if 'privacy_stats' in request.json:
        user.privacy_stats = int(request.json['privacy_stats'])
    if 'privacy_content' in request.json:
        user.privacy_content = int(request.json['privacy_content'])
    if 'privacy_follow' in request.json:
        user.privacy_follow = int(request.json['privacy_follow'])

    db_session.session.commit()
    db_session.session.refresh(user)

    return success_response(user.to_dict(), '隐私设置更新成功')
