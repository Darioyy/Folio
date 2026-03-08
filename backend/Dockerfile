FROM python:3.11-slim

WORKDIR /app

# 使用阿里云镜像源
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 5000

# 启动命令 - 针对 2核2G 服务器优化
# -w 2: 2个worker进程（适合2核CPU）
# --threads 2: 每个worker 2个线程（总计4并发，适合2G内存）
# --worker-class sync: 同步worker（更稳定）
# --timeout 60: 请求超时60秒
# --max-requests 500: 处理500个请求后重启worker（防止内存泄漏）
# --max-requests-jitter 50: 随机抖动，避免所有worker同时重启
# --graceful-timeout 20: 优雅关闭超时
# --worker-connections 1000: 每个worker处理1000个连接后重启
# --backlog 2048: 连接队列大小
# --keep-alive 2: 保持连接2秒
CMD ["gunicorn", \
     "-w", "2", \
     "--threads", "2", \
     "--worker-class", "sync", \
     "--timeout", "60", \
     "--max-requests", "500", \
     "--max-requests-jitter", "50", \
     "--graceful-timeout", "20", \
     "--worker-connections", "1000", \
     "--backlog", "2048", \
     "--keep-alive", "2", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "warning", \
     "--capture-output", \
     "--bind", "0.0.0.0:5000", \
     "wsgi:app"]
