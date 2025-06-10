#!/usr/bin/env python3
import os
from backend.app import create_app
from backend import database as db

def load_env_file():
    """加载环境变量文件"""
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"加载环境配置文件: {env_file}")
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ.setdefault(key, value)

# 加载环境变量
load_env_file()

# 创建应用
flask_env = os.environ.get('FLASK_ENV', 'production')
app = create_app(flask_env)

if __name__ == '__main__':
    # 确保数据库存在并初始化
    with app.app_context():
        db.init_db()
        print("数据库初始化完成")
    
    # 启动应用
    port = int(os.environ.get('PORT', 32228))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = flask_env == 'development'
    
    print(f"应用启动配置:")
    print(f"- 环境: {flask_env}")
    print(f"- 地址: http://{host}:{port}")
    print(f"- 调试模式: {debug}")
    print("默认管理员账户: admin / admin123")
    
    app.run(host=host, port=port, debug=debug)