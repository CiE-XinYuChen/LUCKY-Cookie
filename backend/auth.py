from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import check_password_hash
from .models import db, User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': '登录成功',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not all(key in data for key in ['username', 'password', 'name']):
        return jsonify({'error': '用户名、密码和姓名不能为空'}), 400
    
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 409
    
    if len(password) < 6:
        return jsonify({'error': '密码长度不能少于6位'}), 400
    
    user = User(username=username, name=name)
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': '注册成功'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '注册失败'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    if not data or not all(key in data for key in ['old_password', 'new_password']):
        return jsonify({'error': '旧密码和新密码不能为空'}), 400
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not user.check_password(old_password):
        return jsonify({'error': '旧密码错误'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': '新密码长度不能少于6位'}), 400
    
    user.set_password(new_password)
    
    try:
        db.session.commit()
        return jsonify({'message': '密码修改成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '密码修改失败'}), 500

@auth_bp.route('/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({
        'valid': True,
        'user': user.to_dict()
    }), 200