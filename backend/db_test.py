#!/usr/bin/env python3
"""
数据库测试工具
用于在服务器上诊断数据库连接问题
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
import pymysql

# 加载环境变量
load_dotenv()


def test_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("数据库连接测试")
    print("=" * 60)

    # 显示配置
    print("\n【当前配置】")
    print(f"  主机: {os.getenv('MYSQL_HOST', 'localhost')}")
    print(f"  端口: {os.getenv('MYSQL_PORT', '3306')}")
    print(f"  用户: {os.getenv('MYSQL_USER', 'root')}")
    print(f"  数据库: {os.getenv('MYSQL_DATABASE', 'ai_web_dev')}")
    print(f"  密码: {'*' * len(os.getenv('MYSQL_PASSWORD', ''))}")

    # 测试连接
    print("\n【测试连接】")
    try:
        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'ai_web_dev'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        print("  ✅ 连接成功！")

        # 测试查询
        print("\n【测试查询】")
        with conn.cursor() as cursor:
            # 测试版本
            cursor.execute("SELECT VERSION() as version")
            result = cursor.fetchone()
            print(f"  MySQL 版本: {result['version']}")

            # 测试数据库
            cursor.execute("SELECT DATABASE() as db")
            result = cursor.fetchone()
            print(f"  当前数据库: {result['db']}")

            # 统计表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"  表数量: {len(tables)}")

            # 统计记录数（使用预定义SQL避免注入）
            print("\n【数据统计】")
            table_queries = {
                'users': "SELECT COUNT(*) as count FROM users",
                'categories': "SELECT COUNT(*) as count FROM categories",
                'posts': "SELECT COUNT(*) as count FROM posts",
                'resources': "SELECT COUNT(*) as count FROM resources",
                'media': "SELECT COUNT(*) as count FROM media"
            }
            for table, query in table_queries.items():
                try:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    print(f"  {table}: {result['count']} 条记录")
                except Exception as e:
                    print(f"  {table}: 查询失败 ({e})")

        conn.close()
        print("\n【测试完成】所有测试通过！")
        return True

    except Exception as e:
        print(f"\n  ❌ 连接失败: {e}")
        print("\n【故障排查建议】")
        print("  1. 检查 .env 文件配置是否正确")
        print("  2. 检查 MySQL 容器是否运行: docker ps")
        print("  3. 检查 MySQL 日志: docker logs ai_web_dev_mysql")
        print("  4. 检查网络连接: docker network ls")
        return False


if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
