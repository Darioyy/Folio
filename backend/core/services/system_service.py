"""
系统服务层 - 业务逻辑
"""
from sqlalchemy import text, func
from db.session import db as db_session
from core.models.user import User
from core.models.category import Category
from core.models.resource import Resource
from core.models.media import Media
from core.models.post import Post
from core.schemas.system import DatabaseStats, SystemInfoResponse
import logging

logger = logging.getLogger(__name__)


class SystemService:
    """系统服务类"""

    @staticmethod
    def get_database_stats() -> DatabaseStats:
        """
        获取数据库统计信息

        Returns:
            DatabaseStats: 数据库统计信息
        """
        try:
            stats = {
                "users": User.query.count(),
                "categories": Category.query.count(),
                "resources": Resource.query.count(),
                "media": Media.query.count(),
                "posts": Post.query.filter_by(status="published").count(),
            }
            return DatabaseStats(**stats)
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
            # 返回零值而不是抛出异常
            return DatabaseStats()

    @staticmethod
    def get_database_size_mb() -> float:
        """
        获取数据库大小（MB）

        Returns:
            float: 数据库大小（MB），查询失败返回 0.0
        """
        try:
            # 获取当前数据库名
            result = db_session.session.execute(text("SELECT DATABASE()"))
            db_name = result.scalar()

            if not db_name:
                return 0.0

            # 查询数据库大小
            query = text("""
                SELECT
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
                FROM information_schema.tables
                WHERE table_schema = :db_name
                GROUP BY table_schema
            """)
            result = db_session.session.execute(query, {"db_name": db_name})
            size = result.scalar()

            return float(size) if size else 0.0
        except Exception as e:
            logger.error(f"获取数据库大小失败: {e}")
            return 0.0

    @staticmethod
    def get_system_info() -> SystemInfoResponse:
        """
        获取系统完整信息

        Returns:
            SystemInfoResponse: 系统信息
        """
        database_stats = SystemService.get_database_stats()
        database_size_mb = SystemService.get_database_size_mb()

        return SystemInfoResponse(
            version="2.0.0",
            database_stats=database_stats,
            database_size_mb=database_size_mb,
        )
