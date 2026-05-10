# 安装与部署指南

本文档介绍 Video Script Extractor 三种部署方式的完整流程：

1. [Docker Compose 部署](#一docker-compose-部署推荐) — 推荐，一行命令拉起全部服务
2. [本地开发环境](#二本地开发环境) — 直接跑源码，便于调试与二次开发
3. [生产部署](#三生产部署) — 加上 HTTPS、域名、反向代理与基本运维

后两节通用主题（环境变量、凭据、故障排查）见末尾参考章节。

---

## 一、Docker Compose 部署（推荐）

### 1.1 前置条件

| 软件 | 最低版本 | 说明 |
|------|----------|------|
| Docker          | 20.10+ | 安装见 [docs.docker.com](https://docs.docker.com/engine/install/) |
| Docker Compose  | v2     | Docker Desktop 自带；Linux 用 `docker compose` 子命令 |
| 可用磁盘        | ≥ 5 GB | 镜像 ~3 GB + Whisper 模型缓存 + 临时文件 |
| 内存            | ≥ 4 GB | 跑 `tiny`/`base` 模型；`large-v3` 建议 ≥ 8 GB |

### 1.2 配置环境变量

```bash
# 1. 后端 .env
cp .env.example .env
```

最少需要修改两项：

```dotenv
# 必改：团队共享的后端 API Key（与前端 Settings 页填写的需要一致）
API_KEY=please-change-me-to-a-strong-random-string

# 可选：使用 OpenAI Whisper API 引擎时必填
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

```bash
# 2. 前端登录凭据（构建时注入）
cp frontend/.env.example frontend/.env.local
```

编辑 `frontend/.env.local`：

```dotenv
VITE_ADMIN_USERNAME=admin
VITE_ADMIN_PASSWORD=ChooseAStrongPasswordHere
```

> 前端凭据是浏览器侧轻量门控，会被 Vite 在构建期内联到 JS bundle 中。**任何能拿到 bundle 的人都能读到密码**。请把它当作"防止陌生人误入"的栅栏，而不是真正的安全边界——真正的鉴权是后端 `API_KEY`。

### 1.3 启动全部服务

```bash
docker compose up -d --build
```

构建首次会比较慢（后端镜像需要安装 Playwright 的 Chromium 浏览器，约 5–10 分钟，取决于网速）。

### 1.4 检查服务状态

```bash
docker compose ps
docker compose logs -f backend     # 后端日志
docker compose logs -f worker      # Celery Worker 日志
```

### 1.5 访问

| 入口 | 地址 |
|------|------|
| 前端 Web UI       | <http://localhost:8080> |
| 后端 API 文档      | <http://localhost:8000/docs> |
| 后端健康检查       | <http://localhost:8000/health> |

首次进入会跳到 `/login`，使用第 1.2 步配置的用户名/密码登录。登录后到 **设置** 页填入与 `.env` 中一致的 `API_KEY`，然后即可在 **新建任务** 页提交链接。

### 1.6 停止与清理

```bash
docker compose stop          # 暂停（保留容器与卷）
docker compose down          # 停止并删除容器（保留卷）
docker compose down -v       # 连同 redis_data / whisper_models 卷一起删除
```

---

## 二、本地开发环境

适合需要调试代码、开发新功能的场景。需要分别启动 Redis、FastAPI、Celery Worker、前端开发服务器四个进程。

### 2.1 系统依赖

```bash
# Debian / Ubuntu
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip ffmpeg redis-server

# macOS (Homebrew)
brew install python@3.11 ffmpeg redis
```

| 依赖 | 用途 |
|------|------|
| Python 3.11+   | 后端运行时（`pydantic-settings`、`fastapi` 0.110+ 要求） |
| Node.js 20+    | 前端构建（Vite 8 要求 Node ≥ 20.19） |
| Redis 7+       | Celery broker + result backend + Pub/Sub |
| ffmpeg         | 音频提取 |
| Playwright Chromium | Ads Library 抽取（首次自动下载，约 130 MB） |

### 2.2 后端

```bash
cd /path/to/Facebook-Script-Extract

# 1. 创建虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 安装 Playwright 浏览器（仅在需要解析 Ads Library 时必须）
playwright install chromium

# 4. 配置 .env
cp .env.example .env
# 编辑 .env，至少修改 API_KEY；本地默认 REDIS_URL=redis://localhost:6379/0 即可

# 5. 启动 Redis（若未作为系统服务运行）
redis-server &

# 6. 启动后端 API（终端 A）
uvicorn api.main:app --reload --port 8000

# 7. 启动 Celery Worker（终端 B）
celery -A api.celery_app worker --loglevel=info --concurrency=2
```

> Worker 与后端共享同一个 `.env`，启动 Worker 时务必从项目根目录执行，否则 `api.tasks.worker` 中的相对路径会失效。

### 2.3 前端

```bash
cd frontend

# 1. 安装依赖
npm install

# 2. 配置登录凭据（构建期注入）
cp .env.example .env.local
# 编辑 .env.local，填入 VITE_ADMIN_USERNAME / VITE_ADMIN_PASSWORD

# 3. 启动 Vite 开发服务器（默认 http://localhost:5173）
npm run dev
```

`vite.config.ts` 已配置好 `/api` 与 `/ws` 代理到 `http://localhost:8000`，开发时无需关心跨域。

### 2.4 验证

1. 浏览器访问 <http://localhost:5173>
2. 用 `.env.local` 中的凭据登录
3. 进入 **设置** 页，填入与后端 `.env` 一致的 `API_KEY`
4. 回到 **新建任务**，粘贴一个 YouTube 短视频链接（比如 30 秒以内的 shorts），选 `本地 Whisper` + `tiny` 模型 + `cpu`
5. 提交后跳到任务详情页，能看到进度从 10% → 30% → 50% → 90% → 100%，完成后能下载脚本即说明三端贯通

### 2.5 测试

```bash
pytest                       # 跑全部测试
pytest tests/api/            # 只跑 API 路由测试
pytest -v --tb=long          # 详细输出
```

---

## 三、生产部署

### 3.1 推荐架构

```
Internet ──▶ Cloud LB / CDN ──▶ Caddy/Nginx (443, HTTPS)
                                    │
                                    ├── /         → frontend (8080)
                                    ├── /api/*    → backend  (8000)
                                    └── /ws/*     → backend  (8000)
```

`docker-compose.yml` 默认暴露 `8080`（前端）和 `8000`（后端）。生产环境建议：

1. 把 `backend` 的 `ports` 注释掉，只保留容器内通信，对外只暴露前端
2. 在前置反代（Caddy / Nginx / Traefik）上挂证书并把 80/443 转发到前端容器
3. 把 `API_KEY`、`OPENAI_API_KEY` 放进 secrets 管理（如 Docker Swarm secrets / `--env-file`），不要直接 commit

### 3.2 反向代理示例（Caddy）

```caddyfile
script.example.com {
    encode gzip

    # WebSocket 与 API 透传到 backend
    @api path /api/* /ws/*
    reverse_proxy @api backend:8000

    # 其余转发到前端
    reverse_proxy frontend:80
}
```

### 3.3 反向代理示例（Nginx）

```nginx
server {
    listen 443 ssl http2;
    server_name script.example.com;

    ssl_certificate     /etc/letsencrypt/live/script.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/script.example.com/privkey.pem;

    client_max_body_size 200m;

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 1800s;          # 长视频转写不要被切断
    }

    location /ws/ {
        proxy_pass http://backend:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
    }

    location / {
        proxy_pass http://frontend:80;
    }
}

server {
    listen 80;
    server_name script.example.com;
    return 301 https://$host$request_uri;
}
```

### 3.4 资源与并发

- Worker 并发数：在 `docker-compose.yml` 里调整 `--concurrency=2`。一个 Worker 进程同时只能跑一个本地 Whisper 推理（faster-whisper 内部已多线程）；CPU 模式建议并发 1–2。
- 任务超时：`api/celery_app.py` 中的 `task_time_limit = 3600`。处理 1 小时以上的视频建议提高到 7200 或更大。
- 模型缓存：`whisper_models` 卷会持久化已下载的 faster-whisper 权重，避免每次重建容器都重新下载。

### 3.5 GPU 加速（可选）

后端镜像已经能在 CUDA 环境下跑 `faster-whisper`。要启用 GPU：

1. 宿主机安装 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. 在 `docker-compose.yml` 的 `worker` 段添加：

   ```yaml
   worker:
     # ... 原有内容
     deploy:
       resources:
         reservations:
           devices:
             - driver: nvidia
               count: all
               capabilities: [gpu]
   ```

3. 提交任务时把 `device` 改成 `cuda`

不需要 GPU 时**不要**加上面的配置——非 NVIDIA 环境会启动失败。

### 3.6 数据持久化

| 卷 / 目录 | 内容 | 是否需要备份 |
|-----------|------|--------------|
| `redis_data`     | 任务元数据、Celery 队列  | 可选（任务历史，可重建） |
| `whisper_models` | 已下载的本地 Whisper 权重 | 否（可重新下载） |
| `./output`       | 脚本与原视频文件         | **建议定期备份** |
| `./temp`         | 下载/转码中间产物        | 否（任务成功后会自动清理） |

### 3.7 升级

```bash
git pull
docker compose pull               # 仅当使用了远端镜像
docker compose up -d --build      # 重新构建并平滑替换
docker compose logs -f backend
```

---

## 四、环境变量参考

### 4.1 后端 `.env`

| 变量 | 默认 | 必填 | 说明 |
|------|------|------|------|
| `API_KEY`               | `dev-api-key-change-me`   | ✅   | 团队共享的 API Key，前端 Settings 页填的就是它 |
| `OPENAI_API_KEY`        | —                          | 条件 | 使用 OpenAI 引擎时必填 |
| `REDIS_URL`             | `redis://localhost:6379/0` |      | Redis 连接地址 |
| `CELERY_BROKER_URL`     | 同 `REDIS_URL`             |      | Celery broker，可与 Redis 不同实例 |
| `CELERY_RESULT_BACKEND` | 同 `REDIS_URL`             |      | Celery 结果存储 |
| `TEMP_DIR`              | `./temp`                   |      | 下载/中间产物路径 |
| `OUTPUT_DIR`            | `./output`                 |      | 脚本/视频输出路径 |
| `RESULT_RETENTION_DAYS` | `7`                        |      | Redis 任务元数据 TTL |
| `DEBUG`                 | `false`                    |      | FastAPI 调试模式 |

### 4.2 前端 `frontend/.env.local`

| 变量 | 必填 | 说明 |
|------|------|------|
| `VITE_ADMIN_USERNAME` | ✅ | 登录用户名 |
| `VITE_ADMIN_PASSWORD` | ✅ | 登录密码 |
| `VITE_API_BASE_URL`   |    | 跨域部署时指向后端绝对地址（如 `https://api.example.com`），同域 Nginx 反代时留空 |

### 4.3 Docker Compose 变量

`docker-compose.yml` 通过 `${API_KEY:-...}` 形式读取，启动前确保它们在 shell 或 `.env` 中已设置。

---

## 五、凭据与安全

| 凭据 | 存放位置 | 谁需要 | 备注 |
|------|----------|--------|------|
| `API_KEY`              | 后端 `.env`、前端浏览器 localStorage | 后端、Worker、前端用户 | 团队共享，定期轮换 |
| `OPENAI_API_KEY`       | 后端 `.env`                          | 后端、Worker            | 可在 OpenAI Dashboard 单独建子 Key |
| 前端登录用户名/密码     | `frontend/.env.local`                | 前端构建机              | 构建期内联到 bundle，仅作门控 |

最佳实践：

- 生产环境的 `.env` 与 `frontend/.env.local` **不要 commit 到 git**（已在 `.gitignore` 中排除）
- `API_KEY` 至少 32 位随机串：`openssl rand -hex 32`
- 不同环境（dev / staging / prod）使用不同的 Key
- 通过反代加 IP 白名单或 Basic Auth，比单纯依赖前端登录更稳

---

## 六、验证安装

```bash
# 1. 健康检查
curl http://localhost:8000/health
# {"status":"ok"}

# 2. 创建一个任务（替换 API_KEY 与 url）
curl -X POST http://localhost:8000/tasks \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/shorts/<id>","language":"auto","output_format":"json","use_local":true,"model_size":"tiny"}'

# 3. 查询任务列表
curl -H "X-API-Key: $API_KEY" http://localhost:8000/tasks

# 4. WebSocket 监听（需要 wscat 或类似工具）
wscat -c "ws://localhost:8000/ws/tasks?api_key=$API_KEY"
```

---

## 七、故障排查

### 7.1 启动相关

| 现象 | 原因 / 排查 |
|------|-------------|
| `docker compose up` 卡在 `playwright install` | 镜像源慢，可设置 `PLAYWRIGHT_DOWNLOAD_HOST` 或预先在镜像层 cache |
| Worker 启动后立刻退出 | 通常是 `REDIS_URL` 不通；进容器 `redis-cli -h redis ping` 验证 |
| `frontend` 容器 502 | `backend` 没起来或没就绪；`docker compose logs backend` 看堆栈 |
| 前端打开后样式丢失 | Vite 构建未完成或 `frontend/dist` 没复制进镜像，重新 `--build` |

### 7.2 任务执行相关

| 现象 | 排查 |
|------|------|
| 提交后一直 `pending` | Worker 没起或没消费队列；`docker compose logs -f worker` |
| Ads Library 链接报"未提取到视频链接" | Playwright Chromium 没装好，或目标广告页已下架；进 backend 容器跑 `playwright install chromium` |
| `OPENAI_API_KEY` 报 401 | Key 失效或额度耗尽；切换到 `use_local=true` 应急 |
| `faster-whisper` 报 OOM | 模型太大或并发太多；降到 `small`/`base` 或减少 Worker `--concurrency` |
| 任务停在 `transcribing` 很久 | 大模型 + CPU 正常现象；30 分钟视频 + `large-v3` + CPU 可能 30 分钟以上 |
| 进度条不动但任务实际跑完 | WebSocket 被反代切断；检查 Nginx/Caddy 的 `Upgrade` 头与 `proxy_read_timeout` |

### 7.3 前端登录相关

| 现象 | 排查 |
|------|------|
| 登录页提示"用户名或密码错误"但确认填对了 | `.env.local` 改了但前端没重新 build。开发态 `npm run dev` 改了 `.env.local` 需要重启 dev server；Docker 部署需要 `docker compose up -d --build frontend` |
| 登录后调用接口 401 | **设置** 页的 `API_KEY` 与后端 `.env` 不一致 |
| 登录态 7 天前过期 | 重新登录即可；如需调整 TTL，修改 `frontend/src/utils/auth.ts` 的 `SESSION_DAYS` |

### 7.4 网络与代理

- 国内环境拉模型/Playwright 慢：在 Dockerfile 中加 `pip` 镜像、`playwright install --with-deps` 等
- 公司代理：在 `.env` 中放开 `HTTP_PROXY` / `HTTPS_PROXY`（已在 `.env.example` 中列出注释行）

### 7.5 日志位置

| 类型 | 位置 |
|------|------|
| Backend / Worker 容器日志       | `docker compose logs <service>` |
| 任务级错误日志                  | `output/<task_id>.error.log` |
| Celery 任务状态                 | `redis-cli -h redis HGETALL task_meta:<task_id>` |

---

## 八、参考

- 后端代码入口：`api/main.py`
- Worker 流水线：`api/tasks/worker.py`
- 前端登录态：`frontend/src/utils/auth.ts`
- 前端路由保护：`frontend/src/components/ProtectedRoute.tsx`
- 任务字段定义：`api/models/schemas.py`
- 自动接口文档：<http://localhost:8000/docs>（Swagger）/ <http://localhost:8000/redoc>
