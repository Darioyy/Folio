"""
Flask应用主入口
学习要点：Flask应用初始化、路由注册、CORS配置、错误处理
"""
import os
import pymysql
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# 导入配置
from config import config

# 初始化数据库连接（全局连接池，学习点：连接管理）
db_connection = None


def get_db_connection():
    """
    获取数据库连接
    学习要点：连接池、异常处理、资源管理
    """
    global db_connection
    if db_connection is None:
        try:
            db_connection = pymysql.connect(
                host=config['default'].MYSQL_HOST,
                port=config['default'].MYSQL_PORT,
                user=config['default'].MYSQL_USER,
                password=config['default'].MYSQL_PASSWORD,
                database=config['default'].MYSQL_DATABASE,
                charset=config['default'].MYSQL_CHARSET,
                cursorclass=pymysql.cursors.DictCursor
            )
            print(f"[OK] 数据库连接成功: {config['default'].MYSQL_DATABASE}")
        except pymysql.Error as e:
            print(f"[ERROR] 数据库连接失败: {e}")
            print("\n请检查:")
            print("1. MySQL服务是否启动")
            print("2. 数据库是否已创建 (运行: mysql -u root -p < database/init.sql)")
            print("3. config.py中的数据库配置是否正确")
            raise
    return db_connection


def create_app(config_name='development'):
    """
    应用工厂函数
    学习要点：应用工厂模式、配置注入、蓝图注册
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 启用CORS - 允许前端跨域访问
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 注册蓝图（路由模块）
    from api import (
        user_bp,      # 用户相关API
        post_bp,      # 文章相关API
        resource_bp,  # 资源相关API
        media_bp,     # 媒体相关API
        system_bp     # 系统相关API
    )
    app.register_blueprint(user_bp, url_prefix=f"{app.config['API_PREFIX']}/users")
    app.register_blueprint(post_bp, url_prefix=f"{app.config['API_PREFIX']}/posts")
    app.register_blueprint(resource_bp, url_prefix=f"{app.config['API_PREFIX']}/resources")
    app.register_blueprint(media_bp, url_prefix=f"{app.config['API_PREFIX']}/media")
    app.register_blueprint(system_bp, url_prefix=f"{app.config['API_PREFIX']}/system")

    # 全局错误处理
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': '请求参数错误', 'message': str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': '资源未找到', 'message': str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': '服务器内部错误', 'message': str(error)}), 500

    # 健康检查端点
    @app.route('/health')
    def health_check():
        """健康检查 - 用于测试服务是否运行"""
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'version': '1.0.0'
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }), 500

    # API根路径
    @app.route('/api')
    def api_root():
        """API根路径 - 返回可用端点列表"""
        return jsonify({
            'name': 'AI Web Dev API',
            'version': '1.0.0',
            'endpoints': {
                'users': f"{app.config['API_PREFIX']}/users",
                'posts': f"{app.config['API_PREFIX']}/posts",
                'resources': f"{app.config['API_PREFIX']}/resources",
                'media': f"{app.config['API_PREFIX']}/media",
                'system': f"{app.config['API_PREFIX']}/system"
            }
        })

    # 静态文件服务 - 提供上传文件的访问
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        """提供上传文件的访问"""
        # 获取项目根目录的绝对路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        uploads_dir = os.path.join(project_root, 'uploads')
        return send_from_directory(uploads_dir, filename)

    return app


if __name__ == '__main__':
    print("\n" + "="*50)
    print("启动 Flask 开发服务器")
    print("="*50)

    # 测试数据库连接
    try:
        get_db_connection()
    except Exception as e:
        print(f"\n启动失败: {e}")
        exit(1)

    # 创建应用
    app = create_app('development')

    print(f"\n[OK] 应用已启动")
    print(f"  - 本地地址: http://localhost:5000")
    print(f"  - API文档: http://localhost:5000/api")
    print(f"  - 健康检查: http://localhost:5000/health")
    print("\n按 Ctrl+C 停止服务器\n")

    # 启动开发服务器
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )