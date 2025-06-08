-- 数据库架构更新脚本
-- 添加新的寝室类型分配表

-- 创建寝室类型分配表
CREATE TABLE IF NOT EXISTS room_type_allocations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    room_type VARCHAR(10) NOT NULL CHECK (room_type IN ('4', '8')),
    allocated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    UNIQUE(user_id)
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_room_type_allocations_user_id ON room_type_allocations(user_id);
CREATE INDEX IF NOT EXISTS idx_room_type_allocations_room_type ON room_type_allocations(room_type);
CREATE INDEX IF NOT EXISTS idx_room_type_allocations_allocated_by ON room_type_allocations(allocated_by);

-- 添加注释
COMMENT ON TABLE room_type_allocations IS '寝室类型分配表';
COMMENT ON COLUMN room_type_allocations.user_id IS '用户ID';
COMMENT ON COLUMN room_type_allocations.room_type IS '寝室类型：4人间或8人间';
COMMENT ON COLUMN room_type_allocations.allocated_by IS '分配操作员ID';
COMMENT ON COLUMN room_type_allocations.allocated_at IS '分配时间';
COMMENT ON COLUMN room_type_allocations.notes IS '备注信息';