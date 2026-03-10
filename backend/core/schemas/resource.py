"""
学习资源相关的 Pydantic Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class ResourceBase(BaseModel):
    """资源基础 Schema"""

    title: str = Field(..., min_length=1, max_length=200, description="资源标题")
    description: Optional[str] = Field(None, description="资源描述")
    category_id: Optional[int] = Field(None, description="分类ID")


class ResourceCreate(ResourceBase):
    """创建资源 Schema"""

    pass


class ResourceUpdate(BaseModel):
    """更新资源 Schema"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category_id: Optional[int] = None


class ResourceResponse(ResourceBase):
    """资源响应 Schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    download_count: int = 0
    uploader_id: int
    category_name: Optional[str] = None
    uploader_name: Optional[str] = None
    created_at: Optional[str] = None
