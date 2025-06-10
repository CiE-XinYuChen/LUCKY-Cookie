# 生产环境部署指南

## JWT签名验证失败问题（最新更新）

### 问题原因
JWT "Signature verification failed" 错误通常由以下原因导致：
1. 应用重启后JWT密钥改变
2. 前后端使用了不同的密钥
3. Token在一个环境生成，在另一个环境验证

### 解决方案
系统现在使用持久化密钥管理器，确保密钥在应用重启后保持一致。

#### 密钥管理
```bash
# 查看当前密钥
python manage_keys.py show

# 重新生成密钥（会使所有token失效）
python manage_keys.py regenerate
```

#### 首次部署
```bash
# 系统会自动生成并保存密钥到 data/secret_keys.json
python app.py
```

#### 密钥优先级
1. 环境变量（如果设置）
2. 持久化密钥文件（data/secret_keys.json）
3. 自动生成新密钥（仅在文件不存在时）

## 权限验证失败问题解决方案

### 问题分析
远程服务器出现 403 权限验证失败错误，主要原因：
1. JWT Token 配置问题
2. CORS 跨域设置问题
3. 生产环境密钥配置问题

### 解决步骤

#### 1. 环境变量配置
复制 `.env.production` 文件并修改配置：

```bash
cp .env.production .env
```

修改 `.env` 文件中的关键配置：
```bash
# 必须修改的安全密钥
SECRET_KEY=your-unique-production-secret-key
JWT_SECRET_KEY=your-unique-jwt-secret-key

# 域名配置
CORS_ORIGINS=https://ybu.room.shaynechen.tech,http://ybu.room.shaynechen.tech
```

#### 2. 生成安全密钥
```python
# 生成安全密钥
import secrets
print("SECRET_KEY:", secrets.token_urlsafe(32))
print("JWT_SECRET_KEY:", secrets.token_urlsafe(32))
```

#### 3. 启动应用
```bash
# 设置环境变量
export FLASK_ENV=production
export SECRET_KEY="your-secret-key"
export JWT_SECRET_KEY="your-jwt-secret-key"

# 启动应用
python app.py
```

#### 4. 验证部署
访问管理后台测试：
- 登录页面：https://ybu.room.shaynechen.tech/login
- 使用管理员账户：admin / admin123
- 测试管理功能是否正常

### 常见问题解决

#### Q: 仍然出现 403 错误
A: 检查以下几点：
1. 确认 JWT_SECRET_KEY 在前后端保持一致
2. 检查 token 是否正确存储在 localStorage
3. 验证 CORS 配置是否包含正确的域名

#### Q: Token 过期问题
A: 
1. 检查 JWT_ACCESS_TOKEN_EXPIRES 设置
2. 前端需要处理 401 错误并重新登录
3. 考虑实现 token 刷新机制

#### Q: 网络请求失败
A:
1. 检查防火墙设置
2. 确认端口 32228 是否开放
3. 检查 nginx 代理配置（如果使用）

### 安全建议

1. **生产环境密钥**：绝不使用默认密钥
2. **HTTPS**：生产环境强制使用 HTTPS
3. **CORS**：限制具体域名，不使用 *
4. **日志**：启用详细日志监控
5. **备份**：定期备份数据库文件

### 监控和维护

```bash
# 查看应用日志
tail -f app.log

# 检查进程状态
ps aux | grep python

# 重启应用
pkill -f app.py
python app.py
```