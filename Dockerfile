# ── Stage 1: 构建前端 ──────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

# 客户端用空值（相对路径），服务端 SSR 通过 nginx 访问后端
ENV NEXT_PUBLIC_API_URL=""
ENV API_INTERNAL_URL="http://localhost:80"
RUN npm run build

# ── Stage 2: 安装 Python 依赖 ──────────────────────────────────────
FROM python:3.12-slim AS deps-installer

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /install
COPY requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 3: 最终镜像 ──────────────────────────────────────────────
FROM python:3.12-slim

# 安装 nginx、supervisor、Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制 Python 依赖
COPY --from=deps-installer /install /usr/local

# 复制后端代码
COPY main.py config.py database.py redis_client.py dependencies.py nginx.conf ./
COPY models/ ./models/
COPY schemas/ ./schemas/
COPY routers/ ./routers/
COPY services/ ./services/
COPY agent/ ./agent/
COPY rag/ ./rag/
COPY monitoring/ ./monitoring/
COPY cache/ ./cache/
COPY scripts/ ./scripts/

# 复制前端构建产物
COPY --from=frontend-builder /build/frontend/.next/standalone ./frontend/
COPY --from=frontend-builder /build/frontend/.next/static ./frontend/.next/static/
COPY frontend/public/ ./frontend/public/

# 复制 Nginx 和 Supervisor 配置
COPY nginx-docker.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 创建日志目录
RUN mkdir -p /var/log/nginx

EXPOSE 80

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
