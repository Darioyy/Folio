"""
系统服务层 - 业务逻辑
"""
import os
import json
import secrets
import string
from datetime import datetime, timedelta
from sqlalchemy import text, func, select, case
from db.session import db as db_session
from core.models.user import User
from core.models.category import Category
from core.models.file import File
from core.models.post import Post
from core.schemas.system import DatabaseStats, SystemInfoResponse, AdminStats, FileCategoryStats
import logging

logger = logging.getLogger(__name__)

_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'system.json')

_DEFAULT_CONFIG = {
    "register_enabled": True,
    "invite_code_required": False,
    "captcha_enabled": True,
    "storage_quota_root": 10737418240,   # 10 GB
    "storage_quota_admin": 5368709120,   # 5 GB
    "storage_quota_user": 1073741824,    # 1 GB
    "max_file_size": 16777216,
    "allowed_extensions": "png,jpg,jpeg,gif,webp,mp4,webm,avi,pdf,doc,docx,txt,md,zip,rar",
    "invite_codes": []
}


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
            session = db_session.session

            # 单次查询所有文件分类统计
            cat_rows = session.execute(
                select(File.file_category, func.count(File.id).label('cnt'))
                .group_by(File.file_category)
            ).all()
            cat_map = {row.file_category: row.cnt for row in cat_rows}

            stats = {
                "users": session.execute(select(func.count(User.id))).scalar() or 0,
                "categories": session.execute(select(func.count(Category.id))).scalar() or 0,
                "resources": cat_map.get('resource', 0),
                "media": cat_map.get('image', 0) + cat_map.get('video', 0),
                "posts": session.execute(
                    select(func.count(Post.id)).where(Post.status == "published")
                ).scalar() or 0,
            }
            return DatabaseStats(**stats)
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
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

    @staticmethod
    def get_admin_stats() -> AdminStats:
        """
        获取管理员数据概览（含各分类文件数、存储总量、近7天新增用户）

        Returns:
            AdminStats
        """
        try:
            session = db_session.session

            # 单次查询：按分类统计文件数 + 总存储
            cat_rows = session.execute(
                select(
                    File.file_category,
                    func.count(File.id).label('cnt'),
                    func.sum(File.file_size).label('sz'),
                ).group_by(File.file_category)
            ).all()
            cat_counts = {'image': 0, 'video': 0, 'resource': 0, 'document': 0}
            storage_total = 0
            for row in cat_rows:
                if row.file_category in cat_counts:
                    cat_counts[row.file_category] = row.cnt
                storage_total += (row.sz or 0)

            # 单次查询：总用户数 + 近 7 天新增
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            user_stats = session.execute(
                select(
                    func.count(User.id).label('total'),
                    func.sum(case((User.created_at >= seven_days_ago, 1), else_=0)).label('new_7d'),
                )
            ).one()

            return AdminStats(
                users_total=user_stats.total or 0,
                files_total=sum(cat_counts.values()),
                files_by_category=FileCategoryStats(**cat_counts),
                storage_total=int(storage_total),
                new_users_7d=int(user_stats.new_7d or 0),
            )
        except Exception as e:
            logger.error(f"获取管理员统计失败: {e}")
            return AdminStats()

    # -----------------------------------------------------------------------
    # 系统配置（JSON 文件存储）
    # -----------------------------------------------------------------------

    @staticmethod
    def load_config() -> dict:
        """读取系统配置，缺失字段回退到默认值"""
        try:
            with open(_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for k, v in _DEFAULT_CONFIG.items():
                if k not in data:
                    data[k] = v
            return data
        except (FileNotFoundError, json.JSONDecodeError):
            return dict(_DEFAULT_CONFIG)

    @staticmethod
    def save_config(config: dict) -> None:
        """将配置写回 JSON 文件"""
        os.makedirs(os.path.dirname(_CONFIG_FILE), exist_ok=True)
        with open(_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2, default=str)

    # -----------------------------------------------------------------------
    # 内测码管理
    # -----------------------------------------------------------------------

    @staticmethod
    def list_invite_codes() -> list:
        """返回所有内测码列表"""
        config = SystemService.load_config()
        return config.get('invite_codes', [])

    @staticmethod
    def generate_invite_code() -> dict:
        """生成随机 8 位内测码（大写字母+数字）"""
        alphabet = string.ascii_uppercase + string.digits
        code = ''.join(secrets.choice(alphabet) for _ in range(8))
        entry = {
            'code': code,
            'used': False,
            'used_by': None,
            'used_at': None,
            'created_at': datetime.utcnow().isoformat(),
        }
        config = SystemService.load_config()
        config.setdefault('invite_codes', []).append(entry)
        SystemService.save_config(config)
        return entry

    @staticmethod
    def validate_and_use_invite_code(code: str, username: str) -> bool:
        """
        校验内测码并标记已使用。

        Returns:
            True  - 校验通过（码存在且未使用）
            False - 码不存在或已被使用
        """
        config = SystemService.load_config()
        codes = config.get('invite_codes', [])
        for entry in codes:
            if entry.get('code') == code:
                if entry.get('used'):
                    return False
                entry['used'] = True
                entry['used_by'] = username
                entry['used_at'] = datetime.utcnow().isoformat()
                SystemService.save_config(config)
                return True
        return False

    @staticmethod
    def delete_invite_code(code: str) -> bool:
        """删除指定内测码，返回是否找到并删除"""
        config = SystemService.load_config()
        codes = config.get('invite_codes', [])
        original_len = len(codes)
        config['invite_codes'] = [c for c in codes if c['code'] != code]
        if len(config['invite_codes']) < original_len:
            SystemService.save_config(config)
            return True
        return False
