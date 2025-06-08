import os
from flask import Flask, render_template, send_from_directory
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config
from .models import db
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
    
    db.init_app(app)
    
    jwt = JWTManager(app)
    
    CORS(app, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])
    
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
    
    @app.route('/lottery')
    def lottery_page():
        return render_template('lottery.html')
    
    @app.route('/room-selection')
    def room_selection_page():
        return render_template('room_selection.html')
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)