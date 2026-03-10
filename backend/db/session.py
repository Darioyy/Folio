"""
数据库会话管理
使用 SQLAlchemy ORM 进行数据库操作
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 基类"""
    pass


# 创建 SQLAlchemy 实例
db = SQLAlchemy(model_class=Base)


def init_db(app):
    """
    初始化数据库

    Args:
        app: Flask 应用实例
    """
    db.init_app(app)

    with app.app_context():
        # 导入所有模型（确保它们被注册）
        from core.models import user, media  # noqa

        # 创建所有表（如果不存在）
        db.create_all()
        app.logger.info("数据库初始化完成")
