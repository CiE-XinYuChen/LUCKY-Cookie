#!/usr/bin/env python3
import os
from backend.app import create_app

app = create_app()

if __name__ == '__main__':
    # 确保数据库表存在
    with app.app_context():
        from backend.models import db
        db.create_all()
        print("数据库表创建完成")
    
    # 启动应用
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    print(f"启动服务器: http://{host}:{port}")
    print("默认管理员账户: admin / admin123")
    
    app.run(host=host, port=port, debug=debug)