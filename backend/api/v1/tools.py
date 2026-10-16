"""
工具箱 API — 服务端网页抓取代理
绕过浏览器 CORS 限制，以服务端身份抓取目标 URL 的 HTML 内容或图片。
"""
import ipaddress
from urllib.parse import urlparse

import requests as http_requests
from flask import Blueprint, request, Response

from core.utils.response import success_response, error_response
from extensions import limiter

tools_bp = Blueprint('tools', __name__)

MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5 MB

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': (
        'text/html,application/xhtml+xml,application/xml;q=0.9,'
        'image/avif,image/webp,image/apng,*/*;q=0.8,'
        'application/signed-exchange;v=b3;q=0.7'
    ),
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}


@tools_bp.route('/proxy')
@limiter.limit('20 per minute')
def fetch_proxy():
    """代理抓取指定 URL 的 HTML 内容，规避浏览器 CORS 限制。"""
    url = request.args.get('url', '').strip()
    if not url:
        return error_response('INVALID_URL', '请提供 url 参数', 400)

    try:
        parsed = urlparse(url)
    except Exception:
        return error_response('INVALID_URL', '无效的 URL', 400)

    if parsed.scheme not in ('http', 'https'):
        return error_response('INVALID_URL', '仅支持 HTTP/HTTPS URL', 400)

    # 防 SSRF：拒绝内网 / 本地地址
    host = (parsed.hostname or '').lower()
    if not host or host in ('localhost', 'internal'):
        return error_response('FORBIDDEN', '不允许访问内网地址', 403)

    try:
        addr = ipaddress.ip_address(host)
        if (addr.is_private or addr.is_loopback or addr.is_link_local
                or addr.is_reserved or addr.is_unspecified):
            return error_response('FORBIDDEN', '不允许访问内网地址', 403)
    except ValueError:
        pass  # 是域名，不是 IP，放行

    try:
        resp = http_requests.get(
            url,
            headers=_HEADERS,
            timeout=20,
            allow_redirects=True,
            stream=True,
        )
        resp.raise_for_status()

        # 限制响应大小，防止超大页面拖慢服务器
        content = b''
        for chunk in resp.iter_content(chunk_size=65536):
            content += chunk
            if len(content) > MAX_RESPONSE_SIZE:
                return error_response('TOO_LARGE', '页面内容超过 5 MB 限制', 413)

        encoding = resp.encoding or 'utf-8'
        try:
            text = content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            text = content.decode('utf-8', errors='replace')

        return success_response({'content': text, 'url': resp.url})

    except http_requests.exceptions.Timeout:
        return error_response('TIMEOUT', '抓取超时（20 秒），请检查网址是否可访问', 504)
    except http_requests.exceptions.ConnectionError:
        return error_response('CONNECTION_ERROR', '无法连接到目标网址', 502)
    except http_requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else 502
        return error_response('HTTP_ERROR', f'目标网站返回 HTTP {code}', code if 400 <= code < 600 else 502)
    except Exception as e:
        return error_response('FETCH_FAILED', f'抓取失败：{str(e)}', 502)


MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 MB

_IMAGE_CONTENT_TYPES = {
    'image/png', 'image/jpeg', 'image/gif', 'image/webp',
    'image/svg+xml', 'image/avif', 'image/bmp',
}


@tools_bp.route('/image')
@limiter.limit('120 per minute')
def fetch_image():
    """代理下载图片，返回原始二进制，供前端打包 ZIP 时使用。"""
    url = request.args.get('url', '').strip()
    if not url:
        return error_response('INVALID_URL', '请提供 url 参数', 400)

    try:
        parsed = urlparse(url)
    except Exception:
        return error_response('INVALID_URL', '无效的 URL', 400)

    if parsed.scheme not in ('http', 'https'):
        return error_response('INVALID_URL', '仅支持 HTTP/HTTPS URL', 400)

    host = (parsed.hostname or '').lower()
    if not host or host in ('localhost', 'internal'):
        return error_response('FORBIDDEN', '不允许访问内网地址', 403)

    try:
        addr = ipaddress.ip_address(host)
        if (addr.is_private or addr.is_loopback or addr.is_link_local
                or addr.is_reserved or addr.is_unspecified):
            return error_response('FORBIDDEN', '不允许访问内网地址', 403)
    except ValueError:
        pass

    try:
        resp = http_requests.get(
            url,
            headers={**_HEADERS, 'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'},
            timeout=10,
            allow_redirects=True,
            stream=True,
        )
        resp.raise_for_status()

        content_type = resp.headers.get('Content-Type', 'application/octet-stream').split(';')[0].strip().lower()
        if not (content_type.startswith('image/') or content_type in ('application/octet-stream', 'binary/octet-stream')):
            return error_response('INVALID_CONTENT', f'目标 URL 返回的不是图片（{content_type}）', 422)

        content = b''
        for chunk in resp.iter_content(chunk_size=32768):
            content += chunk
            if len(content) > MAX_IMAGE_SIZE:
                return error_response('TOO_LARGE', '图片超过 2 MB', 413)

        return Response(content, content_type=content_type)

    except http_requests.exceptions.Timeout:
        return error_response('TIMEOUT', '图片下载超时', 504)
    except http_requests.exceptions.ConnectionError:
        return error_response('CONNECTION_ERROR', '无法连接到图片服务器', 502)
    except http_requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else 502
        return error_response('HTTP_ERROR', f'图片服务器返回 HTTP {code}', 502)
    except Exception as e:
        return error_response('FETCH_FAILED', f'下载失败：{str(e)}', 502)
