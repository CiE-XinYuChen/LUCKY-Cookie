"""
简单的基于数据库的认证系统
不依赖JWT，避免签名验证问题
"""
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from . import database as db

def init_auth_table():
    """初始化认证token表"""
    try:
        conn = db.get_db()
        with open('database/add_auth_tokens_table.sql', 'r') as f:
            conn.executescript(f.read())
        conn.commit()
    except Exception as e:
        current_app.logger.error(f"初始化auth_tokens表失败: {str(e)}")

def generate_token():
    """生成安全的随机token"""
    return secrets.token_urlsafe(32)

def create_auth_token(user_id, expires_in_hours=24):
    """为用户创建认证token"""
    token = generate_token()
    expires_at = datetime.now() + timedelta(hours=expires_in_hours)
    
    try:
        conn = db.get_db()
        # 先清理该用户的旧token
        conn.execute(
            'UPDATE auth_tokens SET is_active = 0 WHERE user_id = ? AND is_active = 1',
            (user_id,)
        )
        
        # 创建新token
        conn.execute(
            '''INSERT INTO auth_tokens (user_id, token, expires_at) 
               VALUES (?, ?, ?)''',
            (user_id, token, expires_at)
        )
        conn.commit()
        return token
    except Exception as e:
        current_app.logger.error(f"创建token失败: {str(e)}")
        return None

def verify_token(token):
    """验证token并返回用户ID"""
    if not token:
        return None
    
    try:
        conn = db.get_db()
        result = conn.execute(
            '''SELECT user_id FROM auth_tokens 
               WHERE token = ? AND is_active = 1 AND expires_at > ?''',
            (token, datetime.now())
        ).fetchone()
        
        if result:
            return result['user_id']
        return None
    except Exception as e:
        current_app.logger.error(f"验证token失败: {str(e)}")
        return None

def invalidate_token(token):
    """使token失效"""
    try:
        conn = db.get_db()
        conn.execute(
            'UPDATE auth_tokens SET is_active = 0 WHERE token = ?',
            (token,)
        )
        conn.commit()
        return True
    except Exception as e:
        current_app.logger.error(f"注销token失败: {str(e)}")
        return False

def get_current_user():
    """从请求中获取当前用户"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]  # 移除 'Bearer ' 前缀
    user_id = verify_token(token)
    
    if user_id:
        return db.get_user_by_id(user_id)
    return None

def simple_auth_required(f):
    """简单认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': '未登录或登录已过期'}), 401
        
        # 将用户信息添加到请求上下文
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def simple_admin_required(f):
    """简单管理员认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'error': '未登录或登录已过期'}), 401
        
        if not user.get('is_admin'):
            return jsonify({'error': '需要管理员权限'}), 403
        
        # 将用户信息添加到请求上下文
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

# 清理过期token的函数（可以定期调用）
def cleanup_expired_tokens():
    """清理过期的token"""
    try:
        conn = db.get_db()
        conn.execute(
            'DELETE FROM auth_tokens WHERE expires_at < ?',
            (datetime.now(),)
        )
        conn.commit()
        return True
    except Exception as e:
        current_app.logger.error(f"清理过期token失败: {str(e)}")
        return False