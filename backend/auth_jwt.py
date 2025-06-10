from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from . import database as db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 验证JWT token
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            if not current_user_id:
                return jsonify({'error': 'Token无效或已过期'}), 401
            
            # 将字符串ID转换为整数
            try:
                user_id = int(current_user_id)
            except (ValueError, TypeError):
                return jsonify({'error': 'Token格式错误'}), 401
            
            user = db.get_user_by_id(user_id)
            
            if not user:
                return jsonify({'error': '用户不存在'}), 403
                
            if not user['is_admin']:
                return jsonify({'error': '需要管理员权限'}), 403
                
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"权限验证失败: {str(e)}")
            # 区分不同类型的验证失败
            if 'expired' in str(e).lower():
                return jsonify({'error': 'Token已过期，请重新登录'}), 401
            elif 'invalid' in str(e).lower() or 'decode' in str(e).lower():
                return jsonify({'error': 'Token无效，请重新登录'}), 401
            else:
                return jsonify({'error': '权限验证失败'}), 403
    return decorated_function

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
    
    # JWT identity必须是字符串
    access_token = create_access_token(identity=str(user['id']))
    
    return jsonify({
        'message': '登录成功',
        'access_token': access_token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'name': user['name'],
            'is_admin': bool(user['is_admin']),
            'created_at': user['created_at']
        }
    }), 200

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
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    # 将字符串ID转换为整数
    try:
        user_id = int(current_user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Token格式错误'}), 401
    
    user = db.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
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
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    # 将字符串ID转换为整数
    try:
        user_id = int(current_user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Token格式错误'}), 401
    
    user = db.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
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
        
        with db.get_db_connection() as conn:
            c = conn.cursor()
            c.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
        
        return jsonify({'message': '密码修改成功'}), 200
    except Exception as e:
        return jsonify({'error': '密码修改失败'}), 500

@auth_bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    current_user_id = get_jwt_identity()
    # 将字符串ID转换为整数
    try:
        user_id = int(current_user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Token格式错误'}), 401
    
    user = db.get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
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