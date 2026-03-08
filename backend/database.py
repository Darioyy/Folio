"""
数据库连接管理模块（重构版 - 解决TINYINT布尔值转换问题）
特性：
- 自动事务管理（上下文管理器自动提交/回滚）
- 连接重试机制
- 统一错误处理
- 详细的日志记录
- 多进程安全
- 资源优化（适合2核2G服务器）
- TINYINT字段返回整数而非布尔值
"""
import os
import time
import logging
import pymysql
from functools import wraps
from contextlib import contextmanager
from flask import g, current_app

# 配置日志
logger = logging.getLogger(__name__)

# 数据库配置类
class DatabaseConfig:
    """数据库配置"""
    def __init__(self, app_config):
        self.host = app_config.get('MYSQL_HOST', 'localhost')
        self.port = int(app_config.get('MYSQL_PORT', 3306))
        self.user = app_config.get('MYSQL_USER', 'root')
        self.password = app_config.get('MYSQL_PASSWORD', '')
        self.database = app_config.get('MYSQL_DATABASE', 'ai_web_dev')
        self.charset = app_config.get('MYSQL_CHARSET', 'utf8mb4')
        # 低配服务器优化：缩短超时时间
        self.connect_timeout = 5  # 连接超时5秒
        self.read_timeout = 15    # 读取超时15秒
        self.write_timeout = 15   # 写入超时15秒

    def __repr__(self):
        return f"DatabaseConfig(host={self.host}, db={self.database}, user={self.user})"


# 全局配置
_db_config = None


def init_database(app_config):
    """
    初始化数据库配置
    在应用启动时调用
    """
    global _db_config
    _db_config = DatabaseConfig(app_config)
    logger.info(f"数据库配置初始化: {_db_config}")


def get_db_config():
    """获取数据库配置"""
    global _db_config
    if _db_config is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    return _db_config


def create_connection():
    """
    创建新的数据库连接
    每次调用都会创建新连接（适合小型应用）

    连接参数说明：
    - autocommit=False: 手动控制事务
    - conv: 自定义转换器，让TINYINT返回整数而非布尔值（关键修复！）
    """
    cfg = get_db_config()

    # 创建转换器字典，禁用 TINYINT -> bool 转换
    # 这是解决权限检查问题的核心修复
    conv = pymysql.converters.conversions.copy()
    conv[pymysql.constants.FIELD_TYPE.TINY] = int

    return pymysql.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        charset=cfg.charset,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=cfg.connect_timeout,
        read_timeout=cfg.read_timeout,
        write_timeout=cfg.write_timeout,
        autocommit=False,  # 手动控制事务
        conv=conv  # 关键：让TINYINT返回整数
    )


def create_connection_with_retry(max_retries=2, retry_delay=0.5):
    """
    创建数据库连接（带重试机制）

    Args:
        max_retries: 最大重试次数（低配服务器减少到2次）
        retry_delay: 重试间隔（秒）

    Returns:
        数据库连接对象
    """
    cfg = get_db_config()
    last_error = None

    for attempt in range(max_retries):
        try:
            conn = create_connection()
            # 测试连接
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            if attempt > 0:
                logger.warning(f"数据库连接重试成功 (第 {attempt + 1} 次尝试)")
            return conn
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.warning(f"数据库连接失败 (第 {attempt + 1} 次尝试): {e}, {retry_delay}秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                logger.error(f"数据库连接失败，已达最大重试次数: {e}")

    raise last_error


@contextmanager
def get_db_connection(auto_commit=True):
    """
    获取数据库连接（上下文管理器）

    特性：
    - 自动处理事务：成功时提交，异常时回滚
    - 自动关闭连接
    - 详细的错误日志

    Args:
        auto_commit: 是否自动提交事务（默认True）

    Usage:
        # 自动提交模式（推荐）
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO ...")
        # 自动提交，无需手动 commit

        # 手动控制事务
        with get_db_connection(auto_commit=False) as conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO ...")
                conn.commit()
    """
    conn = None
    try:
        conn = create_connection_with_retry()
        yield conn

        # 自动提交事务
        if auto_commit:
            conn.commit()
            logger.debug(f"事务自动提交成功")

    except Exception as e:
        # 回滚事务
        if conn:
            try:
                conn.rollback()
                logger.error(f"事务已回滚: {e}")
            except Exception as rollback_error:
                logger.error(f"回滚失败: {rollback_error}")
        raise

    finally:
        # 关闭连接
        if conn:
            try:
                conn.close()
            except Exception as close_error:
                logger.error(f"关闭连接失败: {close_error}")


@contextmanager
def get_db_cursor():
    """
    获取数据库游标（简化的上下文管理器）

    自动获取连接、创建游标、提交事务、关闭连接

    Usage:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            results = cursor.fetchall()
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            yield cursor


# 便捷函数
def execute_query(sql, params=None, fetch_one=False, auto_commit=True):
    """
    执行SQL查询（便捷函数）

    Args:
        sql: SQL语句
        params: 参数（元组或字典）
        fetch_one: 是否只获取一条记录
        auto_commit: 是否自动提交

    Returns:
        查询结果（字典列表或单个字典）
    """
    with get_db_connection(auto_commit=auto_commit) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()


def execute_update(sql, params=None):
    """
    执行更新操作（便捷函数）

    Args:
        sql: SQL语句
        params: 参数

    Returns:
        影响的行数
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            result = cursor.execute(sql, params)
            return cursor.rowcount


def execute_insert(sql, params=None):
    """
    执行插入操作（便捷函数）

    Args:
        sql: SQL语句
        params: 参数

    Returns:
        新插入记录的ID
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.lastrowid


# Flask 请求钩子支持
def init_app(app):
    """
    初始化 Flask 应用扩展
    """
    init_database(app.config)

    @app.before_request
    def before_request():
        """请求开始前的钩子"""
        g.db_start_time = time.time()

    @app.teardown_request
    def teardown_request(exception=None):
        """请求结束后的钩子"""
        if hasattr(g, 'db_start_time'):
            db_time = time.time() - g.db_start_time
            if db_time > 2.0:  # 超过2秒记录警告（低配服务器调整）
                logger.warning(f"慢请求: {db_time:.2f}秒")


# 兼容旧接口
def init_db():
    """兼容旧的初始化函数"""
    if _db_config is None:
        # 从 config 模块导入
        from config import config
        init_database(config['default'].__dict__)


def close_pool():
    """兼容旧的关闭函数（无操作）"""
    pass


# 导出函数（兼容旧的 API）
__all__ = [
    'get_db_connection',
    'get_db_cursor',
    'execute_query',
    'execute_update',
    'execute_insert',
    'init_db',
    'init_database',
    'init_app',
    'close_pool',
]
