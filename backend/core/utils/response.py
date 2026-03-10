"""
统一响应格式工具
"""
from typing import Any, Optional
from flask import jsonify


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
