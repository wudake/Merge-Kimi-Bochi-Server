# 项目开发进度记录

> 记录时间：2026-04-25
> 项目：Video Script Extractor - Team Edition（前后端分离版）

---

## 一、项目概述

将原有的 CLI 工具改造为前后端分离的团队协作平台：
- **前端**：React + Vite + TailwindCSS 单页应用
- **后端**：FastAPI + Celery + Redis 异步任务队列
- **部署**：Docker Compose 一键部署（Nginx + 前端 + 后端 + Worker + Redis）

---

## 二、已完成模块

### 2.1 后端 API (`api/`)

| 文件 | 行数 | 状态 | 说明 |
|------|------|------|------|
| `api/main.py` | 45 | 完成 | FastAPI 入口，含 lifespan 启动 WebSocket 监听线程 |
| `api/celery_app.py` | 23 | 完成 | Celery 配置，Redis 作为 broker/backend |
| `api/core/config.py` | 41 | 完成 | Pydantic Settings，支持 .env |
| `api/models/schemas.py` | 69 | 完成 | 任务状态、输出格式、请求/响应模型 |
| `api/routers/health.py` | 8 | 完成 | 健康检查端点 |
| `api/routers/tasks.py` | 193 | 完成 | 任务 CRUD + 下载 + 结果查询 |
| `api/routers/ws.py` | 70 | 完成 | WebSocket 端点 + Redis Pub/Sub 监听线程 |
| `api/tasks/worker.py` | 190 | 完成 | Celery 任务：下载→提取音频→转写→保存 |

**已实现接口：**
- `POST /tasks` — 创建转写任务
- `GET /tasks` — 任务列表（分页）
- `GET /tasks/{id}` — 任务详情
- `GET /tasks/{id}/result` — 获取结果数据
- `GET /tasks/{id}/download` — 下载结果文件
- `WS /ws/tasks?api_key=xxx` — WebSocket 实时进度

**后端特性：**
- X-API-Key Header 认证
- CORS 全开
- Celery 任务自动重试（最多3次，指数退避）
- Redis Pub/Sub 实时进度推送
- 模型缓存复用（worker 进程内）
- 错误日志自动保存到 output/

### 2.2 核心模块 (`src/`)

| 文件 | 行数 | 状态 | 说明 |
|------|------|------|------|
| `src/downloader.py` | 27 | 完成 | yt-dlp 下载视频 |
| `src/audio_extractor.py` | 26 | 完成 | ffmpeg 提取音频 |
| `src/transcriber.py` | 38 | 完成 | OpenAI Whisper API 转写 |
| `src/local_transcriber.py` | 46 | 完成 | 本地 faster-whisper 转写 |
| `src/formatter.py` | 63 | 完成 | TXT/SRT/VTT/JSON 格式化输出 |
| `src/utils.py` | 38 | 完成 | Facebook URL 验证和 ID 提取 |

### 2.3 前端应用 (`frontend/`)

| 文件 | 行数 | 状态 | 说明 |
|------|------|------|------|
| `src/main.tsx` | 6 | 完成 | React 入口 |
| `src/App.tsx` | 21 | 完成 | React Router 路由配置 |
| `src/index.css` | 24 | 完成 | TailwindCSS + 自定义滚动条样式 |
| `src/api/client.ts` | 84 | 完成 | Axios 客户端 + 类型定义 + API 封装 |
| `src/hooks/useWebSocket.ts` | 38 | 完成 | WebSocket Hook，接收实时进度 |
| `src/components/Layout.tsx` | 56 | 完成 | 顶部导航栏 + 路由布局 |
| `src/pages/SubmitPage.tsx` | 191 | 完成 | 新建任务页面（URL/语言/格式/引擎选择） |
| `src/pages/TasksPage.tsx` | 146 | 完成 | 任务列表（实时进度条 + WebSocket 更新） |
| `src/pages/TaskDetailPage.tsx` | 174 | 完成 | 任务详情（进度/信息/文本预览/分段预览/下载） |
| `src/pages/SettingsPage.tsx` | 59 | 完成 | 设置页面（API Key 配置） |

**前端页面：**
- `/` — 新建任务：支持 Facebook 链接、语言选择、输出格式、本地/API 引擎切换
- `/tasks` — 任务列表：状态标签、实时进度条、刷新、下载
- `/tasks/:id` — 任务详情：完整进度、错误信息、文本/分段预览、下载按钮
- `/settings` — 设置：API Key 本地存储

**前端技术栈：**
- React 19 + TypeScript + Vite 8
- TailwindCSS v3 + PostCSS + Autoprefixer
- React Router DOM v7
- Axios（HTTP 客户端）
- Lucide React（图标）
- WebSocket API（原生，非 socket.io）

**前端开发代理配置：**
- `/api/*` → `http://localhost:8000`
- `/ws/*` → `ws://localhost:8000`

### 2.4 CLI 工具 (`main.py`)

| 文件 | 行数 | 状态 | 说明 |
|------|------|------|------|
| `main.py` | 87 | 完成 | 命令行入口，保留向后兼容 |

### 2.5 部署配置

| 文件 | 状态 | 说明 |
|------|------|------|
| `Dockerfile` | 完成 | 后端镜像（Python 3.11 + ffmpeg） |
| `frontend/Dockerfile` | 完成 | 前端镜像（Node 构建 + Nginx 托管） |
| `frontend/nginx.conf` | 完成 | Nginx 反向代理（/api、/ws 转发到后端） |
| `docker-compose.yml` | 完成 | 5 个服务：redis / backend / worker / frontend |
| `.dockerignore` | 完成 | 排除 node_modules、venv 等 |

### 2.6 文档

| 文件 | 状态 | 说明 |
|------|------|------|
| `README.md` | 完成 | 项目说明、快速开始、架构图、API 文档 |
| `requirements.md` | 已有 | 原始需求文档 |
| `.env.example` | 完成 | 环境变量模板 |

---

## 三、当前项目结构

```
Facebook-Script-Extract/
├── api/                          # FastAPI 后端
│   ├── __init__.py
│   ├── main.py                   # 应用入口 (45行)
│   ├── celery_app.py             # Celery 配置 (23行)
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py             # 配置管理 (41行)
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic 模型 (69行)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py             # 健康检查 (8行)
│   │   ├── tasks.py              # 任务路由 (193行)
│   │   └── ws.py                 # WebSocket (70行)
│   └── tasks/
│       ├── __init__.py
│       └── worker.py             # Celery Worker (190行)
├── frontend/                     # React 前端
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── index.html
│   ├── package.json              # 依赖已安装
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── vite.config.ts            # 含开发代理
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── api/
│       │   └── client.ts         # API 客户端
│       ├── components/
│       │   └── Layout.tsx        # 导航布局
│       ├── hooks/
│       │   └── useWebSocket.ts   # WebSocket Hook
│       └── pages/
│           ├── SubmitPage.tsx    # 新建任务
│           ├── TasksPage.tsx     # 任务列表
│           ├── TaskDetailPage.tsx # 任务详情
│           └── SettingsPage.tsx  # 设置
├── src/                          # 核心模块（前后端共享）
│   ├── __init__.py
│   ├── downloader.py             # yt-dlp 下载
│   ├── audio_extractor.py        # ffmpeg 提取音频
│   ├── transcriber.py            # OpenAI Whisper API
│   ├── local_transcriber.py      # 本地 faster-whisper
│   ├── formatter.py              # 输出格式化
│   └── utils.py                  # 工具函数
├── output/                       # 结果输出目录
├── temp/                         # 临时文件目录
├── main.py                       # CLI 入口 (87行)
├── requirements.txt              # Python 依赖
├── requirements.md               # 需求文档
├── docker-compose.yml            # Docker 编排
├── Dockerfile                    # 后端镜像
├── .dockerignore
├── .env.example                  # 环境变量模板
├── README.md                     # 项目文档
└── PROGRESS.md                   # ← 本文件
```

---

## 四、构建与运行状态

### 4.1 前端构建
- 状态：通过
- 输出：`frontend/dist/`（index.html + CSS + JS）
- 已知问题：Tailwind CSS 已降级到 v3（v4 与 PostCSS 集成方式变更）

### 4.2 后端运行
- 本地开发：`uvicorn api.main:app --reload --port 8000`
- Celery Worker：`celery -A api.celery_app worker --loglevel=info`
- 需要 Redis：`redis-server`

### 4.3 Docker 部署
- 命令：`docker-compose up -d`
- 访问：前端 `http://localhost`，API `http://localhost:8000`

---

## 五、待办事项 / 明天可继续的方向

### 5.1 高优先级

1. **用户系统**
   - 当前：单 API Key 共享认证
   - 目标：多用户登录（JWT + 用户表），任务归属到用户
   - 影响文件：`api/core/config.py`（添加用户模型）、`api/routers/`（添加 auth 路由）、前端登录页

2. **测试**
   - 当前：无任何测试
   - 目标：后端单元测试（pytest）、前端组件测试（Vitest）
   - 需创建：`tests/`、`frontend/src/**/*.test.tsx`

3. **任务队列监控**
   - 当前：仅通过 API 查询任务状态
   - 目标：集成 Flower（Celery 监控面板）到 docker-compose

### 5.2 中优先级

4. **批量提交**
   - 当前：仅支持单链接提交
   - 目标：支持上传 txt/csv 文件批量提交多个链接
   - 影响文件：`api/routers/tasks.py`（批量创建接口）、`frontend/src/pages/SubmitPage.tsx`

5. **结果持久化**
   - 当前：结果保存在文件系统，Redis 元数据 7 天后过期
   - 目标：PostgreSQL/SQLite 数据库存储任务和结果
   - 影响文件：`api/models/`（SQLAlchemy 模型）、`docker-compose.yml`

6. **说话人分离（Diarization）**
   - 当前：已实现语音转写，无说话人分离
   - 目标：集成 pyannote.audio，在 JSON 输出中区分 speaker
   - 影响文件：`src/diarization.py`（新模块）、`api/tasks/worker.py`

7. **文本摘要**
   - 当前：仅输出原文
   - 目标：基于 LLM 自动生成视频内容摘要
   - 影响文件：`api/tasks/worker.py`（添加摘要步骤）、前端详情页

### 5.3 低优先级 / 优化项

8. **前端优化**
   - 添加暗黑模式
   - 拖拽上传视频文件（不仅 URL）
   - 响应式移动端适配
   - 任务搜索/筛选
   - 分页组件（当前仅展示前50条）

9. **后端优化**
   - 添加 API 限流（Rate Limiting）
   - 文件上传大小限制
   - 更细粒度的进度（当前仅 10/30/50/90/100）
   - 任务取消功能

10. **运维**
    - 添加 Prometheus/Grafana 监控
    - 日志收集（ELK / Loki）
    - 自动清理过期文件（当前仅 Redis 过期）

---

## 六、已知问题

| 问题 | 严重程度 | 说明 |
|------|----------|------|
| 前端 `socket.io-client` 已安装但未使用 | 低 | 前端使用原生 WebSocket API，`socket.io-client` 是冗余依赖 |
| Worker GPU 配置需要 NVIDIA Docker | 低 | docker-compose.yml 中配置了 `deploy.resources.reservations.devices`，非 NVIDIA 环境启动会报错，需注释掉 |
| 无数据库 | 中 | 任务元数据存 Redis，结果存文件系统，重启后数据依赖 Redis 持久化 |
| 单点 API Key | 中 | 团队共享一个 Key，无用户隔离 |

---

## 七、环境要求

### 开发环境
- Python 3.11+
- Node.js 20+
- Redis 7+
- ffmpeg（系统依赖）

### 生产环境（Docker）
- Docker + Docker Compose
- 可选：NVIDIA Docker Runtime（用于 GPU 加速）

### 环境变量（`.env`）
```
API_KEY=dev-api-key-change-me
OPENAI_API_KEY=sk-xxx
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
TEMP_DIR=./temp
OUTPUT_DIR=./output
```

---

## 八、快速恢复开发

### 明天继续前端开发
```bash
cd /root/Facebook-Script-Extract/frontend
npm run dev
# 访问 http://localhost:5173
```

### 明天继续后端开发
```bash
cd /root/Facebook-Script-Extract
# 终端1：启动 Redis
redis-server

# 终端2：启动 FastAPI
uvicorn api.main:app --reload --port 8000

# 终端3：启动 Celery Worker
celery -A api.celery_app worker --loglevel=info --concurrency=2
```

### 明天继续 Docker 部署
```bash
cd /root/Facebook-Script-Extract
docker-compose up -d --build
```

---

*本文件由 Claude 于 2026-04-25 自动生成，用于记录项目快照。*
