"""
用户相关的 Pydantic Schemas
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from typing import Optional


class UserBase(BaseModel):
    """用户基础 Schema"""
    username: str = Field(..., min_length=3, max_length=50, description='用户名')
    email: Optional[EmailStr] = Field(None, description='邮箱')


class UserCreate(UserBase):
    """创建用户 Schema"""
    password: str = Field(..., min_length=6, max_length=100, description='密码')
    invite_code: Optional[str] = Field(None, description='内测码')
    is_admin: Optional[int] = Field(None, description='是否管理员（通过内测码等）')
    nickname: Optional[str] = Field(None, min_length=1, max_length=50, description='昵称')


class UserUpdate(BaseModel):
    """更新用户 Schema"""
    uid: Optional[str] = Field(None, min_length=8, max_length=8, description='用户UID（仅 Root 可修改）')
    username: Optional[str] = Field(None, min_length=3, max_length=50, description='用户名（仅 Root 可修改）')
    email: Optional[str] = Field(None, description='邮箱')
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    avatar: Optional[str] = Field(None, description='头像路径')
    nickname: Optional[str] = Field(None, min_length=1, max_length=50, description='昵称')
    signature: Optional[str] = Field(None, max_length=200, description='个性签名')
    is_admin: Optional[int] = None
    is_root: Optional[int] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """验证邮箱：空字符串或有效邮箱"""
        if v is None or v == '':
            return None
        # Pydantic 的 EmailStr 会自动验证非空值
        return v


class UserResponse(UserBase):
    """用户响应 Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    avatar: Optional[str] = None
    nickname: Optional[str] = None
    signature: Optional[str] = None
    storage_used: Optional[int] = Field(None, description='已用存储（字节）')
    storage_quota: Optional[int] = Field(None, description='存储配额（字节）')
    is_admin: int = Field(default=0, description='是否管理员')
    is_root: int = Field(default=0, description='是否超级管理员')
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserLogin(BaseModel):
    """用户登录 Schema"""
    username: str = Field(..., description='用户名')
    password: str = Field(..., description='密码')


class UserChangePassword(BaseModel):
    """修改密码 Schema"""
    old_password: str = Field(..., description='旧密码')
    new_password: str = Field(..., min_length=6, max_length=100, description='新密码')


class ProfileUpdate(BaseModel):
    """个人资料更新 Schema"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=50, description='昵称')
    signature: Optional[str] = Field(None, max_length=200, description='个性签名')
    email: Optional[str] = Field(None, description='邮箱')
