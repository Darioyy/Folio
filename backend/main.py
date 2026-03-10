"""
Flask 应用主入口 - 三层架构版本
整合 SQLAlchemy ORM 和新的 API v1
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# 导入配置
from config.default import Config, DevelopmentConfig, ProductionConfig

# 导入数据库
from db.session import init_db, db as db_session

# 导入 API v1 蓝图
from api.v1 import users_bp, media_bp, resources_bp, posts_bp, system_bp, hub_bp


# 配置日志
def setup_logging(app):
    """配置日志系统"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_level = logging.DEBUG if app.debug else logging.INFO

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # 文件处理器
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

    Args:
        config_name: 配置名称 ('development', 'production', 'testing')

    Returns:
        Flask 应用实例
    """
    app = Flask(__name__)

    # 加载配置
    if config_name == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    app.config['JSON_AS_ASCII'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    # 配置代理头（用于 Nginx 反向代理）
    app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

    # 配置日志
    setup_logging(app)

    # 初始化数据库
    try:
        init_db(app)
        app.logger.info(f"数据库连接成功: {app.config['MYSQL_DATABASE']}")
    except Exception as e:
        app.logger.error(f"数据库连接失败: {e}")
        raise

    # 配置 session
    app.secret_key = app.config['SECRET_KEY']

    # 配置 CORS
    is_dev = app.debug
    if is_dev:
        origins = ["http://localhost:5000", "http://127.0.0.1:5000",
                   "http://localhost:5500", "http://127.0.0.1:5500"]
    else:
        site_url = os.environ.get('SITE_URL', 'http://121.40.237.168')
        origins = [site_url, 'http://121.40.237.168', 'http://121.40.237.168/admin.html']

    CORS(app, resources={
        r"/api/*": {
            "origins": origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })

    # 注册蓝图
    api_prefix = app.config['API_PREFIX']
    app.register_blueprint(users_bp, url_prefix=f"{api_prefix}/users")
    app.register_blueprint(media_bp, url_prefix=f"{api_prefix}/media")
    app.register_blueprint(resources_bp, url_prefix=f"{api_prefix}/resources")
    app.register_blueprint(posts_bp, url_prefix=f"{api_prefix}/posts")
    app.register_blueprint(system_bp, url_prefix=f"{api_prefix}/system")
    app.register_blueprint(hub_bp, url_prefix=f"{api_prefix}/hub")

    # 健康检查端点
    @app.route('/health')
    def health_check():
        """健康检查"""
        try:
            from sqlalchemy import text
            db_session.session.execute(text("SELECT 1"))
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'version': '2.0.0'
            })
        except Exception as e:
            app.logger.error(f"Health Check Failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }), 500

    # API 根路径
    @app.route('/api')
    def api_root():
        """API 根路径"""
        return jsonify({
            'name': 'AI Web Dev API',
            'version': '2.0.0',
            'architecture': 'three-tier',
            'endpoints': {
                'users': f"{api_prefix}/users",
                'media': f"{api_prefix}/media",
                'resources': f"{api_prefix}/resources",
                'posts': f"{api_prefix}/posts",
                'system': f"{api_prefix}/system",
                'hub': f"{api_prefix}/hub",
                'login': f"{api_prefix}/users/login",
                'register': f"{api_prefix}/users/register"
            }
        })

    # 静态文件服务
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        """提供上传文件的访问"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        uploads_dir = os.path.join(project_root, 'uploads')

        # 安全检查
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            app.logger.warning(f"检测到路径遍历尝试: {filename}")
            return jsonify({'error': '非法的文件路径'}), 403

        full_path = os.path.abspath(os.path.join(uploads_dir, filename))
        uploads_abs = os.path.abspath(uploads_dir)
        if not full_path.startswith(uploads_abs):
            app.logger.warning(f"检测到路径遍历尝试: {filename}")
            return jsonify({'error': '非法的文件路径'}), 403

        if not os.path.exists(full_path):
            return jsonify({'error': '文件不存在'}), 404

        return send_from_directory(uploads_dir, filename)

    # 全局错误处理
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f"Bad Request: {error}")
        return jsonify({'success': False, 'error': {'code': 'BAD_REQUEST', 'message': str(error)}}), 400

    @app.errorhandler(404)
    def not_found(error):
        app.logger.info(f"Not Found: {request.path}")
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': str(error)}}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal Error: {error}")
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': str(error)}}), 500

    return app


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("启动 Flask 开发服务器 (三层架构版)")
    print("=" * 50)

    app = create_app('development')

    print(f"\n[OK] 应用已启动")
    print(f"  - 本地地址: http://localhost:5000")
    print(f"  - API文档: http://localhost:5000/api")
    print(f"  - 健康检查: http://localhost:5000/health")
    print(f"\n[架构] 三层架构 (API -> Service -> Model)")
    print(f"[ORM] SQLAlchemy 2.0")
    print(f"[验证] Pydantic v2")
    print("\n按 Ctrl+C 停止服务器\n")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
