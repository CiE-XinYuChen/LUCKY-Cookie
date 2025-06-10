"""
认证模块 V2 - 使用简单的基于数据库的token认证
"""
from flask import Blueprint, request, jsonify, current_app
from . import database as db
from .simple_auth import (
    init_auth_table, create_auth_token, verify_token, 
    invalidate_token, simple_auth_required, simple_admin_required,
    get_current_user
)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# 导出装饰器供其他模块使用
admin_required = simple_admin_required
jwt_required = simple_auth_required  # 保持接口兼容

# 模拟JWT的get_jwt_identity函数
def get_jwt_identity():
    """获取当前用户ID（保持接口兼容）"""
    user = get_current_user()
    if user:
        return str(user['id'])  # 返回字符串格式的ID
    return None

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    user = db.get_user_by_username(username)
    
    if not user or not db.check_password(user, password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # 创建认证token
    token = create_auth_token(user['id'])
    if not token:
        return jsonify({'error': '登录失败，请稍后重试'}), 500
    
    return jsonify({
        'message': '登录成功',
        'access_token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'name': user['name'],
            'is_admin': bool(user['is_admin']),
            'created_at': user['created_at']
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@simple_auth_required
def logout():
    """注销登录"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        invalidate_token(token)
    
    return jsonify({'message': '已退出登录'}), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not all(key in data for key in ['username', 'password', 'name']):
        return jsonify({'error': '用户名、密码和姓名不能为空'}), 400
    
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    
    if db.get_user_by_username(username):
        return jsonify({'error': '用户名已存在'}), 409
    
    if len(password) < 6:
        return jsonify({'error': '密码长度不能少于6位'}), 400
    
    try:
        user_id = db.create_user(username, password, name)
        return jsonify({'message': '注册成功'}), 201
    except Exception as e:
        return jsonify({'error': '注册失败'}), 500

@auth_bp.route('/profile', methods=['GET'])
@simple_auth_required
def get_profile():
    user = request.current_user
    
    return jsonify({
        'user': {
            'id': user['id'],
            'username': user['username'],
            'name': user['name'],
            'is_admin': bool(user['is_admin']),
            'created_at': user['created_at']
        }
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
@simple_auth_required
def change_password():
    user = request.current_user
    data = request.get_json()
    
    if not data or not all(key in data for key in ['old_password', 'new_password']):
        return jsonify({'error': '旧密码和新密码不能为空'}), 400
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not db.check_password(user, old_password):
        return jsonify({'error': '旧密码错误'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': '新密码长度不能少于6位'}), 400
    
    try:
        import bcrypt
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = db.get_db()
        conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user['id']))
        conn.commit()
        
        return jsonify({'message': '密码修改成功'}), 200
    except Exception as e:
        return jsonify({'error': '密码修改失败'}), 500

@auth_bp.route('/verify-token', methods=['GET'])
@simple_auth_required
def verify_token_endpoint():
    user = request.current_user
    
    return jsonify({
        'valid': True,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'name': user['name'],
            'is_admin': bool(user['is_admin']),
            'created_at': user['created_at']
        }
    }), 200