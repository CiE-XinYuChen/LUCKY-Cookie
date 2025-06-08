-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 抽签设置表
CREATE TABLE lottery_settings (
    id SERIAL PRIMARY KEY,
    lottery_name VARCHAR(100) NOT NULL,
    lottery_time TIMESTAMP NOT NULL,
    is_published BOOLEAN DEFAULT FALSE,
    room_type VARCHAR(10) NOT NULL CHECK (room_type IN ('4', '8')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 宿舍楼表
CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 宿舍房间表
CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    building_id INTEGER REFERENCES buildings(id) ON DELETE CASCADE,
    room_number VARCHAR(20) NOT NULL,
    room_type VARCHAR(10) NOT NULL CHECK (room_type IN ('4', '8')),
    max_capacity INTEGER NOT NULL,
    current_occupancy INTEGER DEFAULT 0,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(building_id, room_number)
);

-- 床位表
CREATE TABLE beds (
    id SERIAL PRIMARY KEY,
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    bed_number VARCHAR(10) NOT NULL,
    is_occupied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(room_id, bed_number)
);

-- 抽签结果表
CREATE TABLE lottery_results (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    lottery_id INTEGER REFERENCES lottery_settings(id) ON DELETE CASCADE,
    lottery_number INTEGER NOT NULL,
    group_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, lottery_id)
);

-- 宿舍选择表
CREATE TABLE room_selections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    bed_id INTEGER REFERENCES beds(id) ON DELETE CASCADE,
    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_confirmed BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id),
    UNIQUE(bed_id)
);

-- 宿舍分配历史表
CREATE TABLE allocation_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
    bed_id INTEGER REFERENCES beds(id) ON DELETE CASCADE,
    action VARCHAR(20) NOT NULL CHECK (action IN ('assigned', 'removed', 'modified')),
    operated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    operated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- 创建索引优化查询性能
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_lottery_results_user_id ON lottery_results(user_id);
CREATE INDEX idx_lottery_results_lottery_id ON lottery_results(lottery_id);
CREATE INDEX idx_room_selections_user_id ON room_selections(user_id);
CREATE INDEX idx_room_selections_room_id ON room_selections(room_id);
CREATE INDEX idx_room_selections_bed_id ON room_selections(bed_id);
CREATE INDEX idx_beds_room_id ON beds(room_id);
CREATE INDEX idx_rooms_building_id ON rooms(building_id);

-- 插入默认管理员账户 (密码: admin123)
INSERT INTO users (username, password_hash, name, is_admin) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewGv93/hYxhFtdS6', '系统管理员', TRUE);

-- 插入测试数据
INSERT INTO buildings (name, description) VALUES 
('A栋', '学生宿舍A栋'),
('B栋', '学生宿舍B栋'),
('C栋', '学生宿舍C栋');

-- 插入测试房间和床位
INSERT INTO rooms (building_id, room_number, room_type, max_capacity) VALUES 
(1, '101', '4', 4),
(1, '102', '4', 4),
(1, '103', '8', 8),
(2, '201', '4', 4),
(2, '202', '8', 8);

-- 为每个房间插入床位
INSERT INTO beds (room_id, bed_number) VALUES 
-- 101房间（4人间）
(1, '1'), (1, '2'), (1, '3'), (1, '4'),
-- 102房间（4人间）
(2, '1'), (2, '2'), (2, '3'), (2, '4'),
-- 103房间（8人间）
(3, '1'), (3, '2'), (3, '3'), (3, '4'), (3, '5'), (3, '6'), (3, '7'), (3, '8'),
-- 201房间（4人间）
(4, '1'), (4, '2'), (4, '3'), (4, '4'),
-- 202房间（8人间）
(5, '1'), (5, '2'), (5, '3'), (5, '4'), (5, '5'), (5, '6'), (5, '7'), (5, '8');