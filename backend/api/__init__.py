"""
API蓝图初始化
学习要点：蓝图模块化、路由组织
"""
from flask import Blueprint

# 创建各模块蓝图
user_bp = Blueprint('users', __name__)
post_bp = Blueprint('posts', __name__)
resource_bp = Blueprint('resources', __name__)
media_bp = Blueprint('media', __name__)
system_bp = Blueprint('system', __name__)

# 导入路由（必须在蓝图定义后导入）
from . import user, post, resource, media, system

__all__ = ['user_bp', 'post_bp', 'resource_bp', 'media_bp', 'system_bp']