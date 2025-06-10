#!/usr/bin/env python3
"""
密钥管理命令行工具
"""
import sys
import argparse
from secret_key_manager import key_manager

def show_keys():
    """显示当前密钥"""
    print("当前密钥配置：")
    print(f"SECRET_KEY: {key_manager.get_secret_key()}")
    print(f"JWT_SECRET_KEY: {key_manager.get_jwt_secret_key()}")

def regenerate_keys():
    """重新生成密钥"""
    confirm = input("警告：重新生成密钥会使所有现有token失效！确定要继续吗？(yes/no): ")
    if confirm.lower() == 'yes':
        keys = key_manager.regenerate_keys()
        print("新密钥已生成：")
        print(f"SECRET_KEY: {keys['SECRET_KEY']}")
        print(f"JWT_SECRET_KEY: {keys['JWT_SECRET_KEY']}")
        print("\n请重启应用以使用新密钥。")
    else:
        print("操作已取消。")

def main():
    parser = argparse.ArgumentParser(description='密钥管理工具')
    parser.add_argument('action', choices=['show', 'regenerate'], 
                        help='操作类型：show(显示密钥) 或 regenerate(重新生成)')
    
    args = parser.parse_args()
    
    if args.action == 'show':
        show_keys()
    elif args.action == 'regenerate':
        regenerate_keys()

if __name__ == '__main__':
    main()