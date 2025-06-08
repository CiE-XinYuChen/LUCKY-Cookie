from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lottery_results = db.relationship('LotteryResult', backref='user', lazy=True)
    room_selections = db.relationship('RoomSelection', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        try:
            # Try bcrypt first (new method)
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception:
            # Fallback to werkzeug for old password hashes
            from werkzeug.security import check_password_hash
            return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class LotterySetting(db.Model):
    __tablename__ = 'lottery_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    lottery_name = db.Column(db.String(100), nullable=False)
    lottery_time = db.Column(db.DateTime, nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    room_type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    lottery_results = db.relationship('LotteryResult', backref='lottery_setting', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'lottery_name': self.lottery_name,
            'lottery_time': self.lottery_time.isoformat() if self.lottery_time else None,
            'is_published': self.is_published,
            'room_type': self.room_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Building(db.Model):
    __tablename__ = 'buildings'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    rooms = db.relationship('Room', backref='building', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Room(db.Model):
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'), nullable=False)
    room_number = db.Column(db.String(20), nullable=False)
    room_type = db.Column(db.String(10), nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    current_occupancy = db.Column(db.Integer, default=0)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    beds = db.relationship('Bed', backref='room', lazy=True)
    room_selections = db.relationship('RoomSelection', backref='room', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('building_id', 'room_number'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'building_id': self.building_id,
            'building_name': self.building.name if self.building else None,
            'room_number': self.room_number,
            'room_type': self.room_type,
            'max_capacity': self.max_capacity,
            'current_occupancy': self.current_occupancy,
            'is_available': self.is_available,
            'available_beds': len([bed for bed in self.beds if not bed.is_occupied]),
            'beds': [bed.to_dict() for bed in self.beds]
        }

class Bed(db.Model):
    __tablename__ = 'beds'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    bed_number = db.Column(db.String(10), nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    room_selections = db.relationship('RoomSelection', backref='bed', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('room_id', 'bed_number'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'bed_number': self.bed_number,
            'is_occupied': self.is_occupied
        }

class LotteryResult(db.Model):
    __tablename__ = 'lottery_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lottery_id = db.Column(db.Integer, db.ForeignKey('lottery_settings.id'), nullable=False)
    lottery_number = db.Column(db.Integer, nullable=False)
    group_number = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'lottery_id'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'lottery_id': self.lottery_id,
            'lottery_number': self.lottery_number,
            'group_number': self.group_number,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RoomSelection(db.Model):
    __tablename__ = 'room_selections'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'), nullable=False)
    selected_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_confirmed = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        db.UniqueConstraint('user_id'),
        db.UniqueConstraint('bed_id')
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'room_id': self.room_id,
            'room_number': self.room.room_number if self.room else None,
            'building_name': self.room.building.name if self.room and self.room.building else None,
            'bed_id': self.bed_id,
            'bed_number': self.bed.bed_number if self.bed else None,
            'selected_at': self.selected_at.isoformat() if self.selected_at else None,
            'is_confirmed': self.is_confirmed
        }

class AllocationHistory(db.Model):
    __tablename__ = 'allocation_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    operated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    operated_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    user = db.relationship('User', foreign_keys=[user_id], backref='allocation_history')
    operator = db.relationship('User', foreign_keys=[operated_by])
    room = db.relationship('Room', backref='allocation_history')
    bed = db.relationship('Bed', backref='allocation_history')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_name': self.user.name if self.user else None,
            'room_info': f"{self.room.building.name}-{self.room.room_number}" if self.room and self.room.building else None,
            'bed_number': self.bed.bed_number if self.bed else None,
            'action': self.action,
            'operator_name': self.operator.name if self.operator else None,
            'operated_at': self.operated_at.isoformat() if self.operated_at else None,
            'notes': self.notes
        }