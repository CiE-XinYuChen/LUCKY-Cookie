import pandas as pd
import io
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from .models import db, User, LotterySetting, Building, Room, Bed, LotteryResult, RoomSelection, AllocationHistory
from .auth import admin_required
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.name.ilike(f'%{search}%')
            )
        )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if user.is_admin:
        return jsonify({'error': '不能删除管理员账户'}), 400
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': '用户删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除失败'}), 500

@admin_bp.route('/users/<int:user_id>/password', methods=['PUT'])
@admin_required
def reset_user_password(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    if not data or not data.get('new_password'):
        return jsonify({'error': '新密码不能为空'}), 400
    
    new_password = data.get('new_password')
    if len(new_password) < 6:
        return jsonify({'error': '密码长度不能少于6位'}), 400
    
    user.set_password(new_password)
    
    try:
        db.session.commit()
        return jsonify({'message': '密码重置成功'}), 200
    except Exception as e:
        db.session.rollback()
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
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 409
    
    try:
        user = User(username=username, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': '用户创建成功',
            'user': user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '用户创建失败'}), 500

@admin_bp.route('/users/import', methods=['POST'])
@admin_required
def import_users():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': '只支持CSV文件'}), 400
    
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = pd.read_csv(stream)
        
        required_columns = ['name', 'username', 'password']
        if not all(col in csv_input.columns for col in required_columns):
            return jsonify({'error': f'CSV文件必须包含以下列: {", ".join(required_columns)}'}), 400
        
        created_count = 0
        skipped_count = 0
        errors = []
        
        for index, row in csv_input.iterrows():
            try:
                username = str(row['username']).strip()
                password = str(row['password']).strip()
                name = str(row['name']).strip()
                
                if not username or not password or not name:
                    errors.append(f'第{index + 2}行: 用户名、密码和姓名不能为空')
                    continue
                
                if User.query.filter_by(username=username).first():
                    skipped_count += 1
                    continue
                
                if len(password) < 6:
                    errors.append(f'第{index + 2}行: 密码长度不能少于6位')
                    continue
                
                user = User(username=username, name=name)
                user.set_password(password)
                db.session.add(user)
                created_count += 1
                
            except Exception as e:
                errors.append(f'第{index + 2}行: {str(e)}')
        
        try:
            db.session.commit()
            return jsonify({
                'message': '用户导入完成',
                'created_count': created_count,
                'skipped_count': skipped_count,
                'errors': errors
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': '数据库保存失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'文件处理失败: {str(e)}'}), 500

@admin_bp.route('/buildings', methods=['GET'])
@admin_required
def get_buildings():
    buildings = Building.query.all()
    return jsonify({
        'buildings': [building.to_dict() for building in buildings]
    }), 200

@admin_bp.route('/buildings', methods=['POST'])
@admin_required
def create_building():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': '建筑名称不能为空'}), 400
    
    building = Building(
        name=data.get('name'),
        description=data.get('description', '')
    )
    
    try:
        db.session.add(building)
        db.session.commit()
        return jsonify({
            'message': '建筑创建成功',
            'building': building.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '创建失败'}), 500

@admin_bp.route('/rooms', methods=['GET'])
@admin_required
def get_rooms():
    building_id = request.args.get('building_id', type=int)
    room_type = request.args.get('room_type')
    
    query = Room.query
    if building_id:
        query = query.filter_by(building_id=building_id)
    if room_type:
        query = query.filter_by(room_type=room_type)
    
    rooms = query.all()
    return jsonify({
        'rooms': [room.to_dict() for room in rooms]
    }), 200

@admin_bp.route('/rooms', methods=['POST'])
@admin_required
def create_room():
    data = request.get_json()
    required_fields = ['building_id', 'room_number', 'room_type', 'max_capacity']
    
    if not data or not all(field in data for field in required_fields):
        return jsonify({'error': '缺少必要字段'}), 400
    
    building = Building.query.get(data['building_id'])
    if not building:
        return jsonify({'error': '建筑不存在'}), 404
    
    if Room.query.filter_by(building_id=data['building_id'], room_number=data['room_number']).first():
        return jsonify({'error': '房间号已存在'}), 409
    
    room = Room(
        building_id=data['building_id'],
        room_number=data['room_number'],
        room_type=data['room_type'],
        max_capacity=data['max_capacity']
    )
    
    try:
        db.session.add(room)
        db.session.flush()
        
        for i in range(1, data['max_capacity'] + 1):
            bed = Bed(room_id=room.id, bed_number=str(i))
            db.session.add(bed)
        
        db.session.commit()
        return jsonify({
            'message': '房间创建成功',
            'room': room.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '创建失败'}), 500

@admin_bp.route('/allocations', methods=['GET'])
@admin_required
def get_allocations():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = RoomSelection.query.paginate(page=page, per_page=per_page, error_out=False)
    allocations = pagination.items
    
    return jsonify({
        'allocations': [allocation.to_dict() for allocation in allocations],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@admin_bp.route('/allocations/<int:allocation_id>', methods=['PUT'])
@admin_required
def update_allocation(allocation_id):
    allocation = RoomSelection.query.get(allocation_id)
    if not allocation:
        return jsonify({'error': '分配记录不存在'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    current_user_id = get_jwt_identity()
    
    try:
        if 'room_id' in data and 'bed_id' in data:
            new_room = Room.query.get(data['room_id'])
            new_bed = Bed.query.get(data['bed_id'])
            
            if not new_room or not new_bed:
                return jsonify({'error': '房间或床位不存在'}), 404
            
            if new_bed.room_id != new_room.id:
                return jsonify({'error': '床位不属于指定房间'}), 400
            
            if new_bed.is_occupied and new_bed.id != allocation.bed_id:
                return jsonify({'error': '床位已被占用'}), 409
            
            old_bed = Bed.query.get(allocation.bed_id)
            if old_bed:
                old_bed.is_occupied = False
            
            new_bed.is_occupied = True
            allocation.room_id = data['room_id']
            allocation.bed_id = data['bed_id']
            
            history = AllocationHistory(
                user_id=allocation.user_id,
                room_id=data['room_id'],
                bed_id=data['bed_id'],
                action='modified',
                operated_by=current_user_id,
                notes=data.get('notes', '管理员修改分配')
            )
            db.session.add(history)
        
        if 'is_confirmed' in data:
            allocation.is_confirmed = data['is_confirmed']
        
        db.session.commit()
        return jsonify({
            'message': '分配更新成功',
            'allocation': allocation.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '更新失败'}), 500

@admin_bp.route('/allocations/<int:allocation_id>', methods=['DELETE'])
@admin_required
def delete_allocation(allocation_id):
    allocation = RoomSelection.query.get(allocation_id)
    if not allocation:
        return jsonify({'error': '分配记录不存在'}), 404
    
    current_user_id = get_jwt_identity()
    
    try:
        bed = Bed.query.get(allocation.bed_id)
        if bed:
            bed.is_occupied = False
        
        history = AllocationHistory(
            user_id=allocation.user_id,
            room_id=allocation.room_id,
            bed_id=allocation.bed_id,
            action='removed',
            operated_by=current_user_id,
            notes='管理员删除分配'
        )
        db.session.add(history)
        db.session.delete(allocation)
        db.session.commit()
        
        return jsonify({'message': '分配删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除失败'}), 500

@admin_bp.route('/allocation-history', methods=['GET'])
@admin_required
def get_allocation_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = AllocationHistory.query.order_by(AllocationHistory.operated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    history = pagination.items
    
    return jsonify({
        'history': [record.to_dict() for record in history],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200