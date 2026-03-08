#!/usr/bin/env python3
"""
权限诊断和修复工具
用于检查和修复用户权限问题
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
import pymysql

# 加载环境变量
load_dotenv()


def check_permissions():
    """检查所有用户的权限状态"""
    print("=" * 60)
    print("用户权限检查")
    print("=" * 60)

    try:
        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'ai_web_dev'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )

        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, email, is_admin, is_root FROM users ORDER BY id")
            users = cursor.fetchall()

            print(f"\n找到 {len(users)} 个用户：\n")
            print(f"{'ID':<5} {'用户名':<20} {'邮箱':<30} {'Admin':<8} {'Root':<8}")
            print("-" * 75)

            for user in users:
                is_admin = "✓" if user.get('is_admin', 0) == 1 else "✗"
                is_root = "✓" if user.get('is_root', 0) == 1 else "✗"
                print(f"{user['id']:<5} {user['username']:<20} {user.get('email', ''):<30} {is_admin:<8} {is_root:<8}")

        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


def fix_user_permission(username, make_admin=False, make_root=False):
    """修复用户权限"""
    try:
        conn = pymysql.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'ai_web_dev'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
        )

        with conn.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT id, username, is_admin, is_root FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if not user:
                print(f"❌ 用户 '{username}' 不存在")
                return False

            print(f"\n用户 '{username}' 当前状态:")
            print(f"  - Admin: {'是' if user.get('is_admin', 0) == 1 else '否'}")
            print(f"  - Root:  {'是' if user.get('is_root', 0) == 1 else '否'}")

            # 更新权限
            updates = []
            params = []

            if make_root:
                updates.append("is_root = 1")
                print(f"\n✓ 设置为 Root 用户")

            elif make_admin:
                updates.append("is_admin = 1")
                print(f"\n✓ 设置为 Admin 用户")

            if updates:
                params.append(username)
                cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE username = %s", params)
                conn.commit()
                print(f"✓ 权限更新成功！")
            else:
                print(f"\n没有需要更新的权限")

        conn.close()
        return True

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("AI Web Dev - 权限诊断工具")
    print("=" * 60)

    # 检查权限
    check_permissions()

    print("\n" + "=" * 60)
    print("操作选项")
    print("=" * 60)
    print("1. 设置用户为 Root")
    print("2. 设置用户为 Admin")
    print("3. 取消用户权限")
    print("4. 仅查看（不修改）")
    print("0. 退出")

    while True:
        choice = input("\n请选择操作 (0-4): ").strip()

        if choice == '0':
            print("退出")
            break
        elif choice == '4':
            check_permissions()
        elif choice in ['1', '2', '3']:
            username = input("请输入用户名: ").strip()
            if not username:
                print("用户名不能为空")
                continue

            if choice == '1':
                fix_user_permission(username, make_root=True)
            elif choice == '2':
                fix_user_permission(username, make_admin=True)
            elif choice == '3':
                # 取消权限
                try:
                    conn = pymysql.connect(
                        host=os.getenv('MYSQL_HOST', 'localhost'),
                        port=int(os.getenv('MYSQL_PORT', 3306)),
                        user=os.getenv('MYSQL_USER', 'root'),
                        password=os.getenv('MYSQL_PASSWORD', ''),
                        database=os.getenv('MYSQL_DATABASE', 'ai_web_dev'),
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor,
                    )
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "UPDATE users SET is_admin = 0, is_root = 0 WHERE username = %s",
                            (username,)
                        )
                        conn.commit()
                        print(f"✓ 已取消 '{username}' 的所有权限")
                    conn.close()
                except Exception as e:
                    print(f"❌ 错误: {e}")

            # 重新检查权限
            check_permissions()
        else:
            print("无效的选择")


if __name__ == '__main__':
    main()
