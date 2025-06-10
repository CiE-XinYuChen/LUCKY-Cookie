import os
from secret_key_manager import key_manager

class Config:
    # 优先使用环境变量，否则使用持久化的密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or key_manager.get_secret_key()
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or key_manager.get_jwt_secret_key()
    DATABASE_NAME = 'dorm_lottery.db'
    
    # 上传文件配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'csv'}
    
    # JWT 配置
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 60 * 60  # 24小时，以秒为单位
    JWT_ALGORITHM = 'HS256'
    
    # CORS 配置
    CORS_ORIGINS = ['*']  # 生产环境建议限制具体域名

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # 生产环境也使用相同的密钥管理逻辑
    # 优先环境变量，其次持久化密钥
    # 生产环境CORS配置 - 可以设置具体域名
    CORS_ORIGINS = [
        'https://ybu.room.shaynechen.tech',
        'http://ybu.room.shaynechen.tech',
        'https://localhost:32228',
        'http://localhost:32228'
    ]

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}