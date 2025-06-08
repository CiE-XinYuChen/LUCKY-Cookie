FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建uploads目录
RUN mkdir -p uploads

# 设置权限
RUN chmod +x app.py

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]