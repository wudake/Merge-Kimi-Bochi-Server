# Video Script Extractor — Team Edition

视频音频转文字脚本提取工具的 **前后端分离团队版**。

输入 Facebook / YouTube / Facebook Ads Library 视频链接，自动完成视频下载、音频提取、语音识别，输出 TXT / SRT / VTT / JSON 四种格式的文字脚本。支持 **本地 Whisper（免费）** 与 **OpenAI Whisper API（付费）** 双引擎切换，并提供任务列表、实时进度、原视频下载、批量管理、已完成脚本汇总等团队协作能力。

---

## 功能概览

- **多平台视频源**
  - Facebook：`watch`、`share/v`、`share/r`、`fb.watch`、用户/页面 `videos`、`groups/posts` 链接
  - YouTube：`watch`、`shorts`、`youtu.be`、`embed`、`/v/` 链接
  - Facebook Ads Library：`facebook.com/ads/library/?id=...`（通过 Playwright 抓取广告 CDN 直链）
- **双转写引擎**
  - 本地 [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper)（CPU/CUDA，模型大小可选 tiny/base/small/medium/large-v3）
  - OpenAI Whisper API（`whisper-1`）
- **输出格式**：JSON（含分段+全文）、TXT（纯文本）、SRT、VTT
- **异步任务队列**：FastAPI 接收请求 → Celery Worker 处理 → Redis Pub/Sub 推送实时进度
- **WebSocket 实时进度**：前端订阅 `/ws/tasks` 自动更新任务状态与百分比
- **任务管理**：详情页、进度条、错误日志、原视频回看、字幕下载、单条删除、一键清空
- **已完成脚本聚合页**：所有完成任务的脚本全文滚动浏览，附一键复制
- **登录门控**：前端构建时注入用户名/密码，浏览器侧校验后写入 7 天本地会话
- **任务防重**：相同 URL 进行中的任务直接复用，不重复下载
- **结果保留**：Redis 元数据默认保留 7 天（`result_retention_days`）

---

## 架构

```
        ┌────────────┐
        │  Browser   │
        └─────┬──────┘
              │ HTTP / WebSocket
   ┌──────────▼───────────┐
   │  Nginx (前端容器)     │  端口 8080
   │  · 托管 React 静态资源 │
   │  · /api/* → backend   │
   │  · /ws/*  → backend   │
   └──────────┬───────────┘
              │
   ┌──────────▼───────────┐       ┌──────────────┐
   │  FastAPI (backend)   │◀─────▶│    Redis     │
   │  · /tasks  REST      │       │  · broker    │
   │  · /ws/tasks         │       │  · pub/sub   │
   │  · /health           │       │  · 元数据存储 │
   └──────────┬───────────┘       └──────┬───────┘
              │ Celery 任务派发                │
   ┌──────────▼───────────┐                  │
   │  Celery Worker       │◀─────────────────┘
   │  下载 → 提音频 → 转写 │
   │  · yt-dlp / Playwright│
   │  · ffmpeg             │
   │  · faster-whisper      │
   │  · OpenAI Whisper API  │
   └──────────────────────┘
```

---

## 快速上手

最快的方式是使用 Docker Compose，一行命令拉起所有服务。详细的环境要求、本地开发流程、生产部署步骤请参考 **[安装与部署指南](docs/INSTALL.md)**。

```bash
# 1. 配置后端环境变量
cp .env.example .env
# 编辑 .env：必填 API_KEY，使用 OpenAI 引擎再填 OPENAI_API_KEY

# 2. 配置前端登录凭据（构建时注入）
cp frontend/.env.example frontend/.env.local
# 编辑 frontend/.env.local：填入 VITE_ADMIN_USERNAME / VITE_ADMIN_PASSWORD

# 3. 启动全部服务
docker compose up -d --build

# 4. 访问
# 前端：http://localhost:8080
# 后端 API 文档：http://localhost:8000/docs
```

> 首次进入前端会跳转到 `/login`，使用 `frontend/.env.local` 中配置的用户名/密码登录。
> 登录后还需在 **设置** 页填入与后端 `.env` 中一致的 `API_KEY`，才能调用后端接口。

---

## 项目结构

```
Facebook-Script-Extract/
├── api/                          FastAPI 后端
│   ├── main.py                   应用入口（含 WebSocket 监听线程启动）
│   ├── celery_app.py             Celery 配置
│   ├── core/config.py            Pydantic Settings
│   ├── models/schemas.py         请求/响应模型
│   ├── routers/
│   │   ├── health.py             健康检查
│   │   ├── tasks.py              任务 REST + 下载
│   │   └── ws.py                 WebSocket + Redis 监听
│   └── tasks/worker.py           Celery 任务流水线
├── src/                          核心转写模块（CLI 与 Worker 共享）
│   ├── downloader.py             yt-dlp 下载（自动分流到 ads_extractor）
│   ├── ads_extractor.py          Playwright 抓取 Ads Library 视频直链
│   ├── audio_extractor.py        ffmpeg 提取音频
│   ├── transcriber.py            OpenAI Whisper API
│   ├── local_transcriber.py      本地 faster-whisper
│   ├── formatter.py              TXT/SRT/VTT/JSON 输出
│   └── utils.py                  URL 校验与 ID 提取
├── frontend/                     React + Vite 前端
│   ├── src/
│   │   ├── App.tsx               路由（含 ProtectedRoute）
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── SubmitPage.tsx
│   │   │   ├── TasksPage.tsx
│   │   │   ├── TaskDetailPage.tsx
│   │   │   ├── CompletedScriptsPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   ├── api/client.ts         Axios + 类型定义
│   │   ├── hooks/useWebSocket.ts
│   │   └── utils/
│   │       ├── auth.ts           登录态管理
│   │       └── validation.ts     URL 校验
│   ├── nginx.conf                生产 Nginx 配置
│   ├── Dockerfile                构建 + Nginx 多阶段镜像
│   └── .env.example              VITE_ADMIN_USERNAME/PASSWORD 模板
├── tests/                        pytest 测试
├── main.py                       CLI 入口（向后兼容）
├── Dockerfile                    后端镜像（含 ffmpeg + Playwright Chromium）
├── docker-compose.yml            redis / backend / worker / frontend
├── requirements.txt              Python 依赖
├── .env.example                  后端环境变量模板
└── docs/INSTALL.md               安装与部署指南
```

---

## API 接口

所有 `/tasks` 接口均需要在 Header 中带 `X-API-Key: <key>`，或通过查询参数 `?api_key=<key>`。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET    | `/health`                       | 健康检查 |
| POST   | `/tasks`                        | 创建转写任务（同 URL 进行中的任务会复用） |
| GET    | `/tasks?skip=&limit=`           | 任务列表（按完成时间倒序，未完成排最后） |
| GET    | `/tasks/{id}`                   | 任务详情 |
| GET    | `/tasks/{id}/result`            | 结构化结果（segments + full_text） |
| GET    | `/tasks/{id}/download`          | 下载脚本文件（原始格式） |
| GET    | `/tasks/{id}/download-video`    | 下载原始视频文件（mp4） |
| DELETE | `/tasks/{id}`                   | 删除任务（撤销 Celery 执行 + 清理 Redis + 删除文件） |
| DELETE | `/tasks`                        | 清空所有任务 |
| WS     | `/ws/tasks?api_key=<key>`       | 订阅实时进度 |

完整字段定义见 `api/models/schemas.py`，自动生成的接口文档：`http://localhost:8000/docs`。

### 任务请求示例

```bash
curl -X POST http://localhost:8000/tasks \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.facebook.com/watch/?v=1234567890",
    "language": "en",
    "output_format": "json",
    "use_local": true,
    "model_size": "tiny",
    "device": "cpu"
  }'
```

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `url`           | string | —      | Facebook / YouTube / Ads Library 链接 |
| `language`      | string | `en`   | `auto` / `zh` / `en` / `ja` / `ko` / `es` / `fr` 等 |
| `output_format` | enum   | `json` | `json` / `txt` / `srt` / `vtt` |
| `use_local`     | bool   | `true` | `true` 走本地 Whisper，`false` 走 OpenAI API |
| `model_size`    | enum   | `tiny` | `tiny` / `base` / `small` / `medium` / `large-v3`（仅本地） |
| `device`        | enum   | `cpu`  | `cpu` / `cuda`（仅本地） |

---

## CLI 用法

CLI 入口 `main.py` 与 Worker 共享 `src/` 模块，便于单机调试或脚本化：

```bash
# 本地 Whisper（免费）
python main.py "https://www.facebook.com/watch/?v=..." --local --model-size tiny --format srt -o ./output/result.srt

# OpenAI API
export OPENAI_API_KEY=sk-...
python main.py "https://youtu.be/..." --language auto --format json -o ./output/result.json
```

完整选项见 `python main.py --help`。

---

## 环境变量

### 后端 `.env`

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_KEY`               | `dev-api-key-change-me`     | 团队共享的后端 API Key（必改） |
| `OPENAI_API_KEY`        | —                            | 使用 OpenAI 引擎时必填 |
| `REDIS_URL`             | `redis://localhost:6379/0`  | Redis 连接 |
| `CELERY_BROKER_URL`     | 同上                         | Celery broker |
| `CELERY_RESULT_BACKEND` | 同上                         | Celery 结果存储 |
| `TEMP_DIR`              | `./temp`                    | 下载/中间产物目录 |
| `OUTPUT_DIR`            | `./output`                  | 脚本与视频输出目录 |
| `RESULT_RETENTION_DAYS` | `7`                         | Redis 任务元数据 TTL（天） |

### 前端 `frontend/.env.local`（构建时注入）

| 变量 | 说明 |
|------|------|
| `VITE_ADMIN_USERNAME` | 登录用户名 |
| `VITE_ADMIN_PASSWORD` | 登录密码 |
| `VITE_API_BASE_URL`   | 可选，跨域部署时指向后端地址（默认空，走同域 Nginx） |

> ⚠️ 前端凭据通过 Vite 在 **构建期** 内联到 JS bundle，仅用于轻量门控；**不是后端鉴权**。后端鉴权由 `API_KEY` 负责。

---

## 已知限制

- 单 API Key 共享认证，无多用户/角色隔离
- 任务元数据存 Redis，结果存文件系统；Redis 重启需开启持久化才能保留
- Ads Library 抽取依赖 Playwright，初次启动会拉取 Chromium（约 130 MB）
- 默认 `task_time_limit=3600s`，超长视频建议拆段或调高 `api/celery_app.py` 中的限制
- Worker GPU 支持：Dockerfile 与代码已兼容 CUDA，但 `docker-compose.yml` 未默认启用，需手动添加 `deploy.resources` 段并配合 NVIDIA Container Toolkit

---

## 文档

- **[安装与部署](docs/INSTALL.md)** — 本地开发、Docker 部署、生产部署、故障排查
- **[需求说明](requirements.md)** — 项目原始需求与设计
- **[开发进度记录](PROGRESS.md)** — 历史里程碑（仅作存档）

---

## License

MIT
