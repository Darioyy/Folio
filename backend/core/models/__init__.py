"""
Models 包初始化
从这里导入所有模型
"""
from core.models.user import User
from core.models.category import Category
from core.models.post import Post
from core.models.file_group import FileGroup
from core.models.file import File
from core.models.follow import Follow
from core.models.interaction import Like, Collection
from core.models.comment import Comment
from core.models.notification import Notification

__all__ = ['User', 'Category', 'Post', 'FileGroup', 'File', 'Follow',
           'Like', 'Collection', 'Comment', 'Notification']
