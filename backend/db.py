"""
数据库连接适配器
支持多种SQL数据库：MySQL, SQLite, PostgreSQL
"""
import os
from config import config

# 数据库类型配置
DB_TYPE = os.getenv('DB_TYPE', 'mysql')  # mysql, sqlite, postgresql


class DatabaseAdapter:
    """数据库适配器基类"""

    def __init__(self):
        self.connection = None

    def get_connection(self):
        raise NotImplementedError

    def get_placeholder(self):
        """返回SQL参数占位符"""
        raise NotImplementedError

    def close(self):
        if self.connection:
            self.connection.close()


class MySQLAdapter(DatabaseAdapter):
    """MySQL适配器"""

    def __init__(self):
        import pymysql
        self.pymysql = pymysql
        self.connection = None

    def get_connection(self):
        if self.connection is None:
            try:
                # 禁用 TINYINT 到 bool 的自动转换，保持为整数
                conv = self.pymysql.converters.conversions.copy()
                conv[self.pymysql.constants.FIELD_TYPE.TINY] = int

                self.connection = self.pymysql.connect(
                    host=config['default'].MYSQL_HOST,
                    port=config['default'].MYSQL_PORT,
                    user=config['default'].MYSQL_USER,
                    password=config['default'].MYSQL_PASSWORD,
                    database=config['default'].MYSQL_DATABASE,
                    charset=config['default'].MYSQL_CHARSET,
                    cursorclass=self.pymysql.cursors.DictCursor,
                    conv=conv  # 禁用 TINYINT -> bool 转换
                )
                print(f"[OK] MySQL连接成功: {config['default'].MYSQL_DATABASE}")
            except Exception as e:
                print(f"[ERROR] MySQL连接失败: {e}")
                raise
        return self.connection

    def get_placeholder(self):
        return "%s"


class SQLiteAdapter(DatabaseAdapter):
    """SQLite适配器"""

    def __init__(self):
        import sqlite3
        self.sqlite3 = sqlite3
        # SQLite数据库文件路径
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ai_web_dev.db')
        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self):
        if self.connection is None:
            try:
                self.connection = self.sqlite3.connect(self.db_path)
                self.connection.row_factory = self.sqlite3.Row  # 返回字典格式
                print(f"[OK] SQLite连接成功: {self.db_path}")
            except Exception as e:
                print(f"[ERROR] SQLite连接失败: {e}")
                raise
        return self.connection

    def get_cursor(self, connection):
        """返回支持字典的游标"""
        return connection.cursor()

    def get_placeholder(self):
        return "?"


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL适配器"""

    def __init__(self):
        try:
            import psycopg2
            import psycopg2.extras
            self.psycopg2 = psycopg2
            self.extras = psycopg2.extras
        except ImportError:
            raise ImportError("请安装psycopg2: pip install psycopg2-binary")
        self.connection = None

    def get_connection(self):
        if self.connection is None:
            try:
                self.connection = self.psycopg2.connect(
                    host=config['default'].MYSQL_HOST,  # 复用配置
                    port=config['default'].MYSQL_PORT,
                    user=config['default'].MYSQL_USER,
                    password=config['default'].MYSQL_PASSWORD,
                    database=config['default'].MYSQL_DATABASE,
                )
                print(f"[OK] PostgreSQL连接成功: {config['default'].MYSQL_DATABASE}")
            except Exception as e:
                print(f"[ERROR] PostgreSQL连接失败: {e}")
                raise
        return self.connection

    def get_placeholder(self):
        return "%s"


def get_db_adapter():
    """根据配置返回对应的数据库适配器"""
    db_type = os.getenv('DB_TYPE', 'mysql').lower()

    if db_type == 'mysql':
        return MySQLAdapter()
    elif db_type == 'sqlite':
        return SQLiteAdapter()
    elif db_type == 'postgresql' or db_type == 'postgres':
        return PostgreSQLAdapter()
    else:
        raise ValueError(f"不支持的数据库类型: {db_type}")


# 全局数据库适配器实例
db_adapter = None


def get_db_connection():
    """获取数据库连接（兼容旧接口）"""
    global db_adapter
    if db_adapter is None:
        db_adapter = get_db_adapter()

    conn = db_adapter.get_connection()

    # 对于SQLite，需要特殊处理游标
    if isinstance(db_adapter, SQLiteAdapter):
        return db_adapter.get_cursor(conn), conn

    return conn


def get_placeholder():
    """获取SQL参数占位符"""
    global db_adapter
    if db_adapter is None:
        db_adapter = get_db_adapter()
    return db_adapter.get_placeholder()


def close_db_connection():
    """关闭数据库连接"""
    global db_adapter
    if db_adapter:
        db_adapter.close()
        db_adapter = None
