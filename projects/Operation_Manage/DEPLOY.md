# 安装部署指南

## 目录

- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Docker 部署](#docker-部署)
- [环境变量说明](#环境变量说明)
- [数据库迁移](#数据库迁移)
- [常见问题](#常见问题)

---

## 开发环境部署

### 1. 系统要求

| 依赖 | 版本 |
|------|------|
| Node.js | >= 22.0.0 |
| pnpm | >= 10.0.0 |
| Docker | >= 24.0.0 |
| Docker Compose | >= 2.20.0 |

### 2. 安装步骤

#### 2.1 克隆代码

```bash
git clone https://github.com/wudake/Operation_Manage.git
cd Operation_Manage
```

#### 2.2 启动 PostgreSQL 与 Redis

```bash
cd docker
docker-compose up -d
```

服务端口：
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

#### 2.3 安装项目依赖

```bash
pnpm install
```

#### 2.4 配置环境变量

```bash
cp apps/api/.env apps/api/.env.local
```

根据实际环境修改 `apps/api/.env.local` 中的配置，详见 [环境变量说明](#环境变量说明)。

#### 2.5 初始化数据库

```bash
# 生成 Prisma Client
pnpm db:generate

# 执行数据库迁移
pnpm db:migrate

# 导入种子数据（含默认管理员账号）
pnpm db:seed
```

#### 2.6 启动服务

```bash
# 同时启动前后端（推荐）
pnpm dev

# 后端: http://localhost:3000
# 前端: http://localhost:5173
```

---

## 生产环境部署

### 1. 构建前端

```bash
cd apps/web
pnpm build
```

构建产物位于 `apps/web/dist/`，可通过 Nginx 等静态服务器托管。

### 2. 构建后端

```bash
cd apps/api
pnpm build
```

构建产物位于 `apps/api/dist/`，使用 `node dist/main` 启动。

### 3. 生产环境 .env 配置

```bash
NODE_ENV=production
PORT=3000

# 数据库 — 使用生产环境 PostgreSQL
DATABASE_URL=postgresql://用户名:密码@生产数据库地址:5432/social_media_management?schema=public

# Redis — 使用生产环境 Redis
REDIS_HOST=生产Redis地址
REDIS_PORT=6379
REDIS_PASSWORD=生产Redis密码

# JWT — 生产环境务必更换强密钥
JWT_SECRET=生产环境强随机字符串
JWT_EXPIRES_IN=2h
JWT_REFRESH_EXPIRES_IN=7d
```

### 4. 使用 PM2 运行后端

```bash
cd apps/api
npm install -g pm2
pm2 start dist/main.js --name "smm-api"
pm2 save
pm2 startup
```

### 5. Nginx 反向代理配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态资源
    location / {
        root /path/to/apps/web/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:3000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Docker 部署

### 完整 Docker 部署（前后端 + 数据库）

在项目根目录创建 `docker-compose.prod.yml`：

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: smm
      POSTGRES_PASSWORD: 修改为你的强密码
      POSTGRES_DB: social_media_management
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - smm-network

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - smm-network

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      NODE_ENV: production
      PORT: 3000
      DATABASE_URL: postgresql://smm:修改为你的强密码@postgres:5432/social_media_management?schema=public
      REDIS_HOST: redis
      REDIS_PORT: 6379
      JWT_SECRET: 修改为你的强密钥
      JWT_EXPIRES_IN: 2h
      JWT_REFRESH_EXPIRES_IN: 7d
    depends_on:
      - postgres
      - redis
    networks:
      - smm-network

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    restart: unless-stopped
    depends_on:
      - api
    networks:
      - smm-network

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
      - api
    networks:
      - smm-network

volumes:
  postgres_data:
  redis_data:

networks:
  smm-network:
    driver: bridge
```

启动：

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 环境变量说明

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `NODE_ENV` | 是 | `development` | 运行环境 |
| `PORT` | 否 | `3000` | 后端服务端口 |
| `DATABASE_URL` | 是 | — | PostgreSQL 连接字符串 |
| `REDIS_HOST` | 是 | `localhost` | Redis 主机地址 |
| `REDIS_PORT` | 否 | `6379` | Redis 端口 |
| `REDIS_PASSWORD` | 否 | — | Redis 密码（无密码留空） |
| `JWT_SECRET` | 是 | — | JWT 签名密钥（生产必须更换） |
| `JWT_EXPIRES_IN` | 否 | `2h` | Access Token 有效期 |
| `JWT_REFRESH_EXPIRES_IN` | 否 | `7d` | Refresh Token 有效期 |

---

## 数据库迁移

### 新建迁移

```bash
cd apps/api
npx prisma migrate dev --name 迁移名称
```

### 生产环境部署迁移

```bash
cd apps/api
npx prisma migrate deploy
```

### 重新生成 Prisma Client

```bash
npx prisma generate
```

### 查看数据库（Prisma Studio）

```bash
npx prisma studio
```

---

## 常见问题

### Q: 前端启动后 API 请求失败？

确保后端已正常启动，且前端 `vite.config.ts` 中已配置代理：

```ts
server: {
  proxy: {
    '/api': 'http://localhost:3000'
  }
}
```

### Q: 数据库连接失败？

检查 `apps/api/.env` 中的 `DATABASE_URL` 是否与 Docker Compose 中配置的一致，确保 PostgreSQL 容器已正常启动。

### Q: 如何重置数据库？

```bash
cd docker
docker-compose down -v   # 删除数据卷
docker-compose up -d     # 重新启动
cd ../apps/api
npx prisma migrate dev
npx prisma db seed
```

### Q: 修改了 Prisma Schema 后如何生效？

```bash
pnpm db:generate
pnpm db:migrate
```

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-05-02 | 初始版本，包含账号管理、内容日历、选题库、用户权限等核心功能 |
