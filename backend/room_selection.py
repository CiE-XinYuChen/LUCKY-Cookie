from flask import Blueprint, request, jsonify
from .auth import jwt_required, get_jwt_identity
from . import database as db
import time
import threading

room_selection_bp = Blueprint('room_selection', __name__, url_prefix='/api/room-selection')

# Simple in-memory lock implementation to replace Redis
class MemoryLock:
    def __init__(self):
        self.locks = {}
        self.lock = threading.Lock()
    
    def acquire(self, key, timeout=5):
        with self.lock:
            current_time = time.time()
            if key in self.locks:
                if current_time < self.locks[key]:
                    return False
            self.locks[key] = current_time + timeout
            return True
    
    def release(self, key):
        with self.lock:
            if key in self.locks:
                del self.locks[key]
    
    def clean_expired(self):
        with self.lock:
            current_time = time.time()
            expired_keys = [k for k, v in self.locks.items() if current_time > v]
            for key in expired_keys:
                del self.locks[key]

memory_lock = MemoryLock()

@room_selection_bp.route('/select', methods=['POST'])
@jwt_required()
def select_room():
    current_user_id = get_jwt_identity()
    # 将字符串ID转换为整数
    try:
        current_user_id = int(current_user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Token格式错误'}), 401
    user = db.get_user_by_id(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if user['is_admin']:
        return jsonify({'error': '管理员不能选择宿舍'}), 400
    
    # Check if user has published lottery result
    conn = db.get_db()
    c = conn.cursor()
    c.execute('''
        SELECT lr.*, ls.is_published, ls.room_type
        FROM lottery_results lr
        JOIN lottery_settings ls ON lr.lottery_id = ls.id
        WHERE lr.user_id = ? AND ls.is_published = 1
    ''', (current_user_id,))
    lottery_result = c.fetchone()
    conn.close()
    
    if not lottery_result:
        return jsonify({'error': '您还没有已发布的抽签结果，无法选择宿舍'}), 403
    
    data = request.get_json()
    if not data or not data.get('bed_id'):
        return jsonify({'error': '床位ID不能为空'}), 400
    
    bed_id = data.get('bed_id')
    lock_key = f"bed_selection:{bed_id}"
    
    # Clean expired locks
    memory_lock.clean_expired()
    
    if not memory_lock.acquire(lock_key):
        return jsonify({'error': '系统繁忙，请稍后重试'}), 503
    
    try:
        # Check if user already has a selection and cancel it if exists
        existing_selection = db.get_user_room_selection(current_user_id)
        if existing_selection:
            # Cancel existing selection
            db.cancel_room_selection(current_user_id)
        
        # Check bed availability
        conn = db.get_db()
        c = conn.cursor()
        c.execute('''
            SELECT b.*, r.id as room_id, r.is_available as room_available, r.room_type
            FROM beds b
            JOIN rooms r ON b.room_id = r.id
            WHERE b.id = ?
        ''', (bed_id,))
        bed_info = c.fetchone()
        conn.close()
        
        if not bed_info:
            return jsonify({'error': '床位不存在'}), 404
        
        if not bed_info['room_available']:
            return jsonify({'error': '房间不可用'}), 400
        
        # Check if room type matches lottery result
        if bed_info['room_type'] != lottery_result['room_type']:
            return jsonify({'error': f'您只能选择{lottery_result["room_type"]}人间的房间'}), 403
        
        if bed_info['is_occupied']:
            return jsonify({'error': '床位已被占用'}), 409
        
        # Check if bed is already selected by another user
        conn = db.get_db()
        c = conn.cursor()
        c.execute('SELECT id FROM room_selections WHERE bed_id = ?', (bed_id,))
        if c.fetchone():
            conn.close()
            return jsonify({'error': '床位已被其他用户选择'}), 409
        conn.close()
        
        try:
            # Select the room
            db.select_room(current_user_id, bed_info['room_id'], bed_id)
            
            # Add history
            with db.get_db_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO allocation_history (user_id, room_id, bed_id, action, operated_by, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (current_user_id, bed_info['room_id'], bed_id, 'assigned', current_user_id, '用户自主选择'))
            
            # Get the selection details
            selection = db.get_user_room_selection(current_user_id)
            
            return jsonify({
                'message': '宿舍选择成功',
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
            }), 201
            
        except Exception as e:
            return jsonify({'error': '选择失败，请重试'}), 500
    
    finally:
        memory_lock.release(lock_key)

@room_selection_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_selection():
    current_user_id = get_jwt_identity()
    # 将字符串ID转换为整数
    try:
        current_user_id = int(current_user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Token格式错误'}), 401
    user = db.get_user_by_id(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    selection = db.get_user_room_selection(current_user_id)
    if not selection:
        return jsonify({'error': '您还没有选择宿舍'}), 404
    
    lock_key = f"bed_selection:{selection['bed_id']}"
    
    if not memory_lock.acquire(lock_key):
        return jsonify({'error': '系统繁忙，请稍后重试'}), 503
    
    try:
        # Add history
        with db.get_db_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO allocation_history (user_id, room_id, bed_id, action, operated_by, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (current_user_id, selection['room_id'], selection['bed_id'], 'removed', current_user_id, '用户取消选择'))
        
        # Cancel the selection
        db.cancel_room_selection(current_user_id)
        
        return jsonify({'message': '选择已取消'}), 200
        
    except Exception as e:
        return jsonify({'error': '取消失败，请重试'}), 500
    
    finally:
        memory_lock.release(lock_key)

@room_selection_bp.route('/confirm', methods=['POST'])
@jwt_required()
def confirm_selection():
    current_user_id = get_jwt_identity()
    # 将字符串ID转换为整数
    try:
        current_user_id = int(current_user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Token格式错误'}), 401
    user = db.get_user_by_id(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    selection = db.get_user_room_selection(current_user_id)
    if not selection:
        return jsonify({'error': '您还没有选择宿舍'}), 404
    
    if selection['is_confirmed']:
        return jsonify({'error': '选择已经确认'}), 400
    
    try:
        with db.get_db_connection() as conn:
            c = conn.cursor()
            c.execute('UPDATE room_selections SET is_confirmed = 1 WHERE user_id = ?', (current_user_id,))
        
        # Get updated selection
        selection = db.get_user_room_selection(current_user_id)
        
        return jsonify({
            'message': '选择确认成功',
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
        
    except Exception as e:
        return jsonify({'error': '确认失败，请重试'}), 500

@room_selection_bp.route('/change', methods=['POST'])
@jwt_required()
def change_selection():
    current_user_id = get_jwt_identity()
    # 将字符串ID转换为整数
    try:
        current_user_id = int(current_user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Token格式错误'}), 401
    user = db.get_user_by_id(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # Check if user has published lottery result
    conn = db.get_db()
    c = conn.cursor()
    c.execute('''
        SELECT lr.*, ls.is_published, ls.room_type
        FROM lottery_results lr
        JOIN lottery_settings ls ON lr.lottery_id = ls.id
        WHERE lr.user_id = ? AND ls.is_published = 1
    ''', (current_user_id,))
    lottery_result = c.fetchone()
    conn.close()
    
    if not lottery_result:
        return jsonify({'error': '您还没有已发布的抽签结果，无法选择宿舍'}), 403
    
    data = request.get_json()
    if not data or not data.get('new_bed_id'):
        return jsonify({'error': '新床位ID不能为空'}), 400
    
    new_bed_id = data.get('new_bed_id')
    
    selection = db.get_user_room_selection(current_user_id)
    if not selection:
        return jsonify({'error': '您还没有选择宿舍'}), 404
    
    
    if selection['bed_id'] == new_bed_id:
        return jsonify({'error': '新床位与当前床位相同'}), 400
    
    old_lock_key = f"bed_selection:{selection['bed_id']}"
    new_lock_key = f"bed_selection:{new_bed_id}"
    
    # Try to acquire both locks
    if not memory_lock.acquire(old_lock_key):
        return jsonify({'error': '系统繁忙，请稍后重试'}), 503
    
    if not memory_lock.acquire(new_lock_key):
        memory_lock.release(old_lock_key)
        return jsonify({'error': '系统繁忙，请稍后重试'}), 503
    
    try:
        # Check new bed availability
        conn = db.get_db()
        c = conn.cursor()
        c.execute('''
            SELECT b.*, r.id as room_id, r.is_available as room_available, r.room_type
            FROM beds b
            JOIN rooms r ON b.room_id = r.id
            WHERE b.id = ?
        ''', (new_bed_id,))
        new_bed_info = c.fetchone()
        
        if not new_bed_info:
            conn.close()
            return jsonify({'error': '新床位不存在'}), 404
        
        # Check if room type matches lottery result
        if new_bed_info['room_type'] != lottery_result['room_type']:
            conn.close()
            return jsonify({'error': f'您只能选择{lottery_result["room_type"]}人间的房间'}), 403
        
        if new_bed_info['is_occupied']:
            conn.close()
            return jsonify({'error': '新床位已被占用'}), 409
        
        # Check if new bed is already selected
        c.execute('SELECT id FROM room_selections WHERE bed_id = ?', (new_bed_id,))
        if c.fetchone():
            conn.close()
            return jsonify({'error': '新床位已被其他用户选择'}), 409
        
        if not new_bed_info['room_available']:
            conn.close()
            return jsonify({'error': '新房间不可用'}), 400
        
        conn.close()
        
        try:
            # Cancel old selection
            db.cancel_room_selection(current_user_id)
            
            # Make new selection
            db.select_room(current_user_id, new_bed_info['room_id'], new_bed_id)
            
            # Add history
            with db.get_db_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO allocation_history (user_id, room_id, bed_id, action, operated_by, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (current_user_id, new_bed_info['room_id'], new_bed_id, 'modified', current_user_id, '用户更改选择'))
            
            # Get updated selection
            selection = db.get_user_room_selection(current_user_id)
            
            return jsonify({
                'message': '选择更改成功',
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
            
        except Exception as e:
            return jsonify({'error': '更改失败，请重试'}), 500
    
    finally:
        memory_lock.release(old_lock_key)
        memory_lock.release(new_lock_key)

@room_selection_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_selection_statistics():
    current_user_id = get_jwt_identity()
    # 将字符串ID转换为整数
    try:
        current_user_id = int(current_user_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Token格式错误'}), 401
    user = db.get_user_by_id(current_user_id)
    
    if not user or not user['is_admin']:
        return jsonify({'error': '需要管理员权限'}), 403
    
    conn = db.get_db()
    c = conn.cursor()
    
    # Total users (non-admin)
    c.execute('SELECT COUNT(*) as total FROM users WHERE is_admin = 0')
    total_users = c.fetchone()['total']
    
    # Total selections
    c.execute('SELECT COUNT(*) as total FROM room_selections')
    total_selections = c.fetchone()['total']
    
    # Confirmed selections
    c.execute('SELECT COUNT(*) as total FROM room_selections WHERE is_confirmed = 1')
    confirmed_selections = c.fetchone()['total']
    
    # Room statistics by type
    c.execute('''
        SELECT room_type,
               COUNT(*) as total_rooms,
               SUM(max_capacity) as total_capacity,
               SUM(current_occupancy) as current_occupancy
        FROM rooms
        GROUP BY room_type
    ''')
    
    room_stats = []
    for row in c.fetchall():
        room_stats.append({
            'room_type': row['room_type'],
            'total_rooms': row['total_rooms'],
            'total_capacity': row['total_capacity'],
            'current_occupancy': row['current_occupancy'],
            'occupancy_rate': round((row['current_occupancy'] / row['total_capacity'] * 100), 2) if row['total_capacity'] > 0 else 0
        })
    
    conn.close()
    
    return jsonify({
        'total_users': total_users,
        'total_selections': total_selections,
        'confirmed_selections': confirmed_selections,
        'unselected_users': total_users - total_selections,
        'room_statistics': room_stats
    }), 200