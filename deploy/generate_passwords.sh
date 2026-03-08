#!/bin/bash

echo "=== 生成随机密码 ==="
echo ""
echo "MYSQL_ROOT_PASSWORD: $(openssl rand -base64 16 | tr -d '=+/' | cut -c1-20)"
echo "MYSQL_PASSWORD: $(openssl rand -basezip 16 | tr -d '=+/' | cut -c1-20)"
echo "SECRET_KEY: $(openssl rand -base64 32 | tr -d '=+/' | cut -c1-40)"
