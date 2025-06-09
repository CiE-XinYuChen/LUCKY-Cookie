import os

class Config:
    SECRET_KEY = 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = 'jwt-secret-key-change-in-production'
    DATABASE_NAME = 'dorm_lottery.db'
    
    # 上传文件配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'csv'}
    
    # JWT 配置
    JWT_ACCESS_TOKEN_EXPIRES = False
    JWT_ALGORITHM = 'HS256'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}