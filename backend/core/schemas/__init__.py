"""
Schemas 包初始化
"""
from core.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    UserChangePassword
)
from core.schemas.media import (
    MediaBase,
    MediaCreate,
    MediaUpdate,
    MediaResponse,
    MediaListResponse,
    MediaUploadResponse
)
from core.schemas.resource import (
    ResourceBase,
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse
)

__all__ = [
    'UserBase',
    'UserCreate',
    'UserUpdate',
    'UserResponse',
    'UserLogin',
    'UserChangePassword',
    'MediaBase',
    'MediaCreate',
    'MediaUpdate',
    'MediaResponse',
    'MediaListResponse',
    'MediaUploadResponse',
    'ResourceBase',
    'ResourceCreate',
    'ResourceUpdate',
    'ResourceResponse'
]
