"""
媒体相关的 Pydantic Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class MediaBase(BaseModel):
    """媒体基础 Schema"""
    title: str = Field(..., min_length=1, max_length=200, description='媒体标题')
    description: Optional[str] = Field(None, description='媒体描述')


class MediaCreate(MediaBase):
    """创建媒体 Schema"""
    file_type: str = Field(..., pattern='^(image|video)$', description='媒体类型')


class MediaUpdate(BaseModel):
    """更新媒体 Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class MediaResponse(MediaBase):
    """媒体响应 Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    file_name: str
    file_type: str
    type: str  # 兼容前端
    thumbnail_path: Optional[str] = None
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    uploader_id: int
    uploader_name: Optional[str] = None
    created_at: Optional[str] = None


class MediaListResponse(BaseModel):
    """媒体列表响应 Schema"""
    items: list[MediaResponse]
    pagination: dict


class MediaUploadResponse(BaseModel):
    """媒体上传响应 Schema"""
    id: int
    title: str
    type: str
