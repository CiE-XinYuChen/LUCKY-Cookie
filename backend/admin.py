import pandas as pd
import io
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from .auth import admin_required
from datetime import datetime
import bcrypt
import random
from . import database as db

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Helper functions to convert database rows to dictionaries
def user_to_dict(user):
    return {
        'id': user['id'],
        'username': user['username'],
        'name': user['name'],
        'is_admin': bool(user['is_admin']),
        'created_at': user['created_at']
    }

def building_to_dict(building):
    return {
        'id': building['id'],
        'name': building['name'],
        'description': building['description'],
        'created_at': building['created_at']
    }

def room_to_dict(room):
    return {
        'id': room['id'],
        'building_id': room['building_id'],
        'building_name': room['building_name'] if 'building_name' in room.keys() else None,
        'room_number': room['room_number'],
        'room_type': room['room_type'],
        'max_capacity': room['max_capacity'],
        'current_occupancy': room['current_occupancy'],
        'is_available': bool(room['is_available']),
        'available_beds': room['available_beds'] if 'available_beds' in room.keys() else 0
    }

def allocation_to_dict(allocation):
    return {
        'id': allocation['id'],
        'user_id': allocation['user_id'],
        'user_name': allocation['user_name'] if 'user_name' in allocation.keys() else None,
        'user_username': allocation['user_username'] if 'user_username' in allocation.keys() else None,
        'room_number': allocation['room_number'] if 'room_number' in allocation.keys() else None,
        'building_name': allocation['building_name'] if 'building_name' in allocation.keys() else None,
        'bed_number': allocation['bed_number'] if 'bed_number' in allocation.keys() else None,
        'selected_at': allocation['selected_at'],
        'is_confirmed': bool(allocation['is_confirmed'])
    }

def room_type_allocation_to_dict(rta):
    return {
        'id': rta['id'],
        'user_id': rta['user_id'],
        'user_name': rta['user_name'] if 'user_name' in rta.keys() else None,
        'user_username': rta['username'] if 'username' in rta.keys() else None,
        'room_type': rta['room_type'],
        'allocated_by': rta['allocated_by'],
        'allocator_name': rta['allocator_name'] if 'allocator_name' in rta.keys() else None,
        'allocated_at': rta['allocated_at'],
        'notes': rta['notes']
    }

def lottery_result_to_dict(result):
    return {
        'id': result['id'],
        'user_id': result['user_id'],
        'user_name': result['user_name'] if 'user_name' in result.keys() else None,
        'lottery_id': result['lottery_id'],
        'lottery_number': result['lottery_number'],
        'group_number': result['group_number'],
        'created_at': result['created_at']
    }

def lottery_setting_to_dict(lottery):
    return {
        'id': lottery['id'],
        'lottery_name': lottery['lottery_name'],
        'lottery_time': lottery['lottery_time'],
        'is_published': bool(lottery['is_published']),
        'room_type': lottery['room_type'],
        'created_at': lottery['created_at']
    }

def history_to_dict(history):
    return {
        'id': history['id'],
        'user_name': history['user_name'] if 'user_name' in history.keys() else None,
        'room_info': history['room_info'] if 'room_info' in history.keys() else None,
        'bed_number': history['bed_number'] if 'bed_number' in history.keys() else None,
        'action': history['action'],
        'operator_name': history['operator_name'] if 'operator_name' in history.keys() else None,
        'operated_at': history['operated_at'],
        'notes': history['notes']
    }

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    conn = db.get_db()
    c = conn.cursor()
    
    # Get total count with search
    if search:
        c.execute('''
            SELECT COUNT(*) as total FROM users 
            WHERE username LIKE ? OR name LIKE ?
        ''', (f'%{search}%', f'%{search}%'))
    else:
        c.execute('SELECT COUNT(*) as total FROM users')
    
    total = c.fetchone()['total']
    pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    
    # Get users with pagination
    if search:
        c.execute('''
            SELECT * FROM users 
            WHERE username LIKE ? OR name LIKE ?
            ORDER BY id DESC LIMIT ? OFFSET ?
        ''', (f'%{search}%', f'%{search}%', per_page, offset))
    else:
        c.execute('SELECT * FROM users ORDER BY id DESC LIMIT ? OFFSET ?', (per_page, offset))
    
    users = c.fetchall()
    conn.close()
    
    return jsonify({
        'users': [user_to_dict(user) for user in users],
        'total': total,
        'pages': pages,
        'current_page': page
    }), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if user['is_admin']:
        return jsonify({'error': '不能删除管理员账户'}), 400
    
    try:
        with db.get_db_connection() as conn:
            c = conn.cursor()
            c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        return jsonify({'message': '用户删除成功'}), 200
    except Exception as e:
        return jsonify({'error': '删除失败'}), 500

@admin_bp.route('/users/<int:user_id>/password', methods=['PUT'])
@admin_required
def reset_user_password(user_id):
    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    if not data or not data.get('new_password'):
        return jsonify({'error': '新密码不能为空'}), 400
    
    new_password = data.get('new_password')
    if len(new_password) < 6:
        return jsonify({'error': '密码长度不能少于6位'}), 400
    
    try:
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with db.get_db_connection() as conn:
            c = conn.cursor()
            c.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
        return jsonify({'message': '密码重置成功'}), 200
    except Exception as e:
        return jsonify({'error': '密码重置失败'}), 500

@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    required_fields = ['username', 'password', 'name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': '用户名、密码和姓名不能为空'}), 400
    
    username = data.get('username').strip()
    password = data.get('password').strip()
    name = data.get('name').strip()
    
    if not username or not password or not name:
        return jsonify({'error': '用户名、密码和姓名不能为空'}), 400
    
    if len(password) < 6:
        return jsonify({'error': '密码长度不能少于6位'}), 400
    
    if db.get_user_by_username(username):
        return jsonify({'error': '用户名已存在'}), 409
    
    try:
        user_id = db.create_user(username, password, name)
        return jsonify({'message': '用户创建成功', 'user_id': user_id}), 201
    except Exception as e:
        return jsonify({'error': '用户创建失败'}), 500

@admin_bp.route('/users/import', methods=['POST'])
@admin_required
def import_users():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件被上传'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': '只支持CSV文件'}), 400
    
    try:
        df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
        
        required_columns = ['username', 'name', 'password']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'CSV文件必须包含username、name和password列'}), 400
        
        success_count = 0
        error_count = 0
        errors = []
        
        with db.get_db_connection() as conn:
            c = conn.cursor()
            
            for index, row in df.iterrows():
                try:
                    username = str(row['username']).strip()
                    name = str(row['name']).strip()
                    password = str(row['password']).strip()
                    
                    # Check if user exists
                    c.execute('SELECT id FROM users WHERE username = ?', (username,))
                    if c.fetchone():
                        error_count += 1
                        errors.append(f"第{index+2}行: 用户名 {username} 已存在")
                        continue
                    
                    # Create user
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    c.execute(
                        'INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)',
                        (username, password_hash, name)
                    )
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"第{index+2}行: {str(e)}")
        
        return jsonify({
            'message': f'导入完成：成功 {success_count} 个，失败 {error_count} 个',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]  # 只返回前10个错误
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'文件处理失败: {str(e)}'}), 500

@admin_bp.route('/lottery/settings', methods=['GET'])
@admin_required
def get_lottery_settings():
    lottery = db.get_active_lottery()
    
    if lottery:
        return jsonify({
            'lottery': lottery_setting_to_dict(lottery)
        }), 200
    
    return jsonify({'lottery': None}), 200

@admin_bp.route('/lottery/settings', methods=['POST'])
@admin_required
def create_lottery_setting():
    data = request.get_json()
    
    if not data or not all(key in data for key in ['lottery_name', 'lottery_time', 'room_type']):
        return jsonify({'error': '抽签名称、抽签时间和房间类型不能为空'}), 400
    
    try:
        lottery_id = db.create_lottery(
            data['lottery_name'],
            data['lottery_time'],
            data['room_type']
        )
        return jsonify({'message': '抽签设置创建成功', 'lottery_id': lottery_id}), 201
    except Exception as e:
        return jsonify({'error': '创建失败'}), 500

@admin_bp.route('/lottery/results', methods=['GET'])
@admin_required
def get_lottery_results():
    lottery = db.get_active_lottery()
    if not lottery:
        return jsonify({'error': '没有活动的抽签'}), 404
    
    results = db.get_lottery_results(lottery['id'])
    
    return jsonify({
        'results': [lottery_result_to_dict(r) for r in results],
        'lottery': lottery_setting_to_dict(lottery)
    }), 200

@admin_bp.route('/lottery/generate', methods=['POST'])
@admin_required
def generate_lottery_results():
    lottery = db.get_active_lottery()
    if not lottery:
        return jsonify({'error': '没有活动的抽签'}), 404
    
    if lottery['is_published']:
        return jsonify({'error': '抽签结果已发布，不能重新生成'}), 400
    
    try:
        # Get all non-admin users
        conn = db.get_db()
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE is_admin = 0')
        users = c.fetchall()
        conn.close()
        
        # Shuffle users
        user_ids = [u['id'] for u in users]
        random.shuffle(user_ids)
        
        # Save results
        with db.get_db_connection() as conn:
            c = conn.cursor()
            # Clear existing results
            c.execute('DELETE FROM lottery_results WHERE lottery_id = ?', (lottery['id'],))
            
            # Insert new results
            for i, user_id in enumerate(user_ids):
                group_number = (i // 4) + 1 if lottery['room_type'] == '4' else (i // 8) + 1
                db.save_lottery_result(user_id, lottery['id'], i + 1, group_number)
        
        return jsonify({'message': '抽签结果生成成功', 'total': len(users)}), 200
        
    except Exception as e:
        return jsonify({'error': f'生成失败: {str(e)}'}), 500

@admin_bp.route('/lottery/publish', methods=['POST'])
@admin_required
def publish_lottery_results():
    lottery = db.get_active_lottery()
    if not lottery:
        return jsonify({'error': '没有活动的抽签'}), 404
    
    try:
        db.publish_lottery(lottery['id'])
        return jsonify({'message': '抽签结果已发布'}), 200
    except Exception as e:
        return jsonify({'error': '发布失败'}), 500

@admin_bp.route('/buildings', methods=['GET'])
@admin_required
def get_buildings():
    buildings = db.get_all_buildings()
    return jsonify({
        'buildings': [building_to_dict(b) for b in buildings]
    }), 200

@admin_bp.route('/buildings', methods=['POST'])
@admin_required
def create_building():
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': '楼栋名称不能为空'}), 400
    
    try:
        building_id = db.create_building(data['name'], data.get('description'))
        return jsonify({'message': '楼栋创建成功', 'building_id': building_id}), 201
    except Exception as e:
        return jsonify({'error': '创建失败'}), 500

@admin_bp.route('/buildings/<int:building_id>/rooms', methods=['GET'])
@admin_required
def get_building_rooms(building_id):
    rooms = db.get_rooms_by_building(building_id)
    return jsonify({
        'rooms': [room_to_dict(r) for r in rooms]
    }), 200

@admin_bp.route('/rooms', methods=['GET'])
@admin_required
def get_rooms():
    building_id = request.args.get('building_id', type=int)
    room_type = request.args.get('room_type')
    
    conn = db.get_db()
    c = conn.cursor()
    
    query = '''
        SELECT r.*, b.name as building_name,
               (SELECT COUNT(*) FROM beds WHERE room_id = r.id AND is_occupied = 0) as available_beds
        FROM rooms r
        JOIN buildings b ON r.building_id = b.id
        WHERE 1=1
    '''
    
    params = []
    if building_id:
        query += ' AND r.building_id = ?'
        params.append(building_id)
    if room_type:
        query += ' AND r.room_type = ?'
        params.append(room_type)
    
    query += ' ORDER BY b.name, r.room_number'
    
    if params:
        c.execute(query, params)
    else:
        c.execute(query)
    
    rooms = c.fetchall()
    conn.close()
    
    return jsonify({
        'rooms': [room_to_dict(r) for r in rooms]
    }), 200

@admin_bp.route('/rooms', methods=['POST'])
@admin_required
def create_room():
    data = request.get_json()
    
    required_fields = ['building_id', 'room_number', 'room_type', 'max_capacity']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': '楼栋、房间号、房间类型和最大容量不能为空'}), 400
    
    try:
        room_id = db.create_room(
            data['building_id'],
            data['room_number'],
            data['room_type'],
            data['max_capacity']
        )
        return jsonify({'message': '房间创建成功', 'room_id': room_id}), 201
    except Exception as e:
        if 'UNIQUE constraint failed' in str(e):
            return jsonify({'error': '该楼栋已存在相同房间号'}), 409
        return jsonify({'error': '创建失败'}), 500

@admin_bp.route('/rooms/import', methods=['POST'])
@admin_required
def import_rooms():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件被上传'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': '只支持CSV文件'}), 400
    
    try:
        df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
        
        required_columns = ['building_name', 'room_number', 'room_type', 'max_capacity']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'CSV文件必须包含building_name、room_number、room_type和max_capacity列'}), 400
        
        success_count = 0
        error_count = 0
        errors = []
        
        with db.get_db_connection() as conn:
            c = conn.cursor()
            
            for index, row in df.iterrows():
                try:
                    building_name = str(row['building_name']).strip()
                    room_number = str(row['room_number']).strip()
                    room_type = str(row['room_type']).strip()
                    max_capacity = int(row['max_capacity'])
                    
                    # Get building by name
                    c.execute('SELECT id FROM buildings WHERE name = ?', (building_name,))
                    building = c.fetchone()
                    if not building:
                        error_count += 1
                        errors.append(f"第{index+2}行: 楼栋 {building_name} 不存在")
                        continue
                    
                    # Check if room already exists
                    c.execute('SELECT id FROM rooms WHERE building_id = ? AND room_number = ?', 
                             (building['id'], room_number))
                    if c.fetchone():
                        error_count += 1
                        errors.append(f"第{index+2}行: 房间 {building_name}-{room_number} 已存在")
                        continue
                    
                    # Create room
                    db.create_room(building['id'], room_number, room_type, max_capacity)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"第{index+2}行: {str(e)}")
        
        return jsonify({
            'message': f'导入完成：成功 {success_count} 个，失败 {error_count} 个',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'文件处理失败: {str(e)}'}), 500

@admin_bp.route('/rooms/<int:room_id>', methods=['GET'])
@admin_required
def get_room_detail(room_id):
    room = db.get_room_with_beds(room_id)
    if not room:
        return jsonify({'error': '房间不存在'}), 404
    
    return jsonify({'room': room}), 200

@admin_bp.route('/rooms/<int:room_id>', methods=['PUT'])
@admin_required
def update_room(room_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    try:
        with db.get_db_connection() as conn:
            c = conn.cursor()
            
            # Check if room exists
            c.execute('SELECT * FROM rooms WHERE id = ?', (room_id,))
            room = c.fetchone()
            if not room:
                return jsonify({'error': '房间不存在'}), 404
            
            # Update room fields
            update_fields = []
            update_params = []
            
            if 'room_number' in data:
                update_fields.append('room_number = ?')
                update_params.append(data['room_number'])
            
            if 'room_type' in data:
                update_fields.append('room_type = ?')
                update_params.append(data['room_type'])
            
            if 'max_capacity' in data:
                new_capacity = int(data['max_capacity'])
                old_capacity = room['max_capacity']
                
                update_fields.append('max_capacity = ?')
                update_params.append(new_capacity)
                
                # Update beds if capacity changed
                if new_capacity != old_capacity:
                    if new_capacity > old_capacity:
                        # Add new beds
                        for i in range(old_capacity + 1, new_capacity + 1):
                            c.execute(
                                'INSERT INTO beds (room_id, bed_number) VALUES (?, ?)',
                                (room_id, str(i))
                            )
                    elif new_capacity < old_capacity:
                        # Remove excess beds (only if not occupied)
                        c.execute(
                            'SELECT COUNT(*) as occupied FROM beds WHERE room_id = ? AND bed_number > ? AND is_occupied = 1',
                            (room_id, str(new_capacity))
                        )
                        occupied_count = c.fetchone()['occupied']
                        if occupied_count > 0:
                            return jsonify({'error': f'无法减少容量，有 {occupied_count} 个床位已被占用'}), 400
                        
                        # Delete excess beds
                        c.execute(
                            'DELETE FROM beds WHERE room_id = ? AND bed_number > ?',
                            (room_id, str(new_capacity))
                        )
            
            if 'is_available' in data:
                update_fields.append('is_available = ?')
                update_params.append(1 if data['is_available'] else 0)
            
            if update_fields:
                update_params.append(room_id)
                c.execute(f'UPDATE rooms SET {", ".join(update_fields)} WHERE id = ?', update_params)
        
        return jsonify({'message': '房间更新成功'}), 200
    except Exception as e:
        return jsonify({'error': f'更新失败: {str(e)}'}), 500

@admin_bp.route('/rooms/<int:room_id>', methods=['DELETE'])
@admin_required
def delete_room(room_id):
    try:
        with db.get_db_connection() as conn:
            c = conn.cursor()
            
            # Check if room exists
            c.execute('SELECT * FROM rooms WHERE id = ?', (room_id,))
            room = c.fetchone()
            if not room:
                return jsonify({'error': '房间不存在'}), 404
            
            # Check if any beds are occupied
            c.execute('SELECT COUNT(*) as occupied FROM beds WHERE room_id = ? AND is_occupied = 1', (room_id,))
            occupied_count = c.fetchone()['occupied']
            if occupied_count > 0:
                return jsonify({'error': f'无法删除房间，有 {occupied_count} 个床位已被学生选择'}), 400
            
            # Check if there are any room selections for this room
            c.execute('SELECT COUNT(*) as selections FROM room_selections WHERE room_id = ?', (room_id,))
            selection_count = c.fetchone()['selections']
            if selection_count > 0:
                return jsonify({'error': '无法删除房间，存在相关的房间选择记录'}), 400
            
            # Delete beds first (foreign key constraint)
            c.execute('DELETE FROM beds WHERE room_id = ?', (room_id,))
            
            # Delete room
            c.execute('DELETE FROM rooms WHERE id = ?', (room_id,))
        
        return jsonify({'message': '房间删除成功'}), 200
    except Exception as e:
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

@admin_bp.route('/allocations', methods=['GET'])
@admin_required
def get_allocations():
    conn = db.get_db()
    c = conn.cursor()
    
    c.execute('''
        SELECT rs.*, u.name as user_name, u.username as user_username,
               r.room_number, b.name as building_name, bd.bed_number
        FROM room_selections rs
        JOIN users u ON rs.user_id = u.id
        JOIN rooms r ON rs.room_id = r.id
        JOIN buildings b ON r.building_id = b.id
        JOIN beds bd ON rs.bed_id = bd.id
        ORDER BY rs.selected_at DESC
    ''')
    
    allocations = c.fetchall()
    conn.close()
    
    return jsonify({
        'allocations': [allocation_to_dict(a) for a in allocations]
    }), 200

@admin_bp.route('/allocations/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_allocation(user_id):
    current_user_id = get_jwt_identity()
    
    try:
        selection = db.get_user_room_selection(user_id)
        if not selection:
            return jsonify({'error': '用户没有分配记录'}), 404
        
        # Save to history
        with db.get_db_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO allocation_history (user_id, room_id, bed_id, action, operated_by, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, selection['room_id'], selection['bed_id'], '取消分配', current_user_id, '管理员取消分配'))
        
        # Cancel selection
        db.cancel_room_selection(user_id)
        
        return jsonify({'message': '分配已取消'}), 200
    except Exception as e:
        return jsonify({'error': '取消失败'}), 500

@admin_bp.route('/room-type-allocations', methods=['GET'])
@admin_required
def get_room_type_allocations():
    allocations = db.get_room_type_allocations()
    return jsonify({
        'allocations': [room_type_allocation_to_dict(a) for a in allocations]
    }), 200

@admin_bp.route('/room-type-allocations', methods=['POST'])
@admin_required
def create_room_type_allocation():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    required_fields = ['user_id', 'room_type']
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': '用户ID和房间类型不能为空'}), 400
    
    if data['room_type'] not in ['4', '8']:
        return jsonify({'error': '房间类型必须是4或8'}), 400
    
    try:
        db.allocate_room_type(
            data['user_id'],
            data['room_type'],
            current_user_id,
            data.get('notes')
        )
        return jsonify({'message': '房间类型分配成功'}), 201
    except Exception as e:
        return jsonify({'error': '分配失败'}), 500

@admin_bp.route('/room-type-allocations/import', methods=['POST'])
@admin_required
def import_room_type_allocations():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件被上传'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': '只支持CSV文件'}), 400
    
    current_user_id = get_jwt_identity()
    
    try:
        df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
        
        required_columns = ['username', 'room_type']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'CSV文件必须包含username和room_type列'}), 400
        
        success_count = 0
        error_count = 0
        errors = []
        
        with db.get_db_connection() as conn:
            c = conn.cursor()
            
            for index, row in df.iterrows():
                try:
                    username = str(row['username']).strip()
                    room_type = str(row['room_type']).strip()
                    
                    if room_type not in ['4', '8']:
                        error_count += 1
                        errors.append(f"第{index+2}行: 房间类型必须是4或8")
                        continue
                    
                    # Get user by username
                    c.execute('SELECT id FROM users WHERE username = ?', (username,))
                    user = c.fetchone()
                    if not user:
                        error_count += 1
                        errors.append(f"第{index+2}行: 用户名 {username} 不存在")
                        continue
                    
                    # Allocate room type
                    notes = row['notes'] if 'notes' in df.columns and pd.notna(row['notes']) else None
                    db.allocate_room_type(user['id'], room_type, current_user_id, notes)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"第{index+2}行: {str(e)}")
        
        return jsonify({
            'message': f'导入完成：成功 {success_count} 个，失败 {error_count} 个',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:10]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'文件处理失败: {str(e)}'}), 500

@admin_bp.route('/statistics', methods=['GET'])
@admin_required
def get_statistics():
    stats = db.get_room_statistics()
    
    conn = db.get_db()
    c = conn.cursor()
    
    # Total users
    c.execute('SELECT COUNT(*) as total FROM users WHERE is_admin = 0')
    stats['total_users'] = c.fetchone()['total']
    
    # Total buildings and rooms
    c.execute('SELECT COUNT(*) as total FROM buildings')
    stats['total_buildings'] = c.fetchone()['total']
    
    c.execute('SELECT COUNT(*) as total FROM rooms')
    stats['total_rooms'] = c.fetchone()['total']
    
    conn.close()
    
    return jsonify({'statistics': stats}), 200

@admin_bp.route('/lottery/quick-draw', methods=['POST'])
@admin_required
def quick_lottery_draw():
    data = request.get_json()
    
    if not data or not all(key in data for key in ['lottery_name', 'room_type']):
        return jsonify({'error': '抽签名称和房间类型不能为空'}), 400
    
    # 获取四人寝和六人寝数量（如果提供）
    room_4_count = data.get('room_4_count', 0)
    room_6_count = data.get('room_6_count', 0)
    
    # 如果没有提供具体数量，使用传统的单一房间类型模式
    if room_4_count == 0 and room_6_count == 0:
        if data['room_type'] not in ['4', '8']:
            return jsonify({'error': '房间类型只能是4或8'}), 400
        
        # 传统模式：所有用户分配到同一类型房间
        if data['room_type'] == '4':
            room_4_count = 999999  # 使用一个很大的数字表示不限制
        else:
            room_6_count = 999999
    
    try:
        from datetime import datetime
        
        # 创建抽签设置
        lottery_id = db.create_lottery(
            data['lottery_name'],
            datetime.now().isoformat(),
            data.get('room_type', 'mixed')  # 混合类型
        )
        
        # 获取所有非管理员用户
        conn = db.get_db()
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE is_admin = 0')
        users = c.fetchall()
        conn.close()
        
        if not users:
            return jsonify({'error': '没有可参与抽签的用户'}), 400
        
        # 打乱用户顺序
        import random
        user_ids = [user['id'] for user in users]
        random.shuffle(user_ids)
        
        # 计算分配
        total_4_beds = room_4_count * 4 if room_4_count != 999999 else len(user_ids)
        total_6_beds = room_6_count * 6 if room_6_count != 999999 else len(user_ids)
        
        with db.get_db_connection() as conn:
            c = conn.cursor()
            
            allocated_users = 0
            group_4_count = 0
            group_6_count = 0
            
            # 先分配四人寝
            if room_4_count > 0:
                needed_4_groups = min(room_4_count, (len(user_ids) + 3) // 4) if room_4_count != 999999 else (len(user_ids) + 3) // 4
                for group in range(needed_4_groups):
                    start_idx = allocated_users
                    end_idx = min(allocated_users + 4, len(user_ids))
                    if start_idx >= len(user_ids):
                        break
                    
                    group_4_count += 1
                    
                    for i in range(start_idx, end_idx):
                        c.execute(
                            'INSERT INTO lottery_results (user_id, lottery_id, lottery_number, group_number, room_type) VALUES (?, ?, ?, ?, ?)',
                            (user_ids[i], lottery_id, i + 1, f'4-{group_4_count}', '4')
                        )
                    
                    allocated_users = end_idx
            
            # 再分配六人寝（如果还有用户）
            if room_6_count > 0 and allocated_users < len(user_ids):
                needed_6_groups = min(room_6_count, (len(user_ids) - allocated_users + 5) // 6) if room_6_count != 999999 else (len(user_ids) - allocated_users + 5) // 6
                for group in range(needed_6_groups):
                    start_idx = allocated_users
                    end_idx = min(allocated_users + 6, len(user_ids))
                    if start_idx >= len(user_ids):
                        break
                    
                    group_6_count += 1
                    
                    for i in range(start_idx, end_idx):
                        c.execute(
                            'INSERT INTO lottery_results (user_id, lottery_id, lottery_number, group_number, room_type) VALUES (?, ?, ?, ?, ?)',
                            (user_ids[i], lottery_id, i + 1, f'6-{group_6_count}', '6')
                        )
                    
                    allocated_users = end_idx
        
        return jsonify({
            'message': '抽签生成成功',
            'lottery_id': lottery_id,
            'total_participants': len(user_ids),
            'allocated_participants': allocated_users,
            'room_4_groups': group_4_count,
            'room_6_groups': group_6_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'抽签失败: {str(e)}'}), 500

@admin_bp.route('/lottery/<int:lottery_id>/publish', methods=['POST'])
@admin_required
def publish_lottery_results(lottery_id):
    try:
        db.publish_lottery(lottery_id)
        return jsonify({'message': '抽签结果已发布'}), 200
    except Exception as e:
        return jsonify({'error': f'发布失败: {str(e)}'}), 500

@admin_bp.route('/lottery/<int:lottery_id>', methods=['DELETE'])
@admin_required
def delete_lottery_results(lottery_id):
    try:
        with db.get_db_connection() as conn:
            c = conn.cursor()
            # 删除抽签结果
            c.execute('DELETE FROM lottery_results WHERE lottery_id = ?', (lottery_id,))
            # 删除抽签设置
            c.execute('DELETE FROM lottery_settings WHERE id = ?', (lottery_id,))
        
        return jsonify({'message': '抽签结果已删除'}), 200
    except Exception as e:
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

@admin_bp.route('/lottery/results', methods=['GET'])
@admin_required
def get_all_lottery_results():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    lottery_id = request.args.get('lottery_id', type=int)
    
    conn = db.get_db()
    c = conn.cursor()
    
    base_query = '''
        SELECT lr.*, u.name as user_name, u.username,
               ls.lottery_name, ls.is_published
        FROM lottery_results lr
        JOIN users u ON lr.user_id = u.id
        JOIN lottery_settings ls ON lr.lottery_id = ls.id
    '''
    
    if lottery_id:
        base_query += ' WHERE lr.lottery_id = ?'
        params = (lottery_id,)
    else:
        params = ()
    
    base_query += ' ORDER BY lr.lottery_number'
    
    # 分页
    offset = (page - 1) * per_page
    if params:
        c.execute(base_query + ' LIMIT ? OFFSET ?', params + (per_page, offset))
    else:
        c.execute(base_query + ' LIMIT ? OFFSET ?', (per_page, offset))
    
    results = c.fetchall()
    
    # 获取总数
    count_query = '''
        SELECT COUNT(*) as total
        FROM lottery_results lr
        JOIN lottery_settings ls ON lr.lottery_id = ls.id
    '''
    if lottery_id:
        count_query += ' WHERE lr.lottery_id = ?'
        c.execute(count_query, (lottery_id,))
    else:
        c.execute(count_query)
    
    total = c.fetchone()['total']
    conn.close()
    
    pages = (total + per_page - 1) // per_page
    
    return jsonify({
        'results': [lottery_result_to_dict(r) for r in results],
        'total': total,
        'pages': pages,
        'current_page': page
    }), 200

@admin_bp.route('/allocation-history', methods=['GET'])
@admin_required
def get_allocation_history():
    conn = db.get_db()
    c = conn.cursor()
    
    c.execute('''
        SELECT ah.*, u.name as user_name, op.name as operator_name,
               b.name as building_name, r.room_number, bd.bed_number
        FROM allocation_history ah
        JOIN users u ON ah.user_id = u.id
        LEFT JOIN users op ON ah.operated_by = op.id
        JOIN rooms r ON ah.room_id = r.id
        JOIN buildings b ON r.building_id = b.id
        JOIN beds bd ON ah.bed_id = bd.id
        ORDER BY ah.operated_at DESC
        LIMIT 100
    ''')
    
    history = c.fetchall()
    conn.close()
    
    return jsonify({
        'history': [history_to_dict(h) for h in history]
    }), 200

@admin_bp.route('/unallocated-users', methods=['GET'])
@admin_required
def get_unallocated_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    conn = db.get_db()
    c = conn.cursor()
    
    # Get users who haven't selected a room
    base_query = '''
        SELECT u.* FROM users u
        WHERE u.is_admin = 0 
        AND u.id NOT IN (SELECT user_id FROM room_selections)
    '''
    
    if search:
        base_query += ' AND (u.username LIKE ? OR u.name LIKE ?)'
        search_params = (f'%{search}%', f'%{search}%')
        
        # Count total
        c.execute(f'SELECT COUNT(*) as total FROM ({base_query})', search_params)
        total = c.fetchone()['total']
        
        # Get users with pagination
        offset = (page - 1) * per_page
        c.execute(f'{base_query} ORDER BY u.id DESC LIMIT ? OFFSET ?', 
                 search_params + (per_page, offset))
    else:
        # Count total
        c.execute(f'SELECT COUNT(*) as total FROM ({base_query})')
        total = c.fetchone()['total']
        
        # Get users with pagination
        offset = (page - 1) * per_page
        c.execute(f'{base_query} ORDER BY u.id DESC LIMIT ? OFFSET ?', (per_page, offset))
    
    users = c.fetchall()
    conn.close()
    
    pages = (total + per_page - 1) // per_page
    
    return jsonify({
        'users': [user_to_dict(user) for user in users],
        'total': total,
        'pages': pages,
        'current_page': page
    }), 200

@admin_bp.route('/unallocated-room-type-users', methods=['GET'])
@admin_required
def get_unallocated_room_type_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    conn = db.get_db()
    c = conn.cursor()
    
    # Get users who haven't been allocated a room type
    base_query = '''
        SELECT u.* FROM users u
        WHERE u.is_admin = 0 
        AND u.id NOT IN (SELECT user_id FROM room_type_allocations)
    '''
    
    if search:
        base_query += ' AND (u.username LIKE ? OR u.name LIKE ?)'
        search_params = (f'%{search}%', f'%{search}%')
        
        # Count total
        c.execute(f'SELECT COUNT(*) as total FROM ({base_query})', search_params)
        total = c.fetchone()['total']
        
        # Get users with pagination
        offset = (page - 1) * per_page
        c.execute(f'{base_query} ORDER BY u.id DESC LIMIT ? OFFSET ?', 
                 search_params + (per_page, offset))
    else:
        # Count total
        c.execute(f'SELECT COUNT(*) as total FROM ({base_query})')
        total = c.fetchone()['total']
        
        # Get users with pagination
        offset = (page - 1) * per_page
        c.execute(f'{base_query} ORDER BY u.id DESC LIMIT ? OFFSET ?', (per_page, offset))
    
    users = c.fetchall()
    conn.close()
    
    pages = (total + per_page - 1) // per_page
    
    return jsonify({
        'users': [user_to_dict(user) for user in users],
        'total': total,
        'pages': pages,
        'current_page': page
    }), 200

@admin_bp.route('/allocations/<int:allocation_id>', methods=['PUT'])
@admin_required
def update_allocation(allocation_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    try:
        with db.get_db_connection() as conn:
            c = conn.cursor()
            
            # Check if allocation exists
            c.execute('SELECT * FROM room_selections WHERE id = ?', (allocation_id,))
            allocation = c.fetchone()
            if not allocation:
                return jsonify({'error': '分配记录不存在'}), 404
            
            # Update fields
            if 'is_confirmed' in data:
                c.execute('UPDATE room_selections SET is_confirmed = ? WHERE id = ?', 
                         (1 if data['is_confirmed'] else 0, allocation_id))
        
        return jsonify({'message': '分配更新成功'}), 200
    except Exception as e:
        return jsonify({'error': '更新失败'}), 500

@admin_bp.route('/lottery/results/<int:result_id>', methods=['PUT'])
@admin_required
def update_lottery_result(result_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    try:
        with db.get_db_connection() as conn:
            c = conn.cursor()
            
            # Check if lottery result exists
            c.execute('SELECT * FROM lottery_results WHERE id = ?', (result_id,))
            result = c.fetchone()
            if not result:
                return jsonify({'error': '抽签结果不存在'}), 404
            
            # Check if lottery is still draft (not published)
            c.execute('SELECT is_published FROM lottery_settings WHERE id = ?', (result['lottery_id'],))
            lottery_setting = c.fetchone()
            if lottery_setting and lottery_setting['is_published']:
                return jsonify({'error': '已发布的抽签结果不能修改'}), 400
            
            # Update fields
            update_fields = []
            update_params = []
            
            if 'lottery_number' in data:
                update_fields.append('lottery_number = ?')
                update_params.append(data['lottery_number'])
            
            if 'group_number' in data:
                update_fields.append('group_number = ?')
                update_params.append(data['group_number'])
            
            if 'room_type' in data:
                update_fields.append('room_type = ?')
                update_params.append(data['room_type'])
            
            if update_fields:
                update_params.append(result_id)
                c.execute(f'UPDATE lottery_results SET {", ".join(update_fields)} WHERE id = ?', update_params)
        
        return jsonify({'message': '抽签结果更新成功'}), 200
    except Exception as e:
        return jsonify({'error': f'更新失败: {str(e)}'}), 500

@admin_bp.route('/room-type-allocations/<int:allocation_id>', methods=['PUT'])
@admin_required
def update_room_type_allocation(allocation_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    try:
        with db.get_db_connection() as conn:
            c = conn.cursor()
            
            # Check if allocation exists
            c.execute('SELECT * FROM room_type_allocations WHERE id = ?', (allocation_id,))
            allocation = c.fetchone()
            if not allocation:
                return jsonify({'error': '寝室类型分配不存在'}), 404
            
            # Update fields
            update_fields = []
            update_params = []
            
            if 'room_type' in data:
                if data['room_type'] not in ['4', '8']:
                    return jsonify({'error': '房间类型必须是4或8'}), 400
                update_fields.append('room_type = ?')
                update_params.append(data['room_type'])
            
            if 'notes' in data:
                update_fields.append('notes = ?')
                update_params.append(data['notes'])
            
            if update_fields:
                update_params.append(allocation_id)
                c.execute(f'UPDATE room_type_allocations SET {", ".join(update_fields)} WHERE id = ?', update_params)
        
        return jsonify({'message': '寝室类型分配更新成功'}), 200
    except Exception as e:
        return jsonify({'error': '更新失败'}), 500

@admin_bp.route('/room-type-allocations/<int:allocation_id>', methods=['DELETE'])
@admin_required
def delete_room_type_allocation(allocation_id):
    try:
        with db.get_db_connection() as conn:
            c = conn.cursor()
            
            # Check if allocation exists
            c.execute('SELECT * FROM room_type_allocations WHERE id = ?', (allocation_id,))
            allocation = c.fetchone()
            if not allocation:
                return jsonify({'error': '寝室类型分配不存在'}), 404
            
            # Delete allocation
            c.execute('DELETE FROM room_type_allocations WHERE id = ?', (allocation_id,))
        
        return jsonify({'message': '寝室类型分配删除成功'}), 200
    except Exception as e:
        return jsonify({'error': '删除失败'}), 500