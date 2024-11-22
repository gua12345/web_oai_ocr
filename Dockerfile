# 使用更小的 Alpine 版本镜像
FROM python:3.9-alpine

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 文件
COPY requirements.txt .

# 安装系统依赖并清理缓存
RUN apk add --no-cache --virtual .build-deps gcc libc-dev libffi-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

# 复制应用文件
COPY . .

# 设置 Python 环境变量
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 54188

# 启动 Uvicorn 服务器
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "54188"]
