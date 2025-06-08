# LUCKY Cookie - 宿舍抽签系统 🏠

<div align="center">

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-11+-blue.svg)
![Redis](https://img.shields.io/badge/Redis-5.0+-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**基于 Python Flask 的现代化宿舍分配系统**

支持公平抽签 • 实时选择 • 高并发处理 • Material Design

[在线演示](http://your-demo-site.com) • [功能特性](#功能特性) • [快速开始](#快速开始) • [部署指南](#部署指南)

</div>

## 📋 目录

- [功能特性](#功能特性)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [部署指南](#部署指南)
- [系统截图](#系统截图)
- [API文档](#api文档)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 🎯 功能特性

### 👥 用户管理
- ✅ 用户注册、登录、个人信息管理
- ✅ CSV文件批量导入用户（姓名、用户名、密码）
- ✅ 手动创建单个用户账户
- ✅ 用户密码自主修改和管理员重置
- ✅ 管理员权限管理和用户删除

### 🎲 抽签系统
- ✅ 创建抽签活动，设置公布时间
- ✅ 支持4人间/8人间不同宿舍类型
- ✅ 一键抽签功能，自动生成抽签结果
- ✅ 抽签结果预览，支持发布/删除操作
- ✅ 自动生成抽签号码，公平透明
- ✅ 分组管理，便于组织
- ✅ 管理员可修改抽签结果

### 🏠 宿舍管理
- ✅ 建筑、房间、床位三级管理
- ✅ 建筑管理：新增、删除（含安全检查）
- ✅ 房间管理：单个创建 + CSV批量导入
- ✅ 房间导入格式：building_name,room_number,room_type,max_capacity
- ✅ 实时显示宿舍占用情况
- ✅ 查看同宿舍室友信息
- ✅ 支持宿舍预览和选择

### 🎯 寝室类型分配系统（核心功能）
- ✅ 分离寝室类型分配和具体宿舍分配
- ✅ 学生先被分配寝室类型（4人间/8人间）
- ✅ 后台可修改学生的寝室类型分配
- ✅ 具体宿舍选择受寝室类型限制
- ✅ 双级管理：类型分配 → 具体房间分配
- ✅ 完整的分配历史记录

### ⚡ 高并发选择
- ✅ Redis分布式锁机制
- ✅ 防止多用户同时抢占同一床位
- ✅ 实时更新宿舍状态
- ✅ 优雅的错误处理和用户提示

### 🎨 现代化界面
- ✅ Material Design 设计规范
- ✅ 响应式布局，支持移动端
- ✅ 直观的操作流程
- ✅ 实时反馈和状态提示

### 🔒 安全特性
- ✅ JWT Token 认证
- ✅ bcrypt 密码加密
- ✅ SQL注入防护
- ✅ CORS安全策略
- ✅ 输入验证和过滤

## 🏗️ 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │    │   Flask API     │    │   数据存储      │
│                 │    │                 │    │                 │
│ • Material UI   │◄──►│ • 用户认证      │◄──►│ • PostgreSQL    │
│ • 响应式设计    │    │ • 抽签管理      │    │ • Redis缓存     │
│ • 实时更新      │    │ • 宿舍分配      │    │ • 分布式锁      │
│ • JavaScript    │    │ • 权限控制      │    │ • 数据持久化    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 核心组件
- **后端**: Flask + SQLAlchemy + JWT
- **数据库**: PostgreSQL (用户数据、宿舍信息)
- **缓存**: Redis (分布式锁、会话管理)
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **部署**: Docker + Docker Compose

## 🚀 快速开始

### 环境要求
- 🐍 Python 3.7+
- 🐘 PostgreSQL 11+
- 🔴 Redis 5.0+
- 🐳 Docker & Docker Compose (可选)

### 方式一：本地开发

#### 1. 克隆项目
```bash
git clone https://github.com/CiE-XinYuChen/LUCKY-Cookie.git
cd LUCKY-Cookie
```

#### 2. 创建虚拟环境
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量
```bash
# 复制配置文件
cp .env.example .env

# 编辑配置（重要！）
nano .env
```

`.env` 文件配置示例：
```bash
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost/dorm_lottery

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 安全密钥（生产环境请修改）
SECRET_KEY=your-very-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# 环境设置
FLASK_ENV=development
FLASK_DEBUG=True
```

#### 5. 初始化数据库
```bash
# 创建数据库
createdb dorm_lottery

# 导入数据结构和示例数据
psql -d dorm_lottery -f database/schema.sql
```

#### 6. 启动服务
```bash
# 使用启动脚本（推荐）
./run.sh

# 或者直接运行
python app.py
```

#### 7. 访问系统
- 🌐 访问地址: http://localhost:5000
- 👤 默认管理员: `admin` / `admin123`

### 方式二：Docker部署

#### 1. 克隆并启动
```bash
git clone https://github.com/CiE-XinYuChen/LUCKY-Cookie.git
cd LUCKY-Cookie

# 启动所有服务
docker-compose up -d
```

#### 2. 查看服务状态
```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f web
```

#### 3. 访问系统
- 🌐 访问地址: http://localhost:5000
- 👤 默认管理员: `admin` / `admin123`

## 🚀 部署指南

### 生产环境部署

#### 1. 服务器准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y python3 python3-pip python3-venv nginx postgresql redis-server git
```

#### 2. 数据库配置
```bash
# 创建数据库用户
sudo -u postgres createuser --interactive dorm_user

# 创建数据库
sudo -u postgres createdb -O dorm_user dorm_lottery

# 设置密码
sudo -u postgres psql -c "ALTER USER dorm_user PASSWORD 'your_password';"
```

#### 3. 项目部署
```bash
# 克隆项目
git clone https://github.com/CiE-XinYuChen/LUCKY-Cookie.git
cd LUCKY-Cookie

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 配置生产环境参数

# 初始化数据库
psql -d dorm_lottery -f database/schema.sql
```

#### 4. 配置系统服务
创建 `/etc/systemd/system/dorm-lottery.service`:
```ini
[Unit]
Description=Dorm Lottery System
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/LUCKY-Cookie
Environment=FLASK_ENV=production
ExecStart=/path/to/LUCKY-Cookie/venv/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### 5. 配置Nginx
创建 `/etc/nginx/sites-available/dorm-lottery`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 静态文件
    location /static/ {
        alias /path/to/LUCKY-Cookie/frontend/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 代理到Flask应用
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

#### 6. 启动服务
```bash
# 启用并启动服务
sudo systemctl enable dorm-lottery
sudo systemctl start dorm-lottery

# 配置Nginx
sudo ln -s /etc/nginx/sites-available/dorm-lottery /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 检查服务状态
sudo systemctl status dorm-lottery
```

### Docker生产部署

#### 1. 配置生产环境
编辑 `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/dorm_lottery
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=dorm_lottery
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### 2. 启动生产环境
```bash
# 设置环境变量
export DB_PASSWORD="your_secure_password"
export SECRET_KEY="your_very_secure_secret_key"
export JWT_SECRET_KEY="your_jwt_secret_key"

# 启动服务
docker-compose -f docker-compose.prod.yml up -d
```

## 📸 系统截图

### 用户界面
| 登录页面 | 个人中心 |
|:---:|:---:|
| ![登录页面](screenshots/login.png) | ![个人中心](screenshots/dashboard.png) |

| 宿舍选择 | 抽签结果 |
|:---:|:---:|
| ![宿舍选择](screenshots/room-selection.png) | ![抽签结果](screenshots/lottery.png) |

### 管理后台
| 用户管理 | 宿舍管理 |
|:---:|:---:|
| ![用户管理](screenshots/admin-users.png) | ![宿舍管理](screenshots/admin-rooms.png) |

## 📚 API文档

### 认证接口
| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| POST | `/api/auth/login` | 用户登录 | `username`, `password` |
| POST | `/api/auth/register` | 用户注册 | `username`, `password`, `name` |
| GET | `/api/auth/profile` | 获取用户信息 | - |
| POST | `/api/auth/change-password` | 修改密码 | `old_password`, `new_password` |

### 管理员接口
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/admin/users` | 获取用户列表 | 管理员 |
| POST | `/api/admin/users` | 创建单个用户 | 管理员 |
| POST | `/api/admin/users/import` | 批量导入用户 | 管理员 |
| DELETE | `/api/admin/users/{id}` | 删除用户 | 管理员 |
| PUT | `/api/admin/users/{id}/password` | 重置密码 | 管理员 |

### 建筑管理接口
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/admin/buildings` | 获取建筑列表 | 管理员 |
| POST | `/api/admin/buildings` | 创建建筑 | 管理员 |
| DELETE | `/api/admin/buildings/{id}` | 删除建筑 | 管理员 |

### 房间管理接口
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/admin/rooms` | 获取房间列表 | 管理员 |
| POST | `/api/admin/rooms` | 创建房间 | 管理员 |
| POST | `/api/admin/rooms/import` | 批量导入房间 | 管理员 |

### 寝室类型分配接口
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/admin/room-type-allocations` | 获取寝室类型分配 | 管理员 |
| POST | `/api/admin/room-type-allocations` | 创建寝室类型分配 | 管理员 |
| PUT | `/api/admin/room-type-allocations/{id}` | 修改寝室类型分配 | 管理员 |
| DELETE | `/api/admin/room-type-allocations/{id}` | 删除寝室类型分配 | 管理员 |
| GET | `/api/admin/unallocated-room-type-users` | 获取未分配寝室类型用户 | 管理员 |

### 抽签接口
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/lottery/settings` | 获取抽签设置 | 所有用户 |
| POST | `/api/lottery/settings` | 创建抽签 | 管理员 |
| POST | `/api/lottery/settings/{id}/publish` | 公布抽签 | 管理员 |
| GET | `/api/lottery/results` | 获取抽签结果 | 所有用户 |
| POST | `/api/admin/lottery/quick-draw` | 一键抽签 | 管理员 |
| POST | `/api/admin/lottery/{id}/publish` | 发布抽签结果 | 管理员 |
| DELETE | `/api/admin/lottery/{id}` | 删除抽签结果 | 管理员 |
| GET | `/api/admin/lottery/results` | 获取所有抽签结果 | 管理员 |

### 宿舍选择接口
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/lottery/rooms/available` | 获取可用房间 | 学生 |
| POST | `/api/room-selection/select` | 选择宿舍 | 学生 |
| POST | `/api/room-selection/cancel` | 取消选择 | 学生 |
| POST | `/api/room-selection/confirm` | 确认选择 | 学生 |

## 💾 数据管理

### 用户导入格式
CSV文件必须包含以下列：

```csv
name,username,password
张三,zhangsan,123456
李四,lisi,123456
王五,wangwu,123456
```

**字段说明：**
- `name`: 学生姓名（必填）
- `username`: 用户名，系统内唯一（必填）
- `password`: 密码，至少6位（必填）

### 房间导入格式
CSV文件必须包含以下列：

```csv
building_name,room_number,room_type,max_capacity
A栋,101,4,4
A栋,102,4,4
A栋,103,8,8
B栋,201,4,4
B栋,202,8,8
```

**字段说明：**
- `building_name`: 建筑名称，必须是已存在的建筑（必填）
- `room_number`: 房间号，在同一建筑内唯一（必填）
- `room_type`: 房间类型，只能是4或8（必填）
- `max_capacity`: 最大容量，必须在1-8之间（必填）

**注意事项：**
- 建筑必须在导入房间前先创建
- 系统会自动为每个房间创建对应数量的床位
- 重复的房间会被跳过

### 数据库结构
```sql
-- 主要表结构
users                   -- 用户表
lottery_settings        -- 抽签设置
buildings               -- 建筑表
rooms                   -- 房间表
beds                    -- 床位表
lottery_results         -- 抽签结果
room_type_allocations   -- 寝室类型分配（新增）
room_selections         -- 宿舍选择
allocation_history      -- 分配历史
```

### 系统流程
```mermaid
graph TD
    A[创建用户] --> B[分配寝室类型]
    B --> C[进行抽签]
    C --> D[发布抽签结果]
    D --> E[学生选择具体宿舍]
    E --> F[确认分配]
    
    B --> G[管理员手动分配寝室类型]
    G --> E
    
    C --> H[管理员修改抽签结果]
    H --> D
```

## 🛠️ 开发指南

### 本地开发环境
```bash
# 安装开发依赖
pip install -r requirements.txt

# 启动开发服务器
FLASK_ENV=development python app.py

# 运行测试
python -m pytest tests/

# 代码格式化
black backend/ frontend/
```

### 项目结构
```
LUCKY-Cookie/
├── 📁 backend/              # 后端代码
│   ├── 📄 app.py            # Flask应用工厂
│   ├── 📄 models.py         # 数据模型
│   ├── 📄 auth.py           # 认证模块
│   ├── 📄 admin.py          # 管理员功能
│   ├── 📄 lottery.py        # 抽签功能
│   ├── 📄 room_selection.py # 宿舍选择
│   └── 📄 redis_lock.py     # Redis锁机制
├── 📁 frontend/             # 前端代码
│   ├── 📁 templates/        # HTML模板
│   └── 📁 static/           # 静态资源
│       ├── 📁 css/         # 样式文件
│       └── 📁 js/          # JavaScript文件
├── 📁 database/             # 数据库文件
│   └── 📄 schema.sql       # 数据库结构
├── 📄 config.py            # 配置文件
├── 📄 requirements.txt     # Python依赖
├── 📄 app.py               # 应用入口
├── 📄 run.sh               # 启动脚本
├── 📄 docker-compose.yml   # Docker配置
└── 📄 README.md            # 项目文档
```

### 代码规范
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) Python代码规范
- 使用 Type Hints 提高代码可读性
- 编写单元测试和集成测试
- 添加适当的注释和文档字符串
- 使用有意义的变量和函数名

### 贡献流程
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## ❓ 常见问题

### 安装问题

**Q: 数据库连接失败怎么办？**
A: 请检查以下几点：
- PostgreSQL服务是否正在运行
- 数据库连接参数是否正确
- 数据库用户是否有足够权限
- 防火墙是否阻止了连接

**Q: Redis连接失败怎么办？**
A: 请检查：
- Redis服务是否启动 (`sudo systemctl status redis`)
- Redis配置是否正确
- 网络连接是否正常

### 使用问题

**Q: 忘记管理员密码怎么办？**
A: 可以通过数据库直接重置：
```sql
-- 重置admin用户密码为admin123
UPDATE users SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewGv93/hYxhFtdS6' WHERE username = 'admin';
```

**Q: 多个用户同时选择同一床位怎么办？**
A: 系统使用Redis分布式锁机制，确保同一时间只有一个用户能成功选择床位。其他用户会收到提示重新选择。

**Q: 如何备份数据？**
A: 使用PostgreSQL的pg_dump工具：
```bash
pg_dump dorm_lottery > backup.sql
```

### 性能优化

**Q: 系统响应慢怎么办？**
A: 可以考虑以下优化：
- 增加Redis内存
- 优化数据库查询
- 使用CDN加速静态资源
- 增加服务器配置

## 🔧 系统监控

### 健康检查
```bash
# 检查Web服务
curl http://localhost:5000/api/auth/verify-token

# 检查数据库连接
psql -d dorm_lottery -c "SELECT 1;"

# 检查Redis连接
redis-cli ping
```

### 日志管理
```bash
# 查看应用日志
sudo journalctl -u dorm-lottery -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 查看PostgreSQL日志
sudo tail -f /var/log/postgresql/postgresql-*.log
```

## 🤝 贡献指南

我们欢迎所有形式的贡献，包括但不限于：

- 🐛 报告Bug
- 💡 提出新功能建议
- 📖 完善文档
- 🔧 提交代码修复
- 🎨 改进界面设计

### 如何贡献
1. 查看 [Issues](https://github.com/CiE-XinYuChen/LUCKY-Cookie/issues) 了解当前需要帮助的内容
2. Fork 仓库并创建新分支
3. 进行开发并测试
4. 提交 Pull Request

### 开发环境设置
```bash
# 克隆你的fork
git clone https://github.com/your-username/LUCKY-Cookie.git
cd LUCKY-Cookie

# 添加上游仓库
git remote add upstream https://github.com/CiE-XinYuChen/LUCKY-Cookie.git

# 创建开发分支
git checkout -b feature/your-feature-name

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果有的话
```

## 📜 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

```
MIT License

Copyright (c) 2024 CiE-XinYuChen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 致谢

感谢以下开源项目和贡献者：

- [Flask](https://flask.palletsprojects.com/) - Python Web框架
- [PostgreSQL](https://www.postgresql.org/) - 数据库系统
- [Redis](https://redis.io/) - 内存数据库
- [Material Design](https://material.io/) - 设计系统
- 所有贡献者和用户的支持

## 📞 联系我们

- 🐛 报告问题: [GitHub Issues](https://github.com/CiE-XinYuChen/LUCKY-Cookie/issues)
- 💬 讨论: [GitHub Discussions](https://github.com/CiE-XinYuChen/LUCKY-Cookie/discussions)
- 📧 邮件: [your-email@example.com](mailto:your-email@example.com)

---

<div align="center">

**[⬆ 回到顶部](#lucky-cookie---宿舍抽签系统-)**

Made with ❤️ by [CiE-XinYuChen](https://github.com/CiE-XinYuChen)

如果这个项目对您有帮助，请考虑给我们一个 ⭐

</div>