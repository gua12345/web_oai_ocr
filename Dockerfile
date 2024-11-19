# 第一个阶段：构建阶段
FROM python:3.11-slim AS build

# 安装构建所需的工具和库
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    python3-dev \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    curl \
    gnupg \
    ca-certificates \
    lsb-release \
    sudo \
    libssl-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件并安装依赖
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 第二个阶段：运行阶段
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 只复制必要的文件
COPY --from=build /app /app

ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 启动 FastAPI 应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
