# Bio Clean Agent - Production Dockerfile
FROM python:3.11-slim

LABEL maintainer="Bio Clean Agent Team"
LABEL description="Intelligent AI-powered agent for cleaning biological and medical data"

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data
COPY examples ./examples

# 创建必要的目录
RUN mkdir -p /app/outputs /app/reports /app/uploads /app/logs

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .[all]

# 创建非root用户
RUN useradd -m -u 1000 bioagent && \
    chown -R bioagent:bioagent /app

# 切换到非root用户
USER bioagent

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV ALLOWED_ORIGINS=http://localhost:8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "-m", "uvicorn", "bio_clean_agent.web.app:app", "--host", "0.0.0.0", "--port", "8080"]
