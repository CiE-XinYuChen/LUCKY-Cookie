import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
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
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key-must-be-changed'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'production-jwt-secret-key-must-be-changed'
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