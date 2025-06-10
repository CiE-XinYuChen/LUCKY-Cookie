"""
密钥管理器 - 确保JWT密钥在应用重启后保持一致
"""
import os
import secrets
import json
from pathlib import Path

class SecretKeyManager:
    def __init__(self, key_file='data/secret_keys.json'):
        self.key_file = Path(key_file)
        self.keys = self._load_keys()
    
    def _load_keys(self):
        """从文件加载密钥，如果文件不存在则创建新密钥"""
        if self.key_file.exists():
            try:
                with open(self.key_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # 生成新密钥
        keys = self._generate_keys()
        self._save_keys(keys)
        return keys
    
    def _generate_keys(self):
        """生成新的密钥"""
        return {
            'SECRET_KEY': secrets.token_urlsafe(32),
            'JWT_SECRET_KEY': secrets.token_urlsafe(32)
        }
    
    def _save_keys(self, keys):
        """保存密钥到文件"""
        # 确保目录存在
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.key_file, 'w') as f:
            json.dump(keys, f, indent=2)
        
        # 设置文件权限为仅所有者可读写
        os.chmod(self.key_file, 0o600)
    
    def get_secret_key(self):
        """获取Flask SECRET_KEY"""
        return self.keys.get('SECRET_KEY')
    
    def get_jwt_secret_key(self):
        """获取JWT_SECRET_KEY"""
        return self.keys.get('JWT_SECRET_KEY')
    
    def regenerate_keys(self):
        """重新生成密钥（慎用！会使所有现有token失效）"""
        self.keys = self._generate_keys()
        self._save_keys(self.keys)
        return self.keys

# 全局密钥管理器实例
key_manager = SecretKeyManager()