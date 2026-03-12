"""
文章相关的 Pydantic Schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class PostBase(BaseModel):
    """文章基础 Schema"""

    title: str = Field(..., min_length=1, max_length=200, description="文章标题")
    content: str = Field("", description="文章内容")
    summary: Optional[str] = Field(None, description="文章摘要")
    category_id: Optional[int] = Field(None, description="分类ID")


class PostCreate(PostBase):
    """创建文章 Schema"""

    cover_image_id: Optional[int] = Field(None, description="封面图文件ID")
    status: Optional[str] = Field(
        "draft", pattern="^(draft|published|archived)$", description="文章状态"
    )


class PostUpdate(BaseModel):
    """更新文章 Schema"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None)
    summary: Optional[str] = None
    category_id: Optional[int] = None
    cover_image_id: Optional[int] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")


class PostAttachmentAdd(BaseModel):
    """添加附件 Schema"""

    file_id: int = Field(..., description="文件ID")


class PostResponse(PostBase):
    """文章响应 Schema"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    author_id: int
    status: str
    view_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    category_name: Optional[str] = None
    author_name: Optional[str] = None


class PostListQuery(BaseModel):
    """文章列表查询参数 Schema"""

    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(10, ge=1, le=100, description="每页数量")
    status: Optional[str] = Field(
        "all", pattern="^(all|draft|published|archived)$", description="状态筛选"
    )
    category_id: Optional[int] = Field(None, description="分类ID筛选")
    search: Optional[str] = Field("", description="搜索关键词")
