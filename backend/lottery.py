import random
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .auth import admin_required
from . import database as db

lottery_bp = Blueprint('lottery', __name__, url_prefix='/api/lottery')

def lottery_setting_to_dict(lottery):
    return {
        'id': lottery['id'],
        'lottery_name': lottery['lottery_name'],
        'lottery_time': lottery['lottery_time'],
        'is_published': bool(lottery['is_published']),
        'room_type': lottery['room_type'],
        'created_at': lottery['created_at']
    }

def lottery_result_to_dict(result):
    return {
        'id': result['id'],
        'user_id': result['user_id'],
        'user_name': result['user_name'] if 'user_name' in result.keys() else None,
        'lottery_id': result['lottery_id'],
        'lottery_number': result['lottery_number'],
        'group_number': result['group_number'],
        'room_type': result['room_type'] if 'room_type' in result.keys() else None,
        'created_at': result['created_at'],
        'is_published': result['is_published'] if 'is_published' in result.keys() else None,
        'lottery_name': result['lottery_name'] if 'lottery_name' in result.keys() else None
    }

@lottery_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_lottery_settings():
    conn = db.get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM lottery_settings ORDER BY created_at DESC')
    settings = c.fetchall()
    conn.close()
    
    return jsonify({
        'settings': [lottery_setting_to_dict(s) for s in settings]
    }), 200

@lottery_bp.route('/settings', methods=['POST'])
@admin_required
def create_lottery_setting():
    data = request.get_json()
    required_fields = ['lottery_name', 'lottery_time', 'room_type']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': '缺少必要字段'}), 400
    
    try:
        lottery_time = datetime.fromisoformat(data['lottery_time'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': '时间格式错误'}), 400
    
    if data['room_type'] not in ['4', '8']:
        return jsonify({'error': '房间类型只能是4或8'}), 400
    
    try:
        lottery_id = db.create_lottery(
            data['lottery_name'],
            lottery_time.isoformat(),
            data['room_type']
        )
        
        # Get the created lottery
        conn = db.get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM lottery_settings WHERE id = ?', (lottery_id,))
        setting = c.fetchone()
        conn.close()
        
        return jsonify({
            'message': '抽签设置创建成功',
            'setting': lottery_setting_to_dict(setting)
        }), 201
    except Exception as e:
        return jsonify({'error': '创建失败'}), 500

@lottery_bp.route('/settings/<int:setting_id>/publish', methods=['POST'])
@admin_required
def publish_lottery(setting_id):
    data = request.get_json() or {}
    
    conn = db.get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM lottery_settings WHERE id = ?', (setting_id,))
    setting = c.fetchone()
    conn.close()
    
    if not setting:
        return jsonify({'error': '抽签设置不存在'}), 404
    
    if setting['is_published']:
        return jsonify({'error': '抽签结果已经公布'}), 400
    
    try:
        # Get all non-admin users
        conn = db.get_db()
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE is_admin = 0')
        users = c.fetchall()
        
        if not users:
            return jsonify({'error': '没有可参与抽签的用户'}), 400
        
        # Check if results already exist
        c.execute('SELECT COUNT(*) as cnt FROM lottery_results WHERE lottery_id = ?', (setting_id,))
        if c.fetchone()['cnt'] > 0:
            conn.close()
            return jsonify({'error': '该抽签已有结果，不能重复生成'}), 400
        
        conn.close()
        
        # Shuffle users
        user_ids = [user['id'] for user in users]
        random.shuffle(user_ids)
        
        # 获取四人寝和六人寝数量
        room_4_count = data.get('room_4_count', 0)
        room_6_count = data.get('room_6_count', 0)
        
        # 计算分配
        total_4_beds = room_4_count * 4
        total_6_beds = room_6_count * 6
        total_beds = total_4_beds + total_6_beds
        
        if total_beds == 0:
            return jsonify({'error': '四人寝和六人寝数量不能都为0'}), 400
        
        if len(user_ids) > total_beds:
            return jsonify({'error': f'参与用户数({len(user_ids)})超过总床位数({total_beds})'}), 400
        
        with db.get_db_connection() as conn:
            c = conn.cursor()
            
            # 分配用户到不同类型的寝室
            allocated_users = 0
            group_4_count = 0
            group_6_count = 0
            
            # 先分配四人寝
            for group in range(room_4_count):
                start_idx = allocated_users
                end_idx = min(allocated_users + 4, len(user_ids))
                group_4_count += 1
                
                for i in range(start_idx, end_idx):
                    c.execute(
                        'INSERT INTO lottery_results (user_id, lottery_id, lottery_number, group_number, room_type) VALUES (?, ?, ?, ?, ?)',
                        (user_ids[i], setting_id, i + 1, f'4-{group_4_count}', '4')
                    )
                
                allocated_users = end_idx
                if allocated_users >= len(user_ids):
                    break
            
            # 再分配六人寝
            for group in range(room_6_count):
                start_idx = allocated_users
                end_idx = min(allocated_users + 6, len(user_ids))
                if start_idx >= len(user_ids):
                    break
                
                group_6_count += 1
                
                for i in range(start_idx, end_idx):
                    c.execute(
                        'INSERT INTO lottery_results (user_id, lottery_id, lottery_number, group_number, room_type) VALUES (?, ?, ?, ?, ?)',
                        (user_ids[i], setting_id, i + 1, f'6-{group_6_count}', '6')
                    )
                
                allocated_users = end_idx
            
            # Publish the lottery
            c.execute('UPDATE lottery_settings SET is_published = 1 WHERE id = ?', (setting_id,))
        
        return jsonify({
            'message': '抽签结果生成并公布成功',
            'total_participants': len(user_ids),
            'allocated_participants': allocated_users,
            'room_4_groups': group_4_count,
            'room_6_groups': group_6_count,
            'total_4_beds': total_4_beds,
            'total_6_beds': total_6_beds
        }), 200
    except Exception as e:
        return jsonify({'error': f'公布失败: {str(e)}'}), 500

@lottery_bp.route('/results', methods=['GET'])
@jwt_required()
def get_lottery_results():
    current_user_id = get_jwt_identity()
    user = db.get_user_by_id(current_user_id)
    
    lottery_id = request.args.get('lottery_id', type=int)
    
    conn = db.get_db()
    c = conn.cursor()
    
    if user['is_admin']:
        if lottery_id:
            c.execute('''
                SELECT lr.*, u.name as user_name
                FROM lottery_results lr
                JOIN users u ON lr.user_id = u.id
                WHERE lr.lottery_id = ?
                ORDER BY lr.lottery_number
            ''', (lottery_id,))
        else:
            c.execute('''
                SELECT lr.*, u.name as user_name
                FROM lottery_results lr
                JOIN users u ON lr.user_id = u.id
                ORDER BY lr.lottery_number
            ''')
    else:
        # 学生可以查看自己的所有抽签结果（包括未发布的）
        if lottery_id:
            c.execute('''
                SELECT lr.*, u.name as user_name, ls.is_published, ls.lottery_name
                FROM lottery_results lr
                JOIN users u ON lr.user_id = u.id
                JOIN lottery_settings ls ON lr.lottery_id = ls.id
                WHERE lr.user_id = ? AND lr.lottery_id = ?
            ''', (current_user_id, lottery_id))
        else:
            c.execute('''
                SELECT lr.*, u.name as user_name, ls.is_published, ls.lottery_name
                FROM lottery_results lr
                JOIN users u ON lr.user_id = u.id
                JOIN lottery_settings ls ON lr.lottery_id = ls.id
                WHERE lr.user_id = ?
                ORDER BY lr.created_at DESC
            ''', (current_user_id,))
    
    results = c.fetchall()
    conn.close()
    
    return jsonify({
        'results': [lottery_result_to_dict(r) for r in results]
    }), 200

@lottery_bp.route('/results/<int:result_id>', methods=['PUT'])
@admin_required
def update_lottery_result(result_id):
    conn = db.get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM lottery_results WHERE id = ?', (result_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return jsonify({'error': '抽签结果不存在'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    try:
        with db.get_db_connection() as conn:
            c = conn.cursor()
            
            if 'lottery_number' in data:
                # Check if number already exists
                c.execute(
                    'SELECT COUNT(*) as cnt FROM lottery_results WHERE lottery_id = ? AND lottery_number = ? AND id != ?',
                    (result['lottery_id'], data['lottery_number'], result_id)
                )
                if c.fetchone()['cnt'] > 0:
                    return jsonify({'error': '抽签号码已存在'}), 409
                
                c.execute(
                    'UPDATE lottery_results SET lottery_number = ? WHERE id = ?',
                    (data['lottery_number'], result_id)
                )
            
            if 'group_number' in data:
                c.execute(
                    'UPDATE lottery_results SET group_number = ? WHERE id = ?',
                    (data['group_number'], result_id)
                )
        
        # Get updated result
        conn = db.get_db()
        c = conn.cursor()
        c.execute('''
            SELECT lr.*, u.name as user_name
            FROM lottery_results lr
            JOIN users u ON lr.user_id = u.id
            WHERE lr.id = ?
        ''', (result_id,))
        updated_result = c.fetchone()
        conn.close()
        
        return jsonify({
            'message': '抽签结果更新成功',
            'result': lottery_result_to_dict(updated_result)
        }), 200
    except Exception as e:
        return jsonify({'error': '更新失败'}), 500

@lottery_bp.route('/rooms/available', methods=['GET'])
@jwt_required()
def get_available_rooms():
    room_type = request.args.get('room_type')
    building_id = request.args.get('building_id', type=int)
    
    conn = db.get_db()
    c = conn.cursor()
    
    query = '''
        SELECT r.*, b.name as building_name,
               (SELECT COUNT(*) FROM beds WHERE room_id = r.id AND is_occupied = 0) as available_beds
        FROM rooms r
        JOIN buildings b ON r.building_id = b.id
        WHERE r.is_available = 1 AND r.current_occupancy < r.max_capacity
    '''
    
    params = []
    if room_type:
        query += ' AND r.room_type = ?'
        params.append(room_type)
    if building_id:
        query += ' AND r.building_id = ?'
        params.append(building_id)
    
    query += ' ORDER BY b.name, r.room_number'
    
    if params:
        c.execute(query, params)
    else:
        c.execute(query)
    
    rooms = c.fetchall()
    
    available_rooms = []
    for room in rooms:
        room_data = {
            'id': room['id'],
            'building_id': room['building_id'],
            'building_name': room['building_name'],
            'room_number': room['room_number'],
            'room_type': room['room_type'],
            'max_capacity': room['max_capacity'],
            'current_occupancy': room['current_occupancy'],
            'is_available': bool(room['is_available']),
            'available_beds': room['available_beds'],
            'beds': []
        }
        
        # Get bed details with occupancy info
        c.execute('''
            SELECT b.*, rs.user_id, u.name as user_name
            FROM beds b
            LEFT JOIN room_selections rs ON b.id = rs.bed_id
            LEFT JOIN users u ON rs.user_id = u.id
            WHERE b.room_id = ?
            ORDER BY b.bed_number
        ''', (room['id'],))
        
        beds = c.fetchall()
        occupied_users = []
        
        for bed in beds:
            bed_info = {
                'id': bed['id'],
                'bed_number': bed['bed_number'],
                'is_occupied': bool(bed['is_occupied'])
            }
            room_data['beds'].append(bed_info)
            
            if bed['user_id']:
                occupied_users.append({
                    'name': bed['user_name'],
                    'bed_number': bed['bed_number']
                })
        
        room_data['occupied_users'] = occupied_users
        available_rooms.append(room_data)
    
    conn.close()
    
    return jsonify({
        'rooms': available_rooms
    }), 200

@lottery_bp.route('/my-selection', methods=['GET'])
@jwt_required()
def get_my_selection():
    current_user_id = get_jwt_identity()
    selection = db.get_user_room_selection(current_user_id)
    
    if not selection:
        return jsonify({'selection': None}), 200
    
    return jsonify({
        'selection': {
            'id': selection['id'],
            'user_id': selection['user_id'],
            'room_id': selection['room_id'],
            'room_number': selection['room_number'],
            'room_type': selection['room_type'],
            'building_name': selection['building_name'],
            'bed_id': selection['bed_id'],
            'bed_number': selection['bed_number'],
            'selected_at': selection['selected_at'],
            'is_confirmed': bool(selection['is_confirmed'])
        }
    }), 200