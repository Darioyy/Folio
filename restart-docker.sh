#!/bin/bash
# 重置Docker环境（会删除数据库数据，慎用！）

echo "⚠️  警告：此操作将删除所有数据库数据！"
echo "按 Ctrl+C 取消，按回车继续..."
read

# 停止并删除容器
docker compose down

# 删除数据库卷
docker volume rm ai_web_dev_mysql_data

# 重新启动
docker compose up -d

echo "✅ Docker环境已重置"
echo "等待数据库初始化（约30秒）..."
sleep 30

echo "✅ 完成！现在可以访问应用了"
