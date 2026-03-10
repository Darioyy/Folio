"""
Models 包初始化
从这里导入所有模型
"""
from core.models.user import User
from core.models.media import Media
from core.models.resource import Resource
from core.models.category import Category
from core.models.post import Post

__all__ = ['User', 'Media', 'Resource', 'Category', 'Post']
