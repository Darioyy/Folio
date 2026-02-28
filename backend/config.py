"""
配置文件 - 集中管理所有配置项
学习要点：环境变量、配置分离、敏感信息保护
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """基础配置类"""

    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = True

    # 数据库配置 - 学习MySQL连接参数
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'ai_web_dev')
    MYSQL_CHARSET = 'utf8mb4'

    # 文件上传配置 - 学习文件安全
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    ALLOWED_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'documents': {'pdf', 'doc', 'docx', 'txt', 'md'},
        'videos': {'mp4', 'webm', 'avi'}
    }
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

    # URL前缀
    API_PREFIX = '/api/v1'


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境强制从环境变量读取敏感信息
    SECRET_KEY = os.getenv('SECRET_KEY')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}