"""
搜索 API
"""
from flask import Blueprint, request

from core.services.search_service import search_service
from core.utils.response import success_response, error_response

bp = Blueprint('search_v1', __name__)


@bp.route('', methods=['GET'])
def search():
    """
    GET /api/v1/search?q=keyword&type=file|user|all&page=1&page_size=20
    """
    q = request.args.get('q', '').strip()
    if not q:
        return error_response('INVALID_PARAMS', '搜索关键词不能为空', 400)

    type_ = request.args.get('type', 'all')
    if type_ not in ('file', 'user', 'all'):
        type_ = 'all'

    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 50)

    result = search_service.search(q, type_, page, page_size)
    return success_response(result)
