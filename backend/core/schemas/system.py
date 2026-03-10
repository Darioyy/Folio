"""
系统相关的 Pydantic Schemas
"""
from pydantic import BaseModel, Field, ConfigDict


class DatabaseStats(BaseModel):
    """数据库统计信息"""

    users: int = Field(0, ge=0, description="用户数量")
    categories: int = Field(0, ge=0, description="分类数量")
    resources: int = Field(0, ge=0, description="资源数量")
    media: int = Field(0, ge=0, description="媒体数量")
    posts: int = Field(0, ge=0, description="已发布文章数量")


class SystemInfoResponse(BaseModel):
    """系统信息响应 Schema"""

    model_config = ConfigDict(from_attributes=True)

    version: str = Field(..., description="系统版本号")
    database_stats: DatabaseStats = Field(..., description="数据库统计信息")
    database_size_mb: float = Field(0.0, ge=0, description="数据库大小(MB)")
