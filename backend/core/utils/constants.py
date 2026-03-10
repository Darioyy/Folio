"""
权限常量定义
"""
from enum import IntEnum


class Role(IntEnum):
    """用户角色枚举"""
    USER = 0  # 普通用户
    ADMIN = 1  # 管理员
    ROOT = 2  # 超级管理员


class Permission(IntEnum):
    """权限位枚举"""
    READ = 1      # 读取权限 (001)
    CREATE = 2    # 创建权限 (010)
    UPDATE = 4    # 更新权限 (100)
    DELETE = 8    # 删除权限 (1000)
    ALL = 15      # 全部权限 (1111)
