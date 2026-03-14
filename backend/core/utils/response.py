"""
统一响应格式工具
"""
from typing import Any, Optional
from flask import jsonify


# Pydantic 字段名 → 中文显示名
_FIELD_LABELS = {
    'username': '用户名', 'password': '密码', 'email': '邮箱',
    'nickname': '昵称', 'title': '标题', 'content': '正文',
    'new_password': '新密码', 'old_password': '旧密码',
    'signature': '个性签名', 'summary': '摘要',
}


def format_pydantic_error(e) -> str:
    """将 Pydantic ValidationError 转换为用户友好的中文提示。"""
    try:
        from pydantic import ValidationError
        if not isinstance(e, ValidationError):
            return str(e)
        errors = e.errors(include_url=False)
    except Exception:
        return str(e)

    messages = []
    for err in errors[:3]:
        field = str(err['loc'][-1]) if err['loc'] else ''
        label = _FIELD_LABELS.get(field, f'「{field}」' if field else '参数')
        err_type = err.get('type', '')
        ctx = err.get('ctx', {})
        msg = err.get('msg', '')

        if err_type == 'missing':
            detail = '不能为空'
        elif err_type == 'string_too_short':
            detail = f'不能少于 {ctx.get("min_length", "?")} 个字符'
        elif err_type == 'string_too_long':
            detail = f'不能超过 {ctx.get("max_length", "?")} 个字符'
        elif err_type in ('value_error', 'string_pattern_mismatch'):
            detail = '格式不正确'
        elif 'email' in msg.lower() or 'valid email' in msg.lower():
            detail = '格式不正确'
        else:
            detail = '无效'

        messages.append(f'{label}{detail}')

    return '；'.join(messages) if messages else '参数验证失败'


def success_response(data: Any = None, message: Optional[str] = None, code: int = 200):
    """
    成功响应

    Args:
        data: 响应数据
        message: 提示消息
        code: HTTP 状态码

    Returns:
        JSON 响应
    """
    response = {'success': True}

    if data is not None:
        response['data'] = data

    if message:
        response['message'] = message

    return jsonify(response), code


def error_response(code: str, message: str, http_code: int = 400):
    """
    错误响应

    Args:
        code: 错误码
        message: 错误信息
        http_code: HTTP 状态码

    Returns:
        JSON 响应
    """
    return jsonify({
        'success': False,
        'error': {
            'code': code,
            'message': message
        }
    }), http_code


def pagination_response(items: list, page: int, page_size: int, total: int):
    """
    分页响应

    Args:
        items: 数据列表
        page: 当前页码
        page_size: 每页数量
        total: 总数量

    Returns:
        JSON 响应
    """
    pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return success_response({
        'items': items,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'pages': pages
        }
    })
