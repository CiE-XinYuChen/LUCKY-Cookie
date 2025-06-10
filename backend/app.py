import os
from flask import Flask, render_template, send_from_directory, request, jsonify
# from flask_jwt_extended import JWTManager  # 不再使用JWT
from flask_cors import CORS
from config import config
from . import database as db
from .auth import auth_bp
from .admin import admin_bp
from .lottery import lottery_bp
from .room_selection import room_selection_bp

def create_app(config_name=None):
    app = Flask(__name__, 
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    app.config.from_object(config[config_name])
    
    # Initialize database
    with app.app_context():
        db.init_db()
    
    # jwt = JWTManager(app)  # 不再使用JWT
    
    # 动态CORS配置，支持生产环境
    cors_origins = app.config.get('CORS_ORIGINS', ['http://localhost:32228', 'http://127.0.0.1:32228'])
    CORS(app, origins=cors_origins, supports_credentials=True)
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(lottery_bp)
    app.register_blueprint(room_selection_bp)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/login')
    def login_page():
        return render_template('login.html')
    
    @app.route('/admin')
    def admin_page():
        return render_template('admin.html')
    
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html')
    
    @app.route('/room-selection')
    def room_selection_page():
        return render_template('room_selection.html')
    
    @app.errorhandler(404)
    def not_found(error):
        # 对API请求返回JSON
        if request.path.startswith('/api/'):
            return jsonify({'error': '请求的资源不存在'}), 404
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        # 对API请求返回JSON
        if request.path.startswith('/api/'):
            app.logger.error(f"内部服务器错误: {str(error)}")
            return jsonify({'error': '服务器内部错误'}), 500
        return render_template('500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        # 记录错误
        app.logger.error(f"未处理的异常: {str(error)}", exc_info=True)
        
        # 对API请求返回JSON
        if request.path.startswith('/api/'):
            return jsonify({'error': '服务器错误，请稍后重试'}), 500
        
        # 其他请求返回500页面
        return render_template('500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=32228)