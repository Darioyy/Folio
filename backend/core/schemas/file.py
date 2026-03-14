"""
文件相关的 Pydantic Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class FileCreate(BaseModel):
    """创建文件 Schema（上传时附带的元数据）"""
    title: str = Field(..., min_length=1, max_length=200, description='文件标题')
    description: Optional[str] = Field(None, description='文件描述')
    file_category: str = Field(..., pattern='^(image|video|document|resource)$', description='文件分类')
    visibility: Optional[str] = Field('private', pattern='^(private|public)$', description='可见性')


class FileUpdate(BaseModel):
    """更新文件 Schema（均为可选）"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description='文件标题')
    description: Optional[str] = Field(None, description='文件描述')
    visibility: Optional[str] = Field(None, pattern='^(private|public)$', description='可见性')
    file_name: Optional[str] = Field(None, min_length=1, max_length=255, description='文件名（含扩展名）')
