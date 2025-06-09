# LUCKY Cookie - 宿舍抽签系统 🏠

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3.0+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Port](https://img.shields.io/badge/Port-32228-red.svg)

**基于 Python Flask 的现代化宿舍分配系统**

支持公平抽签 • 实时选择 • 高并发处理 • Material Design • 完全重构

[功能特性](#功能特性) • [快速开始](#快速开始) • [系统架构](#系统架构) • [部署指南](#部署指南)

</div>

## 📋 目录

- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [部署指南](#部署指南)
- [API文档](#api文档)
- [开发指南](#开发指南)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [许可证](#许可证)

## 🎯 功能特性

### 🔐 用户认证系统
- ✅ JWT Token 认证机制，安全可靠
- ✅ bcrypt 密码加密存储
- ✅ 用户注册、登录、密码修改
- ✅ 管理员权限分离和访问控制
- ✅ 会话管理和自动登出

### 👥 用户管理
- ✅ **CSV批量导入用户** - 支持姓名、用户名、密码批量导入
- ✅ **单个用户创建** - 手动创建学生和管理员账户
- ✅ **用户信息管理** - 查看、编辑、删除用户
- ✅ **密码重置功能** - 管理员可重置任意用户密码
- ✅ **用户状态统计** - 实时显示用户数量和分配状态

### 🏗️ 宿舍管理系统
- ✅ **三级管理架构** - 建筑 → 房间 → 床位
- ✅ **建筑管理** - 新增、删除建筑，安全检查关联房间
- ✅ **房间管理** - 支持4人间/8人间/自定义容量
- ✅ **CSV批量导入** - 房间信息批量导入和验证
- ✅ **床位自动生成** - 根据房间类型自动创建床位
- ✅ **实时占用状态** - 动态显示房间和床位占用情况

### 🎲 抽签系统
- ✅ **一键抽签功能** - 自动为所有用户生成抽签号码
- ✅ **寝室类型分配** - 先分配寝室类型（4人间/8人间）
- ✅ **抽签结果管理** - 发布、预览、删除抽签结果
- ✅ **结果修改功能** - 管理员可手动调整抽签结果
- ✅ **分配历史记录** - 完整的分配历史和操作日志

### 🏠 宿舍选择系统
- ✅ **智能筛选** - 按楼栋、房间类型筛选可用宿舍
- ✅ **实时更新** - 宿舍状态实时同步，防止冲突
- ✅ **室友信息预览** - 选择前查看当前室友信息
- ✅ **床位标注系统** - 8人间下铺标注，便于选择
- ✅ **选择确认机制** - 两步确认，防止误操作
- ✅ **选择历史** - 查看和管理选择历史

### 🎨 现代化界面设计
- ✅ **Material Design** - 遵循Material Design设计规范
- ✅ **响应式布局** - 完美适配桌面、平板、手机
- ✅ **无图标设计** - 极简设计，专注内容
- ✅ **动画效果** - 流畅的页面切换和交互动画
- ✅ **无障碍支持** - ARIA标签和键盘导航支持

### 💻 个人中心功能
- ✅ **状态概览** - 抽签状态、宿舍状态一目了然
- ✅ **个人信息** - 查看姓名、用户名等基本信息
- ✅ **抽签结果展示** - 抽签号码和分配结果
- ✅ **宿舍选择管理** - 当前选择状态和确认操作
- ✅ **密码修改** - 安全的密码更改功能

### 🔒 安全特性
- ✅ **输入验证** - 前后端双重数据验证
- ✅ **SQL注入防护** - 参数化查询防止注入
- ✅ **XSS防护** - HTML转义和内容安全策略
- ✅ **CSRF保护** - 跨站请求伪造防护
- ✅ **权限控制** - 细粒度的接口权限控制

### 📱 管理后台
- ✅ **统一管理界面** - 集中管理所有功能模块
- ✅ **数据统计面板** - 实时数据统计和图表展示
- ✅ **批量操作功能** - 支持批量导入、导出操作
- ✅ **操作日志** - 详细的管理操作记录
- ✅ **系统监控** - 用户活动和系统状态监控

### 🌐 用户体验优化
- ✅ **ICP备案信息** - 符合中国法律法规要求
- ✅ **错误处理机制** - 友好的错误提示和重试机制
- ✅ **加载状态** - 骨架屏和加载动画
- ✅ **操作反馈** - 实时操作结果反馈
- ✅ **自动刷新** - 关键数据自动更新

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端界面      │    │   Flask API     │    │   数据存储      │
│                 │    │                 │    │                 │
│ • Material UI   │◄──►│ • JWT认证       │◄──►│ • SQLite数据库  │
│ • 响应式设计    │    │ • 权限控制      │    │ • 文件存储      │
│ • 实时交互      │    │ • 业务逻辑      │    │ • 数据持久化    │
│ • 无障碍支持    │    │ • API接口       │    │ • 事务处理      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 技术栈
- **后端框架**: Flask 2.3+ + Flask-JWT-Extended
- **数据库**: SQLite 3.0+ (轻量级，易部署)
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **UI框架**: Material Design Components
- **部署**: Docker + Docker Compose
- **安全**: bcrypt + JWT + CORS

### 核心模块
```
backend/
├── app.py              # Flask应用工厂和配置
├── auth.py             # 用户认证和授权
├── admin.py            # 管理员功能模块
├── lottery.py          # 抽签系统核心逻辑
├── room_selection.py   # 宿舍选择功能
└── database.py         # 数据库操作封装

frontend/
├── templates/          # Jinja2模板文件
│   ├── base.html      # 基础模板
│   ├── index.html     # 主页
│   ├── login.html     # 登录页
│   ├── dashboard.html # 个人中心
│   ├── room_selection.html # 宿舍选择
│   └── admin.html     # 管理后台
└── static/
    ├── css/material.css # Material Design样式
    └── js/api.js       # API调用封装
```

## 🚀 快速开始

### 环境要求
- 🐍 **Python 3.9+** (推荐3.11+)
- 💾 **SQLite** (Python内置)
- 🐳 **Docker** (可选，用于容器化部署)
- 🌐 **现代浏览器** (Chrome 90+, Firefox 88+, Safari 14+)

### 一键启动 (推荐)

```bash
# 1. 克隆项目
git clone https://github.com/CiE-XinYuChen/LUCKY-Cookie.git
cd LUCKY-Cookie

# 2. 运行启动脚本
chmod +x run.sh
./run.sh

# 3. 访问系统
# 浏览器打开: http://localhost:32228
# 默认管理员: admin / admin123
```

### 手动安装步骤

#### 1. 项目下载
```bash
git clone https://github.com/CiE-XinYuChen/LUCKY-Cookie.git
cd LUCKY-Cookie
```

#### 2. 环境配置
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. 数据库初始化
```bash
# 创建数据库（自动执行）
python -c "
from backend.database import init_db
init_db()
print('数据库初始化完成!')
"
```

#### 4. 启动服务
```bash
# 开发环境启动
python app.py

# 生产环境启动
FLASK_ENV=production python app.py
```

#### 5. 访问系统
- 🌐 **访问地址**: http://localhost:32228
- 👤 **默认管理员**: `admin` / `admin123`
- 📱 **支持移动端**: 响应式设计，手机平板完美适配

## 🐳 Docker部署

### 快速部署
```bash
# 克隆项目
git clone https://github.com/CiE-XinYuChen/LUCKY-Cookie.git
cd LUCKY-Cookie

# 启动容器
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 自定义配置
编辑 `docker-compose.yml`:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "32228:32228"  # 自定义端口映射
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-secret-key
    volumes:
      - ./data:/app/data  # 数据持久化
    restart: unless-stopped
```

## 📚 API文档

### 认证接口
| 方法 | 路径 | 说明 | 参数 |
|------|------|------|------|
| `POST` | `/api/auth/login` | 用户登录 | `username`, `password` |
| `POST` | `/api/auth/register` | 用户注册 | `username`, `password`, `name` |
| `GET` | `/api/auth/profile` | 获取用户信息 | - |
| `POST` | `/api/auth/change-password` | 修改密码 | `old_password`, `new_password` |
| `GET` | `/api/auth/verify-token` | 验证Token | - |

### 管理员接口
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/api/admin/users` | 获取用户列表 | 管理员 |
| `POST` | `/api/admin/users` | 创建用户 | 管理员 |
| `POST` | `/api/admin/users/import` | 批量导入用户 | 管理员 |
| `DELETE` | `/api/admin/users/{id}` | 删除用户 | 管理员 |
| `PUT` | `/api/admin/users/{id}/password` | 重置密码 | 管理员 |

### 建筑管理接口
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/api/admin/buildings` | 获取建筑列表 | 管理员 |
| `POST` | `/api/admin/buildings` | 创建建筑 | 管理员 |
| `DELETE` | `/api/admin/buildings/{id}` | 删除建筑 | 管理员 |

### 房间管理接口
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/api/admin/rooms` | 获取房间列表 | 管理员 |
| `POST` | `/api/admin/rooms` | 创建房间 | 管理员 |
| `POST` | `/api/admin/rooms/import` | 批量导入房间 | 管理员 |
| `PUT` | `/api/admin/rooms/{id}` | 更新房间信息 | 管理员 |
| `DELETE` | `/api/admin/rooms/{id}` | 删除房间 | 管理员 |

### 抽签系统接口
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `POST` | `/api/admin/lottery/quick-draw` | 一键抽签 | 管理员 |
| `POST` | `/api/admin/lottery/{id}/publish` | 发布抽签结果 | 管理员 |
| `DELETE` | `/api/admin/lottery/{id}` | 删除抽签结果 | 管理员 |
| `GET` | `/api/lottery/results` | 获取个人抽签结果 | 学生 |

### 宿舍选择接口
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/api/lottery/buildings` | 获取可选楼栋 | 学生 |
| `GET` | `/api/lottery/rooms/available` | 获取可用房间 | 学生 |
| `POST` | `/api/room-selection/select` | 选择宿舍 | 学生 |
| `POST` | `/api/room-selection/confirm` | 确认选择 | 学生 |
| `POST` | `/api/room-selection/cancel` | 取消选择 | 学生 |
| `GET` | `/api/lottery/my-selection` | 获取我的选择 | 学生 |

## 🛠️ 开发指南

### 本地开发环境
```bash
# 克隆代码
git clone https://github.com/CiE-XinYuChen/LUCKY-Cookie.git
cd LUCKY-Cookie

# 安装开发依赖
pip install -r requirements.txt

# 设置开发环境变量
export FLASK_ENV=development
export FLASK_DEBUG=True

# 启动开发服务器
python app.py
```

### 项目结构说明
```
LUCKY-Cookie/
├── 📄 app.py                 # 应用程序入口
├── 📄 config.py              # 配置文件
├── 📄 run.sh                 # 启动脚本
├── 📄 requirements.txt       # Python依赖
├── 📄 Dockerfile            # Docker镜像构建
├── 📄 docker-compose.yml    # Docker Compose配置
├── 📁 backend/              # 后端核心代码
│   ├── 📄 __init__.py       # 包初始化
│   ├── 📄 app.py            # Flask应用工厂
│   ├── 📄 database.py       # 数据库操作
│   ├── 📄 auth.py           # 认证模块
│   ├── 📄 admin.py          # 管理功能
│   ├── 📄 lottery.py        # 抽签功能
│   └── 📄 room_selection.py # 宿舍选择
├── 📁 frontend/             # 前端代码
│   ├── 📁 templates/        # HTML模板
│   │   ├── 📄 base.html     # 基础模板
│   │   ├── 📄 index.html    # 主页
│   │   ├── 📄 login.html    # 登录页
│   │   ├── 📄 dashboard.html # 个人中心
│   │   ├── 📄 room_selection.html # 宿舍选择
│   │   └── 📄 admin.html    # 管理后台
│   └── 📁 static/           # 静态资源
│       ├── 📁 css/         # 样式文件
│       │   └── 📄 material.css # Material Design样式
│       └── 📁 js/          # JavaScript文件
│           └── 📄 api.js    # API调用封装
├── 📁 database/             # 数据库相关
│   ├── 📄 schema.sql       # 数据库结构
│   └── 📄 update_schema.sql # 结构更新
├── 📁 uploads/              # 文件上传目录
├── 📄 example_import_users.csv    # 用户导入示例
├── 📄 example_import_rooms.csv    # 房间导入示例
└── 📄 批量导入说明.md        # 导入功能说明
```

### 代码规范
- **Python代码**: 遵循 PEP 8 规范
- **JavaScript代码**: 使用 ES6+ 语法
- **HTML/CSS**: 语义化标签，BEM命名规范
- **API设计**: RESTful风格，统一错误码
- **数据库**: 合理的表结构设计和索引

### 测试指南
```bash
# 运行基础测试
python -c "
from backend.database import get_db
conn = get_db()
print('数据库连接正常' if conn else '数据库连接失败')
"

# 测试API接口
curl -X POST http://localhost:32228/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'
```

## ⚙️ 配置说明

### 环境变量配置
```bash
# 基础配置
FLASK_ENV=production          # 运行环境 (development/production)
FLASK_DEBUG=False            # 调试模式
SECRET_KEY=your-secret-key   # Flask密钥
JWT_SECRET_KEY=jwt-secret    # JWT密钥

# 数据库配置
DATABASE_PATH=data/app.db    # SQLite数据库文件路径

# 服务器配置
HOST=0.0.0.0                # 监听地址
PORT=32228                  # 监听端口

# 安全配置
JWT_ACCESS_TOKEN_EXPIRES=24  # JWT过期时间(小时)
UPLOAD_FOLDER=uploads        # 文件上传目录
MAX_CONTENT_LENGTH=16MB      # 最大上传文件大小
```

### 数据导入格式

#### 用户导入 CSV 格式
```csv
name,username,password
张三,zhangsan,123456
李四,lisi,123456
王五,wangwu,123456
```

#### 房间导入 CSV 格式
```csv
building_name,room_number,room_type,max_capacity
A栋,101,4,4
A栋,102,4,4
A栋,103,8,8
B栋,201,4,4
```

### 数据库结构
```sql
-- 核心表结构
CREATE TABLE users (               -- 用户表
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE buildings (           -- 建筑表
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rooms (               -- 房间表
    id INTEGER PRIMARY KEY,
    building_id INTEGER REFERENCES buildings(id),
    room_number TEXT NOT NULL,
    room_type INTEGER NOT NULL,
    max_capacity INTEGER NOT NULL,
    current_occupancy INTEGER DEFAULT 0,
    is_available BOOLEAN DEFAULT TRUE
);

CREATE TABLE beds (                -- 床位表
    id INTEGER PRIMARY KEY,
    room_id INTEGER REFERENCES rooms(id),
    bed_number INTEGER NOT NULL,
    is_occupied BOOLEAN DEFAULT FALSE
);

CREATE TABLE lottery_results (     -- 抽签结果表
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    lottery_number INTEGER NOT NULL,
    room_type INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE room_selections (     -- 宿舍选择表
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    bed_id INTEGER REFERENCES beds(id),
    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_confirmed BOOLEAN DEFAULT FALSE
);
```

## ❓ 常见问题

### 安装问题

**Q: 启动时提示端口被占用怎么办？**
```bash
# 查看端口占用
lsof -i :32228
# 或者
netstat -tulpn | grep 32228

# 终止占用进程
kill -9 <PID>

# 或者修改端口
export PORT=32229
python app.py
```

**Q: 数据库初始化失败怎么办？**
```bash
# 删除现有数据库文件
rm -f data/app.db

# 重新初始化
python -c "from backend.database import init_db; init_db()"
```

**Q: 依赖安装失败怎么办？**
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 或者使用conda
conda install --file requirements.txt
```

### 使用问题

**Q: 忘记管理员密码怎么办？**
```bash
# 重置管理员密码为admin123
python -c "
from backend.database import get_db
import bcrypt
conn = get_db()
password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, 'admin'))
conn.commit()
print('管理员密码已重置为: admin123')
"
```

**Q: CSV导入失败怎么办？**
- 检查CSV文件编码是否为UTF-8
- 确保列名与格式要求完全匹配
- 检查数据中是否有特殊字符
- 确保用户名不重复，房间号不重复

**Q: 用户无法选择宿舍怎么办？**
- 确认用户已有抽签结果
- 检查抽签结果是否已发布
- 确认有可用的对应类型房间
- 检查用户权限是否正常

### 性能优化

**Q: 系统响应慢怎么办？**
- 检查SQLite数据库文件大小
- 清理无用的历史数据
- 重启应用释放内存
- 考虑升级服务器配置

**Q: 并发用户多时出现错误怎么办？**
- SQLite支持的并发有限，考虑升级到PostgreSQL
- 增加应用实例使用负载均衡
- 优化数据库查询和索引

## 🔄 更新日志

### v2.0.0 (最新版本)
- 🎉 **完全重构个人中心页面** - 模块化架构，更好的错误处理
- 🏠 **新增主页宿舍选择入口** - 大型按钮，更便于访问
- 🔧 **修复楼栋筛选问题** - 用户现在可以正常看到楼栋选项
- 🎨 **移除所有SVG图标** - 极简设计，专注内容
- 🛡️ **添加ICP备案信息** - 符合中国法律法规要求
- 🔄 **更改服务端口为32228** - 避免常用端口冲突
- 🐛 **修复确认选择按钮失效** - 完善事件处理机制
- 📱 **优化移动端体验** - 响应式设计改进

### v1.0.0
- 🎯 初始版本发布
- ✅ 基础用户管理功能
- ✅ 抽签系统核心功能
- ✅ 宿舍管理系统
- ✅ 基础界面设计

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 贡献类型
- 🐛 **Bug报告** - 发现问题请提交Issue
- 💡 **功能建议** - 新功能想法和建议
- 📖 **文档改进** - 完善文档和注释
- 🔧 **代码贡献** - 修复Bug或添加功能
- 🎨 **界面设计** - UI/UX改进建议

### 贡献流程
1. Fork本仓库
2. 创建特性分支 `git checkout -b feature/AmazingFeature`
3. 提交更改 `git commit -m 'Add some AmazingFeature'`
4. 推送分支 `git push origin feature/AmazingFeature`
5. 创建Pull Request

### 开发环境设置
```bash
# Fork并克隆
git clone https://github.com/your-username/LUCKY-Cookie.git
cd LUCKY-Cookie

# 添加上游仓库
git remote add upstream https://github.com/CiE-XinYuChen/LUCKY-Cookie.git

# 创建开发分支
git checkout -b feature/your-feature

# 安装开发依赖
pip install -r requirements.txt

# 启动开发服务器
FLASK_ENV=development python app.py
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

感谢以下技术和项目的支持：

- [Flask](https://flask.palletsprojects.com/) - Python Web框架
- [SQLite](https://www.sqlite.org/) - 轻量级数据库
- [Material Design](https://material.io/) - 设计系统
- [JWT](https://jwt.io/) - 安全认证标准
- [bcrypt](https://github.com/pyca/bcrypt/) - 密码加密
- 所有贡献者和用户的支持与反馈

## 📞 联系我们

- 🐛 **问题报告**: [GitHub Issues](https://github.com/CiE-XinYuChen/LUCKY-Cookie/issues)
- 💬 **功能讨论**: [GitHub Discussions](https://github.com/CiE-XinYuChen/LUCKY-Cookie/discussions)
- 📧 **邮件联系**: [your-email@example.com](mailto:your-email@example.com)
- 🌟 **关注项目**: 点击右上角 ⭐ Star 支持我们

---

<div align="center">

**[⬆ 回到顶部](#lucky-cookie---宿舍抽签系统-)**

Made with ❤️ by [CiE-XinYuChen](https://github.com/CiE-XinYuChen)

**如果这个项目对您有帮助，请给我们一个 ⭐**

</div>