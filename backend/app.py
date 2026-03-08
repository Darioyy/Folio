"""
Flask应用主入口
学习要点：Flask应用初始化、路由注册、CORS配置、错误处理、日志系统
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# 导入配置
from config import config
from database import init_app as init_database, get_db_connection

# 配置日志
def setup_logging(app):
    """
    配置日志系统
    """
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # 设置日志级别
    log_level = logging.DEBUG if app.config['DEBUG'] else logging.INFO

    # 创建格式化器
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # 文件处理器（自动轮转）
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # 配置应用日志
    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)

    # 禁用 Werkzeug 默认日志
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)

    app.logger.info('日志系统初始化完成')


def create_app(config_name='development'):
    """
    应用工厂函数
    学习要点：应用工厂模式、配置注入、蓝图注册
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.config['JSON_AS_ASCII'] = False  # 确保JSON正确处理中文

    # 配置日志
    setup_logging(app)

    # 初始化数据库连接池
    try:
        init_database(app)
        app.logger.info(f"数据库连接成功: {app.config['MYSQL_DATABASE']}")
    except Exception as e:
        app.logger.error(f"数据库连接失败: {e}")
        raise

    # 配置session
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    # 只有在使用HTTPS时才启用SECURE cookie
    # 从环境变量或请求头判断是否使用HTTPS
    is_https = os.environ.get('HTTPS', 'off').lower() == 'on'
    if is_https:
        app.config['SESSION_COOKIE_SECURE'] = True

    # 启用CORS
    is_dev = os.environ.get('FLASK_ENV', 'development') == 'development'
    if is_dev:
        # 开发环境：本地地址
        origins = ["http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:5500", "http://127.0.0.1:5500"]
    else:
        # 生产环境：使用实际域名（从环境变量获取或使用通配符）
        # 注意：使用 supports_credentials: True 时，不能使用 "*"，必须指定具体域名
        site_url = os.environ.get('SITE_URL', 'http://121.40.237.168')
        origins = [site_url, 'http://121.40.237.168', 'http://121.40.237.168/admin.html']

    CORS(app, resources={
        r"/api/*": {
            "origins": origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True,
            "max_age": 3600,
            "expose_headers": ["Content-Type", "Authorization", "Set-Cookie"]
        }
    })

    # 注册蓝图
    from api import (
        user_bp, post_bp, resource_bp, media_bp, system_bp
    )
    app.register_blueprint(user_bp, url_prefix=f"{app.config['API_PREFIX']}/users")
    app.register_blueprint(post_bp, url_prefix=f"{app.config['API_PREFIX']}/posts")
    app.register_blueprint(resource_bp, url_prefix=f"{app.config['API_PREFIX']}/resources")
    app.register_blueprint(media_bp, url_prefix=f"{app.config['API_PREFIX']}/media")
    app.register_blueprint(system_bp, url_prefix=f"{app.config['API_PREFIX']}/system")

    # 全局错误处理
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f"Bad Request: {error}")
        return jsonify({'error': '请求参数错误', 'message': str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        app.logger.info(f"Not Found: {request.path}")
        return jsonify({'error': '资源未找到', 'message': str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal Error: {error}")
        return jsonify({'error': '服务器内部错误', 'message': str(error)}), 500

    # 健康检查端点
    @app.route('/health')
    def health_check():
        """健康检查"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'version': '1.0.0'
            })
        except Exception as e:
            app.logger.error(f"Health Check Failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }), 500

    # API根路径
    @app.route('/api')
    def api_root():
        """API根路径"""
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

    # 静态文件服务（安全版本）
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        """提供上传文件的访问（带安全检查）"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        uploads_dir = os.path.join(project_root, 'uploads')

        # 安全检查：防止路径遍历攻击
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            app.logger.warning(f"检测到路径遍历尝试: {filename}")
            return jsonify({'error': '非法的文件路径'}), 403

        # 检查文件是否在uploads目录内
        full_path = os.path.abspath(os.path.join(uploads_dir, filename))
        uploads_abs = os.path.abspath(uploads_dir)
        if not full_path.startswith(uploads_abs):
            app.logger.warning(f"检测到路径遍历尝试: {filename}, full_path: {full_path}")
            return jsonify({'error': '非法的文件路径'}), 403

        # 检查文件是否存在
        if not os.path.exists(full_path):
            return jsonify({'error': '文件不存在'}), 404

        return send_from_directory(uploads_dir, filename)

    return app


if __name__ == '__main__':
    print("\n" + "="*50)
    print("启动 Flask 开发服务器")
    print("="*50)

    app = create_app('development')

    print(f"\n[OK] 应用已启动")
    print(f"  - 本地地址: http://localhost:5000")
    print(f"  - API文档: http://localhost:5000/api")
    print(f"  - 健康检查: http://localhost:5000/health")
    print("\n按 Ctrl+C 停止服务器\n")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
