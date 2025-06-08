import random
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db, User, LotterySetting, Building, Room, Bed, LotteryResult, RoomSelection, AllocationHistory
from .auth import admin_required

lottery_bp = Blueprint('lottery', __name__, url_prefix='/api/lottery')

@lottery_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_lottery_settings():
    settings = LotterySetting.query.order_by(LotterySetting.created_at.desc()).all()
    return jsonify({
        'settings': [setting.to_dict() for setting in settings]
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
    
    setting = LotterySetting(
        lottery_name=data['lottery_name'],
        lottery_time=lottery_time,
        room_type=data['room_type']
    )
    
    try:
        db.session.add(setting)
        db.session.commit()
        return jsonify({
            'message': '抽签设置创建成功',
            'setting': setting.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '创建失败'}), 500

@lottery_bp.route('/settings/<int:setting_id>/publish', methods=['POST'])
@admin_required
def publish_lottery(setting_id):
    setting = LotterySetting.query.get(setting_id)
    if not setting:
        return jsonify({'error': '抽签设置不存在'}), 404
    
    if setting.is_published:
        return jsonify({'error': '抽签结果已经公布'}), 400
    
    try:
        users = User.query.filter_by(is_admin=False).all()
        if not users:
            return jsonify({'error': '没有可参与抽签的用户'}), 400
        
        existing_results = LotteryResult.query.filter_by(lottery_id=setting_id).first()
        if existing_results:
            return jsonify({'error': '该抽签已有结果，不能重复生成'}), 400
        
        user_ids = [user.id for user in users]
        random.shuffle(user_ids)
        
        lottery_results = []
        group_size = 4 if setting.room_type == '4' else 8
        
        for i, user_id in enumerate(user_ids):
            result = LotteryResult(
                user_id=user_id,
                lottery_id=setting_id,
                lottery_number=i + 1,
                group_number=(i // group_size) + 1
            )
            lottery_results.append(result)
        
        db.session.add_all(lottery_results)
        setting.is_published = True
        db.session.commit()
        
        return jsonify({
            'message': '抽签结果生成并公布成功',
            'total_participants': len(users),
            'total_groups': (len(users) - 1) // group_size + 1
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '公布失败'}), 500

@lottery_bp.route('/results', methods=['GET'])
@jwt_required()
def get_lottery_results():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    lottery_id = request.args.get('lottery_id', type=int)
    
    if user.is_admin:
        query = LotteryResult.query
        if lottery_id:
            query = query.filter_by(lottery_id=lottery_id)
        results = query.order_by(LotteryResult.lottery_number).all()
    else:
        query = LotteryResult.query.filter_by(user_id=current_user_id)
        if lottery_id:
            query = query.filter_by(lottery_id=lottery_id)
        results = query.all()
    
    return jsonify({
        'results': [result.to_dict() for result in results]
    }), 200

@lottery_bp.route('/results/<int:result_id>', methods=['PUT'])
@admin_required
def update_lottery_result(result_id):
    result = LotteryResult.query.get(result_id)
    if not result:
        return jsonify({'error': '抽签结果不存在'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    try:
        if 'lottery_number' in data:
            if LotteryResult.query.filter_by(
                lottery_id=result.lottery_id,
                lottery_number=data['lottery_number']
            ).filter(LotteryResult.id != result_id).first():
                return jsonify({'error': '抽签号码已存在'}), 409
            result.lottery_number = data['lottery_number']
        
        if 'group_number' in data:
            result.group_number = data['group_number']
        
        db.session.commit()
        return jsonify({
            'message': '抽签结果更新成功',
            'result': result.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '更新失败'}), 500

@lottery_bp.route('/rooms/available', methods=['GET'])
@jwt_required()
def get_available_rooms():
    room_type = request.args.get('room_type')
    building_id = request.args.get('building_id', type=int)
    
    query = Room.query.filter_by(is_available=True)
    if room_type:
        query = query.filter_by(room_type=room_type)
    if building_id:
        query = query.filter_by(building_id=building_id)
    
    rooms = query.all()
    
    available_rooms = []
    for room in rooms:
        if room.current_occupancy < room.max_capacity:
            room_data = room.to_dict()
            room_data['available_beds'] = len([bed for bed in room.beds if not bed.is_occupied])
            
            occupied_users = []
            for bed in room.beds:
                if bed.is_occupied:
                    selection = RoomSelection.query.filter_by(bed_id=bed.id).first()
                    if selection and selection.user:
                        occupied_users.append({
                            'name': selection.user.name,
                            'bed_number': bed.bed_number
                        })
            room_data['occupied_users'] = occupied_users
            available_rooms.append(room_data)
    
    return jsonify({
        'rooms': available_rooms
    }), 200

@lottery_bp.route('/my-selection', methods=['GET'])
@jwt_required()
def get_my_selection():
    current_user_id = get_jwt_identity()
    selection = RoomSelection.query.filter_by(user_id=current_user_id).first()
    
    if not selection:
        return jsonify({'selection': None}), 200
    
    return jsonify({
        'selection': selection.to_dict()
    }), 200