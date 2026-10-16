"""
Flask 应用主入口 - 三层架构版本
整合 SQLAlchemy ORM 和新的 API v1
"""
import os
import logging
import threading
import time
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# 导入配置
from config.default import Config, DevelopmentConfig, ProductionConfig

# 导入数据库
from db.session import init_db, db as db_session

# 导入 API v1 蓝图
from api.v1 import (users_bp, posts_bp, post_interactions_bp,
                    system_bp, hub_bp, files_bp, groups_bp, interactions_bp,
                    comments_bp, notifications_bp, search_bp, feedback_bp, tools_bp)
from extensions import limiter


# 配置日志
def setup_logging(app):
    """配置日志系统"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_level = logging.DEBUG if app.debug else logging.INFO

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )

    # 文件处理器：每日轮转，保留 30 天，超期文件自动删除
    file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        when='midnight',
        backupCount=30,
        encoding='utf-8',
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


def _run_notification_cleanup(app):
    """后台 daemon 线程：每 24 小时清理 90 天前的通知记录"""
    while True:
        time.sleep(24 * 3600)
        with app.app_context():
            try:
                from sqlalchemy import delete as sa_delete
                from core.models.notification import Notification
                from db.session import db as _db
                cutoff = datetime.utcnow() - timedelta(days=90)
                result = _db.session.execute(
                    sa_delete(Notification).where(Notification.created_at < cutoff)
                )
                _db.session.commit()
                app.logger.info(f'通知清理完成，删除 {result.rowcount} 条 90 天前记录')
            except Exception as e:
                app.logger.error(f'通知清理失败: {e}')


def create_app(config_name=None):
    """
    应用工厂函数

    Args:
        config_name: 配置名称，None 时自动读取 FLASK_ENV 环境变量

    Returns:
        Flask 应用实例
    """
    # P3: 读取 FLASK_ENV 环境变量，不再硬编码
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)

    # 加载配置
    if config_name == 'production':
        app.config.from_object(ProductionConfig)
        # S-4: 生产环境 SECRET_KEY 必须来自环境变量，禁止使用弱默认值
        secret = app.config.get('SECRET_KEY', '')
        if not secret or secret == 'dev-secret-key-change-in-production':
            raise RuntimeError("生产环境必须在 .env 中设置 SECRET_KEY 环境变量")
    else:
        app.config.from_object(DevelopmentConfig)

    app.config['JSON_AS_ASCII'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    # S-5: 确保文件上传大小限制生效
    app.config['MAX_CONTENT_LENGTH'] = app.config.get('MAX_FILE_SIZE', 16 * 1024 * 1024)

    # P2: 配置代理头（补全 x_for + x_proto，影响真实 IP 识别和 HTTPS 检测）
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_prefix=1)

    # 配置日志
    setup_logging(app)

    # 初始化扩展
    limiter.init_app(app)

    # 初始化数据库
    try:
        init_db(app)
        app.logger.info(f"数据库连接成功: {app.config['MYSQL_DATABASE']}")
    except Exception as e:
        app.logger.error(f"数据库连接失败: {e}")
        raise

    # 配置 session
    app.secret_key = app.config['SECRET_KEY']

    # 配置 CORS — P3: 从 CORS_ORIGINS 环境变量读取，禁止硬编码 IP
    is_dev = app.debug
    if is_dev:
        raw = os.environ.get(
            'CORS_ORIGINS',
            'http://localhost:5000,http://127.0.0.1:5000,http://localhost:5173,http://127.0.0.1:5173'
        )
        origins = [o.strip() for o in raw.split(',') if o.strip()]
    else:
        raw = os.environ.get('CORS_ORIGINS', '')
        if not raw:
            raise RuntimeError("生产环境必须在 .env 中设置 CORS_ORIGINS 环境变量")
        origins = [o.strip() for o in raw.split(',') if o.strip()]

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
    app.register_blueprint(posts_bp, url_prefix=f"{api_prefix}/posts")
    app.register_blueprint(post_interactions_bp, url_prefix=f"{api_prefix}/posts")
    app.register_blueprint(system_bp, url_prefix=f"{api_prefix}/system")
    app.register_blueprint(hub_bp, url_prefix=f"{api_prefix}/hub")
    app.register_blueprint(files_bp, url_prefix=f"{api_prefix}/files")
    app.register_blueprint(groups_bp, url_prefix=f"{api_prefix}/groups")
    app.register_blueprint(interactions_bp, url_prefix=f"{api_prefix}/files")
    app.register_blueprint(comments_bp, url_prefix=f"{api_prefix}")
    app.register_blueprint(notifications_bp, url_prefix=f"{api_prefix}/notifications")
    app.register_blueprint(search_bp, url_prefix=f"{api_prefix}/search")
    app.register_blueprint(feedback_bp, url_prefix=f"{api_prefix}/feedback")
    app.register_blueprint(tools_bp, url_prefix=f"{api_prefix}/tools")

    # S-6: 安全响应头（API 响应层）
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # X-XSS-Protection 已被现代浏览器废弃，改由 CSP 负责
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        # 敏感 API 响应禁止缓存
        if response.content_type.startswith('application/json'):
            response.headers.setdefault('Cache-Control', 'no-store')
        return response

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
                'version': '3.3.1'
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
            'name': 'Folio API',
            'version': '3.3.1',
            'architecture': 'three-tier',
            'endpoints': {
                'users': f"{api_prefix}/users",
                'posts': f"{api_prefix}/posts",
                'files': f"{api_prefix}/files",
                'search': f"{api_prefix}/search",
                'feedback': f"{api_prefix}/feedback",
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
        # uploads/ 与 Config.UPLOAD_FOLDER 保持一致：backend/uploads/
        uploads_dir = os.path.abspath(Config.UPLOAD_FOLDER)

        # 安全检查
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            app.logger.warning(f"检测到路径遍历尝试: {filename}")
            return jsonify({'error': '非法的文件路径'}), 403

        full_path = os.path.realpath(os.path.abspath(os.path.join(uploads_dir, filename)))
        uploads_abs = os.path.realpath(os.path.abspath(uploads_dir))
        if not full_path.startswith(uploads_abs + os.sep):
            app.logger.warning(f"检测到路径遍历尝试: {filename}")
            return jsonify({'error': '非法的文件路径'}), 403

        if not os.path.exists(full_path):
            return '', 404

        return send_from_directory(uploads_dir, filename)

    # 全局错误处理
    @app.errorhandler(429)
    def rate_limited(error):
        return jsonify({'success': False, 'error': {'code': 'RATE_LIMITED', 'message': '请求过于频繁，请稍后再试'}}), 429

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

    # 启动后台通知清理线程（非测试环境，daemon=True 随主进程退出）
    if config_name != 'testing':
        t = threading.Thread(target=_run_notification_cleanup, args=(app,), daemon=True)
        t.start()
        app.logger.info('通知清理后台线程已启动')

    return app


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("Folio")
    print("=" * 50)

    app = create_app()

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
