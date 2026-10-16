"""
用户 API 路由 - v1版本
遵循 RESTful 规范和三层架构
"""
import os
import random
import io
import base64
from flask import Blueprint, request, session, g, send_file, Response
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError

from db.session import db as db_session
from core.models.user import User
from core.schemas.user import UserCreate, UserUpdate, UserLogin, UserChangePassword, ProfileUpdate
from core.services.user_service import UserService
from core.services.follow_service import follow_service
from core.utils.validators import login_required, admin_required, root_required
from core.utils.response import success_response, error_response, pagination_response, format_pydantic_error
from core.utils.permissions import get_user_role, require_root
from core.services.system_service import SystemService
from config.default import Config
from extensions import limiter


# 创建蓝图
bp = Blueprint('users_v1', __name__)

# 验证码字符集（去掉易混淆字符 0/O/1/I/l）
_CAPTCHA_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'


def _build_captcha_image(code: str) -> bytes:
    """用 Pillow 生成高难度验证码 PNG：逐字旋转+变形+波形扭曲+彩色噪点"""
    import math
    from PIL import Image, ImageDraw, ImageFont

    width, height = 140, 48
    n = len(code)

    # ── 渐变背景 ────────────────────────────────────────────
    bg_colors = [
        (238, 240, 255), (237, 233, 254), (232, 240, 255), (240, 245, 255)
    ]
    bg1 = random.choice(bg_colors)
    bg2 = random.choice(bg_colors)
    img = Image.new('RGB', (width, height), bg1)
    draw = ImageDraw.Draw(img)
    # 左右渐变
    for x in range(width):
        t = x / width
        r = int(bg1[0] * (1 - t) + bg2[0] * t)
        g_c = int(bg1[1] * (1 - t) + bg2[1] * t)
        b = int(bg1[2] * (1 - t) + bg2[2] * t)
        draw.line([(x, 0), (x, height)], fill=(r, g_c, b))

    # ── 彩色噪点 ────────────────────────────────────────────
    for _ in range(150):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        r_c = random.randint(80, 200)
        g_c = random.randint(80, 180)
        b_c = random.randint(140, 240)
        draw.point((x, y), fill=(r_c, g_c, b_c))

    # ── 干扰曲线（贝塞尔近似：分段折线） ──────────────────────
    for _ in range(4):
        c = (random.randint(60, 160), random.randint(60, 130), random.randint(140, 220))
        lw = 1
        # 用多段折线模拟曲线
        pts = []
        segs = 8
        for k in range(segs + 1):
            px = int(width * k / segs) + random.randint(-8, 8)
            py = height // 2 + random.randint(-height // 2 + 2, height // 2 - 2)
            pts.append((px, py))
        for k in range(len(pts) - 1):
            draw.line([pts[k], pts[k + 1]], fill=c, width=lw)

    # ── 逐字符绘制（旋转 + 缩放变形） ──────────────────────────
    char_w = width // (n + 1)
    for i, ch in enumerate(code):
        size = random.randint(22, 30)
        try:
            font = ImageFont.load_default(size=size)
        except TypeError:
            font = ImageFont.load_default()

        # 在临时小图上画字
        tmp_size = 48
        tmp = Image.new('RGBA', (tmp_size, tmp_size), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        r_c = random.randint(15, 90)
        g_c = random.randint(10, 60)
        b_c = random.randint(100, 200)
        td.text((tmp_size // 2 - size // 2, tmp_size // 2 - size // 2),
                ch, fill=(r_c, g_c, b_c, 255), font=font)

        # 随机旋转 ±18°
        angle = random.uniform(-18, 18)
        tmp = tmp.rotate(angle, resample=Image.BICUBIC, expand=False)

        # 随机 X/Y 缩放（轻微拉伸）
        scale_x = random.uniform(0.85, 1.15)
        scale_y = random.uniform(0.9, 1.1)
        new_w = max(1, int(tmp_size * scale_x))
        new_h = max(1, int(tmp_size * scale_y))
        tmp = tmp.resize((new_w, new_h), resample=Image.BICUBIC)

        # 粘贴到主图上
        paste_x = char_w * i + char_w // 2 - new_w // 2 + random.randint(-4, 4)
        paste_y = height // 2 - new_h // 2 + random.randint(-5, 5)
        img.paste(tmp, (paste_x, paste_y), tmp)

    # ── 前景叠加干扰（覆盖在字符上） ───────────────────────────
    draw = ImageDraw.Draw(img)
    for _ in range(2):
        c = (random.randint(80, 160), random.randint(80, 130), random.randint(150, 210))
        pts = [(random.randint(0, width // 4), random.randint(4, height - 4))]
        for _ in range(3):
            pts.append((pts[-1][0] + random.randint(20, 45),
                        random.randint(4, height - 4)))
        for k in range(len(pts) - 1):
            draw.line([pts[k], pts[k + 1]], fill=c, width=1)

    # ── 波形像素扭曲（正弦双向位移，轻微） ──────────────────────
    amp = random.uniform(1.5, 2.5)
    freq_h = random.uniform(0.04, 0.08)
    freq_v = random.uniform(0.04, 0.08)
    phase_h = random.uniform(0, math.pi * 2)
    phase_v = random.uniform(0, math.pi * 2)

    src_pixels = img.load()
    dst = Image.new('RGB', (width, height))
    dst_pixels = dst.load()
    for x in range(width):
        for y in range(height):
            dx = int(amp * math.sin(y * freq_h * 1.5 + phase_h))
            dy = int(amp * math.sin(x * freq_v + phase_v))
            sx = min(width - 1, max(0, x - dx))
            sy = min(height - 1, max(0, y - dy))
            dst_pixels[x, y] = src_pixels[sx, sy]

    buf = io.BytesIO()
    dst.save(buf, format='PNG')
    return buf.getvalue()


def _build_avatar_svg(letter: str) -> str:
    """Generate a simple letter-based SVG avatar, used as fallback when no avatar is uploaded."""
    import html
    safe = html.escape((letter or 'F').upper())
    palette = ['#5a67d8', '#7c3aed', '#db2777', '#0891b2', '#059669', '#d97706', '#dc2626', '#2563eb']
    color = palette[ord(letter.lower()) % len(palette)] if letter else palette[0]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40">'
        f'<circle cx="20" cy="20" r="20" fill="{color}"/>'
        f'<text x="20" y="20" dy=".35em" text-anchor="middle" fill="white" '
        f'font-family="system-ui,-apple-system,sans-serif" font-size="16" font-weight="600">{safe}</text>'
        f'</svg>'
    )


@bp.route('/check-email', methods=['GET'])
@limiter.limit("20/minute")
def check_email():
    """GET /api/v1/users/check-email?email=xxx — 检查邮箱是否可用（匿名）"""
    from sqlalchemy import select as _sel
    email = request.args.get('email', '').strip().lower()
    if not email:
        return error_response('INVALID_PARAMS', '邮箱不能为空', 400)
    existing = db_session.session.execute(
        _sel(User).where(User.email == email)
    ).scalar_one_or_none()
    if existing:
        return success_response({'available': False, 'message': '邮箱已被注册'})
    return success_response({'available': True, 'message': '邮箱可用'})


@bp.route('/check-username', methods=['GET'])
@limiter.limit("20/minute")
def check_username():
    """
    检查用户名是否可用（匿名访问）

    Request:
        GET /api/v1/users/check-username?username=xxx

    Response:
        { "success": true, "data": { "available": true/false, "message": "..." } }
    """
    username = request.args.get('username', '').strip()
    if not username:
        return error_response('INVALID_PARAMS', '用户名不能为空', 400)
    if len(username) < 3 or len(username) > 50:
        return success_response({'available': False, 'message': '用户名长度需为 3-50 个字符'})

    existing = UserService.get_by_username(username, db_session.session)
    if existing:
        return success_response({'available': False, 'message': '用户名已被占用'})
    return success_response({'available': True, 'message': '用户名可用'})


@bp.route('/captcha', methods=['GET'])
def get_captcha():
    """
    获取验证码状态及图片
    验证码关闭时返回 enabled=false，无需输入；开启时返回 base64 图片。

    Response:
        { "success": true, "data": { "enabled": true/false, "image": "data:image/png;base64,..." } }
    """
    captcha_enabled = SystemService.load_config().get('captcha_enabled', True)
    if not captcha_enabled:
        session.pop('captcha_answer', None)
        return success_response({'enabled': False, 'image': ''})

    code = ''.join(random.choices(_CAPTCHA_CHARS, k=5))
    session['captcha_answer'] = code.lower()
    img_bytes = _build_captcha_image(code)
    img_b64 = base64.b64encode(img_bytes).decode()
    return success_response({'enabled': True, 'image': f'data:image/png;base64,{img_b64}'})


@bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
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
    body = request.get_json() or {}

    # 后端验证码校验（配置可关闭）
    if SystemService.load_config().get('captcha_enabled', True):
        captcha_input = body.get('captcha', '').strip().lower()
        captcha_expected = session.pop('captcha_answer', None)
        if not captcha_expected or captcha_input != captcha_expected:
            return error_response('INVALID_CAPTCHA', '验证码错误或已过期，请刷新重试', 400)
    else:
        session.pop('captcha_answer', None)  # 清除残留答案

    try:
        data = UserLogin(**body)
    except Exception as e:
        return error_response('INVALID_PARAMS', format_pydantic_error(e), 400)

    user = UserService.authenticate(data.username, data.password, db_session.session)

    # Python-level 大小写精确校验（MySQL utf8mb4_unicode_ci 不敏感，补充精确比对）
    if user and user.username != data.username:
        user = None

    if not user:
        return error_response('LOGIN_FAILED', '用户名或密码错误', 401)

    # 设置 session（permanent=True 使 PERMANENT_SESSION_LIFETIME 生效，即 7 天过期）
    session.permanent = True
    session['user_id'] = user.id
    session['username'] = user.username
    session['is_admin'] = user.is_admin
    session['is_root'] = user.is_root

    # 兼容服务器端 session（如 Flask-Session）
    response_data = {'user': user.to_dict(show_email=True)}
    if hasattr(session, 'sid'):
        response_data['session_id'] = session.sid
    return success_response(response_data, '登录成功')


@bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
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
    body = request.get_json() or {}

    # 后端验证码校验（配置可关闭）
    config = SystemService.load_config()
    if config.get('captcha_enabled', True):
        captcha_input = body.get('captcha', '').strip().lower()
        captcha_expected = session.pop('captcha_answer', None)
        if not captcha_expected or captcha_input != captcha_expected:
            return error_response('INVALID_CAPTCHA', '验证码错误或已过期，请刷新重试', 400)
    else:
        session.pop('captcha_answer', None)

    try:
        data = UserCreate(**body)
    except Exception as e:
        return error_response('INVALID_PARAMS', format_pydantic_error(e), 400)

    # 检查注册开关和内测码（config 已在上方加载）
    if not config.get('register_enabled', True):
        return error_response('REGISTER_DISABLED', '注册已关闭', 403)

    if data.invite_code:
        # 提供了内测码：校验并标记已使用，成功后晋升为管理员
        if not SystemService.validate_and_use_invite_code(data.invite_code, data.username):
            return error_response('INVALID_INVITE_CODE', '内测码无效或已被使用', 400)
        data = data.model_copy(update={'is_admin': 1})
    elif config.get('invite_code_required', False):
        return error_response('INVITE_CODE_REQUIRED', '注册需要内测码', 400)

    try:
        user = UserService.create(data, db_session.session)
        # 注册成功后自动登录（与 login 端点保持一致）
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        session['is_root'] = user.is_root
        return success_response({'user': user.to_dict(show_email=True)}, '注册成功', 201)
    except ValueError as e:
        return error_response('REGISTER_FAILED', str(e), 400)
    except IntegrityError as e:
        db_session.session.rollback()
        err_str = str(e.orig).lower() if e.orig else ''
        if 'email' in err_str or 'uk_email' in err_str:
            return error_response('EMAIL_EXISTS', '该邮箱已被注册', 400)
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
    session.clear()
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
    from sqlalchemy import func, select as sa_select
    from core.models.post import Post

    user = UserService.get_by_id(g.user_id, db_session.session)
    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    data = user.to_dict(show_email=True)

    # 统计该用户所有博文的总获赞数和总被收藏数
    like_count = db_session.session.execute(
        sa_select(func.sum(Post.like_count)).where(Post.author_id == g.user_id)
    ).scalar() or 0
    collect_count = db_session.session.execute(
        sa_select(func.sum(Post.collect_count)).where(Post.author_id == g.user_id)
    ).scalar() or 0

    data['like_count'] = int(like_count)
    data['collect_count'] = int(collect_count)

    return success_response(data)


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
        return error_response('INVALID_PARAMS', format_pydantic_error(e), 400)

    user = UserService.get_by_id(g.user_id, db_session.session)
    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    # 验证旧密码
    if not UserService.verify_password(data.old_password, user.password_hash):
        return error_response('INVALID_PASSWORD', '原密码错误', 400)

    # 更新密码
    user.password_hash = UserService.hash_password(data.new_password)
    db_session.session.commit()

    # 密码修改成功后强制清除 session，要求重新登录
    session.clear()

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

    # 只有本人或管理员才能看到邮箱
    is_self = g.user_id == user_id
    is_admin_user = require_admin(g.user_id, db_session.session)
    return success_response(user.to_dict(show_email=is_self or is_admin_user))


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
        return error_response('INVALID_PARAMS', format_pydantic_error(e), 400)

    try:
        user = UserService.update(user_id, data, g.user_id, db_session.session)
        return success_response(user.to_dict(show_email=True), '更新成功')
    except ValueError as e:
        msg = str(e)
        http_code = 404 if '不存在' in msg else 400
        return error_response('NOT_FOUND' if http_code == 404 else 'BAD_REQUEST', msg, http_code)
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
    data = request.get_json() or {}
    user = UserService.get_by_id(user_id, db_session.session)

    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    # 只有 ROOT 可以设置 ROOT 角色
    if data.get('is_root', 0) and not require_root(g.user_id, db_session.session):
        return error_response('FORBIDDEN', '只有超级管理员可以设置超级管理员', 403)

    # ADMIN 不能将自己设置为 ROOT
    if user_id == g.user_id and data.get('is_root', 0):
        return error_response('FORBIDDEN', '不能将自己设置为超级管理员', 403)

    # ADMIN 不能修改其他 ADMIN 的角色
    if user.is_admin and not require_root(g.user_id, db_session.session):
        return error_response('FORBIDDEN', '无权修改管理员角色', 403)

    user.is_admin = data.get('is_admin', user.is_admin)
    user.is_root = data.get('is_root', user.is_root)

    db_session.session.commit()
    db_session.session.refresh(user)

    return success_response(user.to_dict(show_email=True), '角色更新成功')


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
        return error_response('INVALID_PARAMS', format_pydantic_error(e), 400)

    try:
        user = UserService.update_profile(g.user_id, data, db_session.session)
        return success_response(user.to_dict(show_email=True), '个人资料更新成功')
    except ValueError as e:
        return error_response('BAD_REQUEST', str(e), 400)


@bp.route('/me/cover', methods=['PUT'])
@login_required
def save_cover():
    """
    保存用户主页封面元数据

    Request:
        PUT /api/v1/users/me/cover
        { "cover_meta": "linear-gradient(...)" }

    Response:
        { "success": true }
    """
    data = request.get_json(silent=True) or {}
    cover_meta = data.get('cover_meta', '')

    # 限制大小（1MB），防止存入超大 data URL
    if len(cover_meta) > 1_048_576:
        return error_response('TOO_LARGE', '封面数据过大', 413)

    from sqlalchemy import update
    db_session.session.execute(
        update(User).where(User.id == g.user_id).values(cover_meta=cover_meta or None)
    )
    db_session.session.commit()
    return success_response({}, '封面保存成功')


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

    return success_response(user.to_dict(show_email=True), '头像上传成功')


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
        letter = user.username[0] if user else 'F'
        return Response(_build_avatar_svg(letter), mimetype='image/svg+xml',
                        headers={'Cache-Control': 'public, max-age=86400'})

    uploads_dir = os.path.abspath(Config.UPLOAD_FOLDER)
    avatar_path = os.path.join(uploads_dir, user.avatar)

    if not os.path.exists(avatar_path):
        return Response(_build_avatar_svg(user.username[0]), mimetype='image/svg+xml',
                        headers={'Cache-Control': 'public, max-age=86400'})

    return send_file(avatar_path, max_age=86400)


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
        letter = user.username[0] if user else 'F'
        return Response(_build_avatar_svg(letter), mimetype='image/svg+xml',
                        headers={'Cache-Control': 'public, max-age=86400'})

    uploads_dir = os.path.abspath(Config.UPLOAD_FOLDER)
    avatar_path = os.path.join(uploads_dir, user.avatar)

    if not os.path.exists(avatar_path):
        return Response(_build_avatar_svg(user.username[0]), mimetype='image/svg+xml',
                        headers={'Cache-Control': 'public, max-age=86400'})

    return send_file(avatar_path, max_age=86400)


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
        'uid': user.uid,
        'username': user.username,
        'nickname': user.nickname,
        'signature': user.signature,
        'cover_meta': user.cover_meta,
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

    # 互相关注检测（仅登录用户可见，且不是自己）
    from flask import session as flask_session
    viewer_id = flask_session.get('user_id')
    if viewer_id and viewer_id != user.id:
        from core.services.follow_service import follow_service
        # is_following_back：目标用户是否关注了当前查看者
        public_info['is_following_back'] = follow_service.is_following(user.id, viewer_id)
    else:
        public_info['is_following_back'] = False

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
            Post.status == 'published',
            Post.is_hidden == 0,  # 过滤管理员隐藏的博文
        ).order_by(Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        posts = list(db_session.session.execute(post_stmt).scalars())
        result['posts'] = [post.to_dict() for post in posts]

    # 获取公开媒体（image + video）
    if content_type in ['all', 'media']:
        from core.models.file import File
        media_stmt = select(File).where(
            File.user_id == user.id,
            File.visibility == 'public',
            File.file_category.in_(['image', 'video'])
        ).order_by(File.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        media_list = list(db_session.session.execute(media_stmt).scalars())
        result['media'] = [item.to_dict() for item in media_list]

    # 获取公开资源
    if content_type in ['all', 'resources']:
        from core.models.file import File
        resource_stmt = select(File).where(
            File.user_id == user.id,
            File.visibility == 'public',
            File.file_category == 'resource'
        ).order_by(File.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

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
            Post.status == 'published',
            Post.is_hidden == 0,  # 不计入被管理员隐藏的博文
        )
    ).scalar() or 0
    stats['posts'] = post_count

    # 统计公开媒体数量（image + video）
    from core.models.file import File
    media_count = db_session.session.execute(
        select(func.count(File.id)).where(
            File.user_id == user.id,
            File.visibility == 'public',
            File.file_category.in_(['image', 'video'])
        )
    ).scalar() or 0
    stats['media'] = media_count

    # 统计公开资源数量
    resource_count = db_session.session.execute(
        select(func.count(File.id)).where(
            File.user_id == user.id,
            File.visibility == 'public',
            File.file_category == 'resource'
        )
    ).scalar() or 0
    stats['resources'] = resource_count

    # 获赞数和被收藏数（受 privacy_stats 控制）
    if user.privacy_stats == 1:
        from core.models.post import Post as PostModel
        likes_received = db_session.session.execute(
            select(func.sum(PostModel.like_count)).where(
                PostModel.author_id == user.id,
                PostModel.status == 'published',
                PostModel.is_hidden == 0,
            )
        ).scalar() or 0
        collects_received = db_session.session.execute(
            select(func.sum(PostModel.collect_count)).where(
                PostModel.author_id == user.id,
                PostModel.status == 'published',
                PostModel.is_hidden == 0,
            )
        ).scalar() or 0
        stats['likes_received'] = int(likes_received)
        stats['collects_received'] = int(collects_received)
    else:
        stats['likes_received'] = None
        stats['collects_received'] = None

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

    follower_ids = [f['id'] for f in followers]
    # 互相关注：仅 profile owner 本人查看时才填充，第三方访问一律置 False
    viewer_id = session.get('user_id')
    if viewer_id == user_id:
        owner_follows = follow_service.check_follow_status(user_id, follower_ids)
        for follower in followers:
            follower['is_mutual'] = owner_follows.get(follower['id'], False)
    else:
        for follower in followers:
            follower['is_mutual'] = False

    # 检查当前访问者的关注状态
    is_logged_in = 'user_id' in session
    if is_logged_in:
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

    following_ids = [f['id'] for f in following]
    # 互相关注：仅 profile owner 本人查看时才填充，第三方访问一律置 False
    viewer_id = session.get('user_id')
    if viewer_id == user_id:
        mutual_set = follow_service.get_mutual_followings(user_id, following_ids)
        for u in following:
            u['is_mutual'] = u['id'] in mutual_set
    else:
        for u in following:
            u['is_mutual'] = False

    # 检查当前访问者的关注状态
    is_logged_in = 'user_id' in session
    if is_logged_in:
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


@bp.route('/me/redeem-code', methods=['POST'])
@login_required
def redeem_invite_code():
    """
    兑换内测码（用于已注册用户补录）
    POST /api/v1/users/me/redeem-code
    Body: { "invite_code": "XXXXXXXX" }
    """
    data = request.get_json() or {}
    code = data.get('invite_code', '').strip().upper()
    if not code:
        return error_response('INVALID_PARAMS', '请输入内测码', 400)

    user = db_session.session.get(User, g.user_id)
    if not user:
        return error_response('USER_NOT_FOUND', '用户不存在', 404)

    if not SystemService.validate_and_use_invite_code(code, user.username):
        return error_response('INVALID_INVITE_CODE', '内测码无效或已被使用', 400)

    return success_response(message='内测码兑换成功')


@bp.route('/username/<username>/posts', methods=['GET'])
def get_user_posts(username: str):
    """
    获取某用户的已发布博文列表（公开，无需登录）
    GET /api/v1/users/username/:username/posts?page=1&page_size=20
    """
    from core.services.post_service import PostService

    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    try:
        result = PostService.get_user_posts(username=username, page=page, page_size=page_size)
        return success_response(result)
    except ValueError as e:
        return error_response('USER_NOT_FOUND', str(e), 404)
    except Exception as e:
        return error_response('INTERNAL_ERROR', str(e), 500)


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

    return success_response(user.to_dict(show_email=True), '隐私设置更新成功')
