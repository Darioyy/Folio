"""
默认配置文件
"""
import os
from datetime import timedelta
from urllib.parse import quote_plus
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """基础配置类"""

    # Flask 配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # 数据库配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'folio')
    MYSQL_CHARSET = 'utf8mb4'

    # SQLAlchemy 配置（密码需要 URL 编码以处理特殊字符）
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{quote_plus(MYSQL_PASSWORD)}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
        f"?charset={MYSQL_CHARSET}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Redis 配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    REDIS_URL = f"redis://{':' + REDIS_PASSWORD + '@' if REDIS_PASSWORD else ''}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    # Flask-Limiter 存储（生产环境用 Redis，多进程间共享限速状态）
    RATELIMIT_STORAGE_URI = REDIS_URL

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'documents': {'pdf', 'doc', 'docx', 'txt', 'md'},
        'videos': {'mp4', 'webm', 'avi'}
    }
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

    # API 配置
    API_PREFIX = '/api/v1'

    # JWT 配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 7 * 24 * 60 * 60  # 7天

    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    RATELIMIT_STORAGE_URI = "memory://"  # 开发环境无需 Redis


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    # SESSION_COOKIE_SECURE = True  # 待上线 HTTPS 后再启用，HTTP 下启用会导致 Cookie 无法发送
    RATELIMIT_STORAGE_URI = "memory://"  # 无 Redis 依赖，2核2G 服务器适用
    # P2: 生产连接池，防止高并发下连接耗尽
    # pool_recycle=300 < MySQL wait_timeout=600，留 5 分钟裕量防止连接被服务端提前关闭
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,
        "max_overflow": 2,
        "pool_recycle": 300,
        "pool_timeout": 10,
        "pool_pre_ping": True,
    }


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_ECHO = False
