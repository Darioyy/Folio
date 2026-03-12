"""
Flask 扩展单例 - 跨蓝图共享
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],          # 不设全局默认，只在具体端点限速
    storage_uri="memory://",
)
