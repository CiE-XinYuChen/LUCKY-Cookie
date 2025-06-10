import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
import bcrypt
from config import Config

def get_db():
    """Create a database connection and configure it to return rows as dictionaries."""
    conn = sqlite3.connect(Config.DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize the database by creating necessary tables if they don't exist."""
    conn = get_db()
    c = conn.cursor()
    
    # 启用外键约束
    c.execute("PRAGMA foreign_keys = ON")
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Buildings table
    c.execute('''CREATE TABLE IF NOT EXISTS buildings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Rooms table
    c.execute('''CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        building_id INTEGER NOT NULL,
        room_number TEXT NOT NULL,
        room_type TEXT NOT NULL,
        max_capacity INTEGER NOT NULL,
        current_occupancy INTEGER DEFAULT 0,
        is_available INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (building_id) REFERENCES buildings(id),
        UNIQUE(building_id, room_number)
    )''')
    
    # Beds table
    c.execute('''CREATE TABLE IF NOT EXISTS beds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER NOT NULL,
        bed_number TEXT NOT NULL,
        is_occupied INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (room_id) REFERENCES rooms(id),
        UNIQUE(room_id, bed_number)
    )''')
    
    # Lottery settings table
    c.execute('''CREATE TABLE IF NOT EXISTS lottery_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lottery_name TEXT NOT NULL,
        lottery_time DATETIME NOT NULL,
        is_published INTEGER DEFAULT 0,
        room_type TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Lottery results table
    c.execute('''CREATE TABLE IF NOT EXISTS lottery_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        lottery_id INTEGER NOT NULL,
        lottery_number INTEGER NOT NULL,
        group_number TEXT,
        room_type TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (lottery_id) REFERENCES lottery_settings(id),
        UNIQUE(user_id, lottery_id)
    )''')
    
    # Room selections table
    c.execute('''CREATE TABLE IF NOT EXISTS room_selections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        room_id INTEGER NOT NULL,
        bed_id INTEGER NOT NULL UNIQUE,
        selected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_confirmed INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (room_id) REFERENCES rooms(id),
        FOREIGN KEY (bed_id) REFERENCES beds(id)
    )''')
    
    # Room type allocations table
    c.execute('''CREATE TABLE IF NOT EXISTS room_type_allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        room_type TEXT NOT NULL,
        allocated_by INTEGER,
        allocated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (allocated_by) REFERENCES users(id)
    )''')
    
    # Allocation history table
    c.execute('''CREATE TABLE IF NOT EXISTS allocation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        room_id INTEGER NOT NULL,
        bed_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        operated_by INTEGER,
        operated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (room_id) REFERENCES rooms(id),
        FOREIGN KEY (bed_id) REFERENCES beds(id),
        FOREIGN KEY (operated_by) REFERENCES users(id)
    )''')
    
    # Auth tokens table (for simple auth system)
    c.execute('''CREATE TABLE IF NOT EXISTS auth_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )''')
    
    # Create indexes for auth_tokens
    c.execute('CREATE INDEX IF NOT EXISTS idx_auth_tokens_token ON auth_tokens(token)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_id ON auth_tokens(user_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires_at ON auth_tokens(expires_at)')
    
    conn.commit()
    
    # 检查并添加新字段（数据库迁移）
    try:
        # 检查lottery_results表是否有room_type字段
        c.execute("PRAGMA table_info(lottery_results)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'room_type' not in columns:
            c.execute('ALTER TABLE lottery_results ADD COLUMN room_type TEXT')
            print("添加 room_type 字段到 lottery_results 表")
        
        # 检查group_number字段类型
        if 'group_number' in columns:
            # SQLite不支持直接修改字段类型，但由于我们存储的是字符串，这里不需要特殊处理
            pass
        
        conn.commit()
    except Exception as e:
        print(f"数据库迁移错误: {e}")
    
    # Create default admin user if not exists
    c.execute('SELECT COUNT(*) as cnt FROM users WHERE username = ?', ('admin',))
    if c.fetchone()['cnt'] == 0:
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        c.execute(
            'INSERT INTO users (username, password_hash, name, is_admin) VALUES (?, ?, ?, ?)',
            ('admin', password_hash, '管理员', 1)
        )
        conn.commit()
    
    conn.close()

# User operations
def create_user(username, password, name, is_admin=False):
    """Create a new user."""
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            'INSERT INTO users (username, password_hash, name, is_admin) VALUES (?, ?, ?, ?)',
            (username, password_hash, name, 1 if is_admin else 0)
        )
        return c.lastrowid

def get_user_by_username(username):
    """Get user by username."""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """Get user by ID."""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def check_password(user, password):
    """Check if password matches user's password hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8'))
    except Exception:
        # Fallback for old password hashes
        from werkzeug.security import check_password_hash
        return check_password_hash(user['password_hash'], password)

def get_all_users(page=1, per_page=20):
    """Get all users with pagination."""
    conn = get_db()
    c = conn.cursor()
    offset = (page - 1) * per_page
    
    c.execute('SELECT COUNT(*) as total FROM users')
    total = c.fetchone()['total']
    
    c.execute('SELECT * FROM users ORDER BY id DESC LIMIT ? OFFSET ?', (per_page, offset))
    users = c.fetchall()
    
    conn.close()
    return users, total

# Building operations
def get_all_buildings():
    """Get all buildings."""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM buildings ORDER BY name')
    buildings = c.fetchall()
    conn.close()
    return buildings

def create_building(name, description=None):
    """Create a new building."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            'INSERT INTO buildings (name, description) VALUES (?, ?)',
            (name, description)
        )
        return c.lastrowid

# Room operations
def get_rooms_by_building(building_id):
    """Get all rooms in a building."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT r.*, b.name as building_name,
               (SELECT COUNT(*) FROM beds WHERE room_id = r.id AND is_occupied = 0) as available_beds
        FROM rooms r
        JOIN buildings b ON r.building_id = b.id
        WHERE r.building_id = ?
        ORDER BY r.room_number
    ''', (building_id,))
    rooms = c.fetchall()
    conn.close()
    return rooms

def get_available_rooms(room_type=None):
    """Get all available rooms, optionally filtered by type."""
    conn = get_db()
    c = conn.cursor()
    
    query = '''
        SELECT r.*, b.name as building_name,
               (SELECT COUNT(*) FROM beds WHERE room_id = r.id AND is_occupied = 0) as available_beds
        FROM rooms r
        JOIN buildings b ON r.building_id = b.id
        WHERE r.is_available = 1 AND r.current_occupancy < r.max_capacity
    '''
    
    if room_type:
        query += ' AND r.room_type = ?'
        c.execute(query + ' ORDER BY b.name, r.room_number', (room_type,))
    else:
        c.execute(query + ' ORDER BY b.name, r.room_number')
    
    rooms = c.fetchall()
    conn.close()
    return rooms

def create_room(building_id, room_number, room_type, max_capacity):
    """Create a new room with beds."""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Create room
        c.execute(
            'INSERT INTO rooms (building_id, room_number, room_type, max_capacity) VALUES (?, ?, ?, ?)',
            (building_id, room_number, room_type, max_capacity)
        )
        room_id = c.lastrowid
        
        # Create beds
        for i in range(1, max_capacity + 1):
            c.execute(
                'INSERT INTO beds (room_id, bed_number) VALUES (?, ?)',
                (room_id, str(i))
            )
        
        return room_id

def get_room_with_beds(room_id):
    """Get room details with bed information."""
    conn = get_db()
    c = conn.cursor()
    
    # Get room info
    c.execute('''
        SELECT r.*, b.name as building_name
        FROM rooms r
        JOIN buildings b ON r.building_id = b.id
        WHERE r.id = ?
    ''', (room_id,))
    room = c.fetchone()
    
    if room:
        # Get beds info
        c.execute('SELECT * FROM beds WHERE room_id = ? ORDER BY bed_number', (room_id,))
        beds = c.fetchall()
        room = dict(room)
        room['beds'] = [dict(bed) for bed in beds]
    
    conn.close()
    return room

# Lottery operations
def get_active_lottery():
    """Get the currently active lottery."""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM lottery_settings ORDER BY created_at DESC LIMIT 1')
    lottery = c.fetchone()
    conn.close()
    return lottery

def create_lottery(lottery_name, lottery_time, room_type):
    """Create a new lottery."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            'INSERT INTO lottery_settings (lottery_name, lottery_time, room_type) VALUES (?, ?, ?)',
            (lottery_name, lottery_time, room_type)
        )
        return c.lastrowid

def get_lottery_results(lottery_id):
    """Get all results for a lottery."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT lr.*, u.name as user_name, u.username
        FROM lottery_results lr
        JOIN users u ON lr.user_id = u.id
        WHERE lr.lottery_id = ?
        ORDER BY lr.lottery_number
    ''', (lottery_id,))
    results = c.fetchall()
    conn.close()
    return results

def save_lottery_result(user_id, lottery_id, lottery_number, group_number=None):
    """Save a lottery result."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            'INSERT OR REPLACE INTO lottery_results (user_id, lottery_id, lottery_number, group_number) VALUES (?, ?, ?, ?)',
            (user_id, lottery_id, lottery_number, group_number)
        )

def publish_lottery(lottery_id):
    """Publish lottery results."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('UPDATE lottery_settings SET is_published = 1 WHERE id = ?', (lottery_id,))

# Room selection operations
def get_user_room_selection(user_id):
    """Get user's room selection."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT rs.*, r.room_number, r.room_type, b.name as building_name, bd.bed_number
        FROM room_selections rs
        JOIN rooms r ON rs.room_id = r.id
        JOIN buildings b ON r.building_id = b.id
        JOIN beds bd ON rs.bed_id = bd.id
        WHERE rs.user_id = ?
    ''', (user_id,))
    selection = c.fetchone()
    conn.close()
    return selection

def select_room(user_id, room_id, bed_id):
    """Select a room and bed for a user."""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Check if bed is available
        c.execute('SELECT is_occupied FROM beds WHERE id = ?', (bed_id,))
        bed = c.fetchone()
        if not bed or bed['is_occupied']:
            raise ValueError('床位已被占用')
        
        # Delete any existing selection
        c.execute('DELETE FROM room_selections WHERE user_id = ?', (user_id,))
        
        # Create new selection
        c.execute(
            'INSERT INTO room_selections (user_id, room_id, bed_id) VALUES (?, ?, ?)',
            (user_id, room_id, bed_id)
        )
        
        # Mark bed as occupied
        c.execute('UPDATE beds SET is_occupied = 1 WHERE id = ?', (bed_id,))
        
        # Update room occupancy
        c.execute('''
            UPDATE rooms 
            SET current_occupancy = (SELECT COUNT(*) FROM beds WHERE room_id = ? AND is_occupied = 1)
            WHERE id = ?
        ''', (room_id, room_id))

def cancel_room_selection(user_id):
    """Cancel user's room selection."""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Get current selection
        c.execute('SELECT room_id, bed_id FROM room_selections WHERE user_id = ?', (user_id,))
        selection = c.fetchone()
        
        if selection:
            # Mark bed as available
            c.execute('UPDATE beds SET is_occupied = 0 WHERE id = ?', (selection['bed_id'],))
            
            # Delete selection
            c.execute('DELETE FROM room_selections WHERE user_id = ?', (user_id,))
            
            # Update room occupancy
            c.execute('''
                UPDATE rooms 
                SET current_occupancy = (SELECT COUNT(*) FROM beds WHERE room_id = ? AND is_occupied = 1)
                WHERE id = ?
            ''', (selection['room_id'], selection['room_id']))

# Room type allocation operations
def get_user_room_type(user_id):
    """Get user's allocated room type."""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT room_type FROM room_type_allocations WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result['room_type'] if result else None

def allocate_room_type(user_id, room_type, allocated_by=None, notes=None):
    """Allocate room type to a user."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            'INSERT OR REPLACE INTO room_type_allocations (user_id, room_type, allocated_by, notes) VALUES (?, ?, ?, ?)',
            (user_id, room_type, allocated_by, notes)
        )

def get_room_type_allocations():
    """Get all room type allocations."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT rta.*, u.name as user_name, u.username, 
               a.name as allocator_name
        FROM room_type_allocations rta
        JOIN users u ON rta.user_id = u.id
        LEFT JOIN users a ON rta.allocated_by = a.id
        ORDER BY rta.allocated_at DESC
    ''')
    allocations = c.fetchall()
    conn.close()
    return allocations

# Statistics operations
def get_room_statistics():
    """Get room allocation statistics."""
    conn = get_db()
    c = conn.cursor()
    
    stats = {}
    
    # Total rooms by type
    c.execute('''
        SELECT room_type, COUNT(*) as total,
               SUM(CASE WHEN is_available = 1 THEN 1 ELSE 0 END) as available,
               SUM(current_occupancy) as occupied_beds,
               SUM(max_capacity) as total_beds
        FROM rooms
        GROUP BY room_type
    ''')
    
    for row in c.fetchall():
        stats[f'room_type_{row["room_type"]}'] = dict(row)
    
    # Total users with room type allocation
    c.execute('SELECT COUNT(*) as total FROM room_type_allocations')
    stats['allocated_users'] = c.fetchone()['total']
    
    # Total users with room selection
    c.execute('SELECT COUNT(*) as total FROM room_selections')
    stats['selected_users'] = c.fetchone()['total']
    
    conn.close()
    return stats

# Initialize database when module is imported
if not os.path.exists(Config.DATABASE_NAME):
    init_db()