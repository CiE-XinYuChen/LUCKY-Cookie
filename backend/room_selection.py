from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db, User, Room, Bed, RoomSelection, AllocationHistory
from .redis_lock import get_redis_client, redis_lock

room_selection_bp = Blueprint('room_selection', __name__, url_prefix='/api/room-selection')

@room_selection_bp.route('/select', methods=['POST'])
@jwt_required()
def select_room():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if user.is_admin:
        return jsonify({'error': '管理员不能选择宿舍'}), 400
    
    data = request.get_json()
    if not data or not data.get('bed_id'):
        return jsonify({'error': '床位ID不能为空'}), 400
    
    bed_id = data.get('bed_id')
    
    redis_client = get_redis_client()
    lock_key = f"bed_selection:{bed_id}"
    
    try:
        with redis_lock(redis_client, lock_key, timeout=5):
            existing_selection = RoomSelection.query.filter_by(user_id=current_user_id).first()
            if existing_selection:
                return jsonify({'error': '您已经选择了宿舍，不能重复选择'}), 409
            
            bed = Bed.query.get(bed_id)
            if not bed:
                return jsonify({'error': '床位不存在'}), 404
            
            room = Room.query.get(bed.room_id)
            if not room or not room.is_available:
                return jsonify({'error': '房间不可用'}), 400
            
            if bed.is_occupied:
                return jsonify({'error': '床位已被占用'}), 409
            
            existing_bed_selection = RoomSelection.query.filter_by(bed_id=bed_id).first()
            if existing_bed_selection:
                return jsonify({'error': '床位已被其他用户选择'}), 409
            
            try:
                bed.is_occupied = True
                room.current_occupancy += 1
                
                selection = RoomSelection(
                    user_id=current_user_id,
                    room_id=room.id,
                    bed_id=bed_id,
                    is_confirmed=False
                )
                
                history = AllocationHistory(
                    user_id=current_user_id,
                    room_id=room.id,
                    bed_id=bed_id,
                    action='assigned',
                    operated_by=current_user_id,
                    notes='用户自主选择'
                )
                
                db.session.add(selection)
                db.session.add(history)
                db.session.commit()
                
                return jsonify({
                    'message': '宿舍选择成功',
                    'selection': selection.to_dict()
                }), 201
                
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': '选择失败，请重试'}), 500
                
    except Exception as e:
        return jsonify({'error': '系统繁忙，请稍后重试'}), 503

@room_selection_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_selection():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    selection = RoomSelection.query.filter_by(user_id=current_user_id).first()
    if not selection:
        return jsonify({'error': '您还没有选择宿舍'}), 404
    
    if selection.is_confirmed:
        return jsonify({'error': '已确认的选择不能取消'}), 400
    
    redis_client = get_redis_client()
    lock_key = f"bed_selection:{selection.bed_id}"
    
    try:
        with redis_lock(redis_client, lock_key, timeout=5):
            try:
                bed = Bed.query.get(selection.bed_id)
                room = Room.query.get(selection.room_id)
                
                if bed:
                    bed.is_occupied = False
                if room:
                    room.current_occupancy = max(0, room.current_occupancy - 1)
                
                history = AllocationHistory(
                    user_id=current_user_id,
                    room_id=selection.room_id,
                    bed_id=selection.bed_id,
                    action='removed',
                    operated_by=current_user_id,
                    notes='用户取消选择'
                )
                
                db.session.add(history)
                db.session.delete(selection)
                db.session.commit()
                
                return jsonify({'message': '选择已取消'}), 200
                
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': '取消失败，请重试'}), 500
                
    except Exception as e:
        return jsonify({'error': '系统繁忙，请稍后重试'}), 503

@room_selection_bp.route('/confirm', methods=['POST'])
@jwt_required()
def confirm_selection():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    selection = RoomSelection.query.filter_by(user_id=current_user_id).first()
    if not selection:
        return jsonify({'error': '您还没有选择宿舍'}), 404
    
    if selection.is_confirmed:
        return jsonify({'error': '选择已经确认'}), 400
    
    try:
        selection.is_confirmed = True
        db.session.commit()
        
        return jsonify({
            'message': '选择确认成功',
            'selection': selection.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '确认失败，请重试'}), 500

@room_selection_bp.route('/change', methods=['POST'])
@jwt_required()
def change_selection():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    if not data or not data.get('new_bed_id'):
        return jsonify({'error': '新床位ID不能为空'}), 400
    
    new_bed_id = data.get('new_bed_id')
    
    selection = RoomSelection.query.filter_by(user_id=current_user_id).first()
    if not selection:
        return jsonify({'error': '您还没有选择宿舍'}), 404
    
    if selection.is_confirmed:
        return jsonify({'error': '已确认的选择不能更改'}), 400
    
    if selection.bed_id == new_bed_id:
        return jsonify({'error': '新床位与当前床位相同'}), 400
    
    redis_client = get_redis_client()
    old_lock_key = f"bed_selection:{selection.bed_id}"
    new_lock_key = f"bed_selection:{new_bed_id}"
    
    locks_acquired = []
    try:
        for lock_key in [old_lock_key, new_lock_key]:
            lock = redis_client.set(f"lock:{lock_key}", current_user_id, nx=True, ex=5)
            if not lock:
                for acquired_key in locks_acquired:
                    redis_client.delete(f"lock:{acquired_key}")
                return jsonify({'error': '系统繁忙，请稍后重试'}), 503
            locks_acquired.append(lock_key)
        
        new_bed = Bed.query.get(new_bed_id)
        if not new_bed:
            return jsonify({'error': '新床位不存在'}), 404
        
        if new_bed.is_occupied:
            return jsonify({'error': '新床位已被占用'}), 409
        
        existing_new_selection = RoomSelection.query.filter_by(bed_id=new_bed_id).first()
        if existing_new_selection:
            return jsonify({'error': '新床位已被其他用户选择'}), 409
        
        new_room = Room.query.get(new_bed.room_id)
        if not new_room or not new_room.is_available:
            return jsonify({'error': '新房间不可用'}), 400
        
        try:
            old_bed = Bed.query.get(selection.bed_id)
            old_room = Room.query.get(selection.room_id)
            
            if old_bed:
                old_bed.is_occupied = False
            if old_room:
                old_room.current_occupancy = max(0, old_room.current_occupancy - 1)
            
            new_bed.is_occupied = True
            new_room.current_occupancy += 1
            
            selection.room_id = new_room.id
            selection.bed_id = new_bed_id
            
            history = AllocationHistory(
                user_id=current_user_id,
                room_id=new_room.id,
                bed_id=new_bed_id,
                action='modified',
                operated_by=current_user_id,
                notes='用户更改选择'
            )
            
            db.session.add(history)
            db.session.commit()
            
            return jsonify({
                'message': '选择更改成功',
                'selection': selection.to_dict()
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': '更改失败，请重试'}), 500
            
    finally:
        for lock_key in locks_acquired:
            redis_client.delete(f"lock:{lock_key}")

@room_selection_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_selection_statistics():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': '需要管理员权限'}), 403
    
    total_users = User.query.filter_by(is_admin=False).count()
    total_selections = RoomSelection.query.count()
    confirmed_selections = RoomSelection.query.filter_by(is_confirmed=True).count()
    
    room_stats = db.session.query(
        Room.room_type,
        db.func.count(Room.id).label('total_rooms'),
        db.func.sum(Room.max_capacity).label('total_capacity'),
        db.func.sum(Room.current_occupancy).label('current_occupancy')
    ).group_by(Room.room_type).all()
    
    return jsonify({
        'total_users': total_users,
        'total_selections': total_selections,
        'confirmed_selections': confirmed_selections,
        'unselected_users': total_users - total_selections,
        'room_statistics': [
            {
                'room_type': stat.room_type,
                'total_rooms': stat.total_rooms,
                'total_capacity': stat.total_capacity,
                'current_occupancy': stat.current_occupancy,
                'occupancy_rate': round((stat.current_occupancy / stat.total_capacity * 100), 2) if stat.total_capacity > 0 else 0
            }
            for stat in room_stats
        ]
    }), 200