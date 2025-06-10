#!/usr/bin/env python3
"""
认证系统切换工具
可以在JWT和简单认证之间切换
"""
import os
import shutil
import sys

def switch_to_simple_auth():
    """切换到简单认证"""
    print("切换到简单认证系统...")
    
    # 备份当前的auth.py
    if os.path.exists('backend/auth.py'):
        shutil.copy('backend/auth.py', 'backend/auth_jwt.py')
        print("已备份原JWT认证到 backend/auth_jwt.py")
    
    # 使用简单认证替换
    if os.path.exists('backend/auth_v2.py'):
        shutil.copy('backend/auth_v2.py', 'backend/auth.py')
        print("已切换到简单认证系统")
        
        # 初始化数据库表
        print("初始化认证表...")
        from backend.app import create_app
        from backend.simple_auth import init_auth_table
        
        app = create_app()
        with app.app_context():
            init_auth_table()
            print("认证表初始化完成")
    else:
        print("错误：找不到 backend/auth_v2.py")
        return False
    
    return True

def switch_to_jwt_auth():
    """切换回JWT认证"""
    print("切换回JWT认证系统...")
    
    if os.path.exists('backend/auth_jwt.py'):
        shutil.copy('backend/auth_jwt.py', 'backend/auth.py')
        print("已切换回JWT认证系统")
    else:
        print("错误：找不到JWT认证备份文件")
        return False
    
    return True

def main():
    if len(sys.argv) < 2:
        print("使用方法：")
        print("  python switch_auth.py simple  - 切换到简单认证")
        print("  python switch_auth.py jwt     - 切换回JWT认证")
        return
    
    auth_type = sys.argv[1].lower()
    
    if auth_type == 'simple':
        if switch_to_simple_auth():
            print("\n✅ 成功切换到简单认证系统")
            print("请重启应用以使更改生效")
    elif auth_type == 'jwt':
        if switch_to_jwt_auth():
            print("\n✅ 成功切换回JWT认证系统")
            print("请重启应用以使更改生效")
    else:
        print(f"未知的认证类型：{auth_type}")

if __name__ == '__main__':
    main()