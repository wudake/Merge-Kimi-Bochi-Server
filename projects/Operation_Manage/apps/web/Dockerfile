# ─────────────────────────────────────────────────────────────────────────────
# Operation_Manage Web Dockerfile
# ─────────────────────────────────────────────────────────────────────────────

FROM node:22-alpine AS builder

ARG VITE_BASE=/op/
ARG VITE_API_BASE_URL=/op/api/v1

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN VITE_BASE=${VITE_BASE} VITE_API_BASE_URL=${VITE_API_BASE_URL} npm run build

# ─── 生产镜像 ───
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# 覆盖默认配置,禁用默认 server,只提供静态文件
RUN echo 'server { listen 80; server_name localhost; root /usr/share/nginx/html; index index.html; location / { try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf
