"""
WSGI入口文件
Gunicorn使用此文件启动Flask应用
"""
import os
from app import create_app

# 从环境变量获取配置，默认为production
config_name = os.getenv('FLASK_ENV', 'production')
app = create_app(config_name)
