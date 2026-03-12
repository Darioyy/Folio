"""
API v1 包初始化
从这里导出所有 v1 版本的蓝图
"""
from api.v1.users import bp as users_bp
from api.v1.media import bp as media_bp
from api.v1.resources import bp as resources_bp
from api.v1.posts import posts_bp
from api.v1.post_interactions import bp as post_interactions_bp
from api.v1.system import system_bp
from api.v1.hub import bp as hub_bp
from api.v1.files import bp as files_bp
from api.v1.groups import groups_bp
from api.v1.interactions import bp as interactions_bp
from api.v1.comments import bp as comments_bp
from api.v1.notifications import bp as notifications_bp
from api.v1.search import bp as search_bp

__all__ = [
    'users_bp', 'media_bp', 'resources_bp', 'posts_bp', 'post_interactions_bp',
    'system_bp', 'hub_bp', 'files_bp', 'groups_bp',
    'interactions_bp', 'comments_bp', 'notifications_bp', 'search_bp'
]
