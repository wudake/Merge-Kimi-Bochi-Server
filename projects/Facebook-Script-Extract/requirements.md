# Video Script Extractor - 项目需求文档

> 版本：v2.0（前后端分离团队版）
> 更新日期：2026-04-26

---

## 1. 项目概述

### 1.1 项目名称
Video Script Extractor —— Facebook 视频脚本提取器（团队版）

### 1.2 项目背景
用户经常需要在 Facebook 上观看视频内容（如课程、讲座、访谈、新闻等），但视频形式不利于快速浏览、检索和存档。本项目旨在通过自动化流程，将 Facebook 视频中的音频内容提取并转换为可编辑、可搜索的文字脚本，并通过 Web 界面和 API 为团队提供协作能力。

### 1.3 项目目标
提供一个稳定、高效、可部署的服务，能够将任意公开的 Facebook 视频链接转换为结构化的文字脚本，支持：
- 多种输出格式（TXT、SRT、VTT、JSON）
- 双引擎语音识别（本地 Whisper / OpenAI Whisper API）
- 实时进度推送与任务管理
- 前后端分离的 Web 界面
- Docker Compose 一键部署

---

## 2. 功能需求

### 2.1 核心功能

| 功能模块 | 需求描述 | 状态 | 优先级 |
|---------|---------|------|--------|
| **链接解析** | 支持标准 Facebook 视频链接（`facebook.com/watch?v=`、`facebook.com/share/v/`、`fb.watch` 短链、群组/主页视频链接、Reels 分享链接） | 已实现 | P0 |
| **视频下载** | 使用 yt-dlp 自动下载公开 Facebook 视频到本地临时存储 | 已实现 | P0 |
| **音频提取** | 使用 ffmpeg 从视频文件中提取 MP3 音频轨道 | 已实现 | P0 |
| **语音识别** | 支持中英文及多语言识别，双引擎切换 | 已实现 | P0 |
| **时间轴对齐** | 输出带时间戳的分段结果（JSON 含 start/end，SRT/VTT 含时间码） | 已实现 | P1 |
| **结果导出** | 支持 TXT、SRT、VTT、JSON 四种格式导出 | 已实现 | P1 |
| **任务队列** | 基于 Celery + Redis 的异步任务处理，支持并发 | 已实现 | P1 |
| **Web 界面** | React 前端：新建任务、任务列表、详情查看、结果下载、已完成脚本浏览 | 已实现 | P1 |
| **实时进度** | WebSocket 推送任务状态与进度百分比 | 已实现 | P1 |
| **API 服务** | FastAPI 提供 RESTful API，含认证、任务 CRUD、结果查询与下载 | 已实现 | P1 |
| **CLI 工具** | 保留命令行入口，支持单链接直接处理 | 已实现 | P2 |
| **防重提交** | 同一 URL 已有进行中的任务时，直接返回现有任务 | 已实现 | P2 |
| **模型缓存** | Worker 进程内复用已加载的 Whisper 模型，减少重复加载开销 | 已实现 | P2 |
| **错误日志** | 任务失败时自动保存错误日志到 output 目录 | 已实现 | P2 |
| **任务重试** | Celery 自动重试（最多 3 次，指数退避 30 秒起） | 已实现 | P2 |

### 2.2 输入规格

- **支持链接格式**：
  - `https://www.facebook.com/watch?v={video_id}`
  - `https://www.facebook.com/share/v/{share_code}/`
  - `https://www.facebook.com/share/r/{share_code}/`（Reels）
  - `https://fb.watch/{short_code}`
  - `https://www.facebook.com/{page_name}/videos/{video_id}`
  - `https://www.facebook.com/groups/{group_id}/posts/{post_id}`
- **视频可见性**：仅限公开（Public）视频
- **视频时长限制**：Celery 任务硬限制 1 小时（`task_time_limit=3600`）
- **文件大小限制**：依赖 yt-dlp 和系统磁盘空间

### 2.3 输出规格

- **纯文本（TXT）**：仅包含转写全文
- **字幕格式（SRT）**：包含序号、时间码（`HH:MM:SS,mmm --> HH:MM:SS,mmm`）、文字内容
- **字幕格式（VTT）**：WebVTT 标准格式
- **结构化 JSON**：
  ```json
  {
    "language": "zh",
    "duration": 120.5,
    "segments": [
      {
        "id": 0,
        "start": 0.0,
        "end": 5.2,
        "text": "大家好，欢迎来到今天的分享。"
      }
    ],
    "full_text": "大家好，欢迎来到今天的分享。..."
  }
  ```

### 2.4 语音识别引擎

| 引擎 | 模型选项 | 设备选项 | 特点 | 适用场景 |
|------|---------|---------|------|---------|
| **本地 Whisper** | tiny / base / small / medium / large-v3 | cpu / cuda | 免费、隐私好、首次需下载模型 | 常规使用、长视频、隐私敏感 |
| **OpenAI Whisper API** | whisper-1 | OpenAI 云端 | 准确度高、按量计费、无需本地 GPU | 追求最高准确度、短视频 |

本地模式默认参数：
- `condition_on_previous_text=True`：利用上下文提升连贯性
- `vad_filter=True`：启用语音活动检测，过滤无语音段落

### 2.5 前端页面

| 页面 | 路径 | 功能描述 |
|------|------|---------|
| 新建任务 | `/` | 输入 Facebook 链接，选择语言、输出格式、转写引擎、模型大小、推理设备 |
| 任务列表 | `/tasks` | 展示所有任务，含状态标签、实时进度条、创建时间、下载/详情操作 |
| 任务详情 | `/tasks/:id` | 完整进度、基本信息、错误信息、文本预览、分段预览（含时间轴）、下载按钮 |
| 已完成脚本 | `/completed` | 汇总展示所有已完成任务的脚本全文，支持快速浏览 |
| 设置 | `/settings` | 配置 API Key（本地存储于浏览器） |

---

## 3. 非功能需求

### 3.1 性能要求

- 视频下载+音频提取：取决于视频大小和网络带宽
- 语音识别速度：本地模式取决于模型大小和设备（CPU/GPU）
- 并发支持：Celery Worker 可通过 `--concurrency` 调整并行数
- 实时推送：WebSocket + Redis Pub/Sub，延迟 < 1 秒

### 3.2 可靠性

- 任务失败自动重试（最多 3 次，指数退避）
- 错误日志自动保存到 `output/{task_id}.error.log`
- 临时文件任务完成后自动清理
- Redis 任务元数据保留 7 天（可配置 `result_retention_days`）

### 3.3 安全与合规

- **认证**：X-API-Key Header 认证，团队共享单一 API Key
- **隐私**：不长期存储原始视频文件，仅保留转写结果
- **版权**：仅处理公开视频
- **API 密钥**：OpenAI API Key 通过环境变量配置，不硬编码

### 3.4 易用性

- 提供 Web 界面、REST API、CLI 三种使用方式
- 前端使用 TailwindCSS，界面清晰、响应式布局
- 处理进度实时反馈（进度条 + WebSocket）
- 清晰的错误提示（链接无效、下载失败、识别失败等）

---

## 4. 技术方案

### 4.1 技术栈

| 环节 | 技术方案 | 版本/说明 |
|-----|---------|----------|
| 视频下载 | `yt-dlp` | Python 包，支持 Facebook 等多种平台 |
| 音频提取 | `ffmpeg` | 系统依赖，提取 MP3 音频 |
| 本地语音识别 | `faster-whisper` | 基于 CTranslate2 的高效 Whisper 实现 |
| API 语音识别 | OpenAI Whisper API | `whisper-1` 模型 |
| 后端框架 | `FastAPI` | Python 异步 Web 框架 |
| 任务队列 | `Celery` + `Redis` | 异步任务处理与结果存储 |
| 前端框架 | `React` + `Vite` + `TypeScript` | React 19 + Vite 8 + TypeScript 6 |
| 前端样式 | `TailwindCSS` v3 + `PostCSS` | 实用工具类 CSS |
| 前端路由 | `React Router DOM` v7 | 单页应用路由 |
| HTTP 客户端 | `Axios` | 前端 API 请求 |
| 图标库 | `Lucide React` | 矢量图标 |
| 实时通信 | 原生 `WebSocket` API + Redis Pub/Sub | 非 socket.io |
| 配置管理 | `Pydantic Settings` | 支持 `.env` 环境变量 |
| 部署 | `Docker` + `Docker Compose` | 多服务编排 |
| 反向代理 | `Nginx` | 前端静态资源 + API/WebSocket 反向代理 |

### 4.2 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│   React     │     │   Redis     │
│  (80端口)   │     │   前端      │     │  任务队列   │
└──────┬──────┘     └─────────────┘     └──────┬──────┘
       │                                         │
       │  /api/* 反向代理                        │
       │  /ws/*  WebSocket                       │
       ▼                                         │
┌─────────────┐     ┌─────────────┐             │
│   FastAPI   │◀────│   Celery    │─────────────┘
│   后端 API  │     │   Worker    │
└─────────────┘     └─────────────┘
```

**Docker Compose 服务组成**：
- `redis`：Redis 7 Alpine，任务队列 broker 与 backend
- `backend`：FastAPI 应用，提供 REST API 与 WebSocket
- `worker`：Celery Worker，执行实际下载/提取/转写任务
- `frontend`：Nginx 托管的 React 构建产物

### 4.3 目录结构

```
Facebook-Script-Extract/
├── api/                          # FastAPI 后端
│   ├── __init__.py
│   ├── main.py                   # FastAPI 入口，含 lifespan 启动 WebSocket 监听
│   ├── celery_app.py             # Celery 配置
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py             # Pydantic Settings 配置管理
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic 数据模型（任务、请求、响应）
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py             # 健康检查
│   │   ├── tasks.py              # 任务 CRUD + 结果下载
│   │   └── ws.py                 # WebSocket 端点 + Redis Pub/Sub 监听
│   └── tasks/
│       ├── __init__.py
│       └── worker.py             # Celery 任务：下载→提取音频→转写→保存
├── frontend/                     # React + Vite 前端
│   ├── Dockerfile
│   ├── nginx.conf                # Nginx 反向代理配置
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts            # Vite 配置（含开发代理）
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx              # React 入口
│       ├── App.tsx               # 路由配置
│       ├── index.css             # TailwindCSS + 自定义样式
│       ├── api/
│       │   └── client.ts         # Axios 客户端 + API 封装 + 类型定义
│       ├── components/
│       │   └── Layout.tsx        # 顶部导航栏 + 页面布局
│       ├── hooks/
│       │   └── useWebSocket.ts   # WebSocket Hook
│       └── pages/
│           ├── SubmitPage.tsx    # 新建转写任务
│           ├── TasksPage.tsx     # 任务列表
│           ├── TaskDetailPage.tsx# 任务详情（进度/预览/下载）
│           ├── CompletedScriptsPage.tsx  # 已完成脚本汇总
│           └── SettingsPage.tsx  # 设置（API Key）
├── src/                          # 核心转写模块（前后端/CLI 共享）
│   ├── __init__.py
│   ├── downloader.py             # yt-dlp 视频下载
│   ├── audio_extractor.py        # ffmpeg 音频提取
│   ├── transcriber.py            # OpenAI Whisper API 转写
│   ├── local_transcriber.py      # 本地 faster-whisper 转写
│   ├── formatter.py              # TXT/SRT/VTT/JSON 格式化输出
│   └── utils.py                  # Facebook URL 验证与 ID 提取
├── tests/                        # 测试目录
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_downloader.py
│   ├── test_audio_extractor.py
│   ├── test_transcriber.py
│   ├── test_local_transcriber.py
│   ├── test_formatter.py
│   ├── test_utils.py
│   └── api/
│       ├── test_health.py
│       ├── test_tasks.py
│       ├── test_config.py
│       ├── test_worker.py
│       ├── test_schemas.py
│       └── test_ws.py
├── output/                       # 转写结果输出目录
├── temp/                         # 临时文件目录
├── main.py                       # CLI 入口（向后兼容）
├── requirements.txt              # Python 依赖
├── docker-compose.yml            # Docker 编排（redis/backend/worker/frontend）
├── Dockerfile                    # 后端镜像（Python 3.11 + ffmpeg）
├── .dockerignore
├── .env.example                  # 环境变量模板
├── .env                          # 实际环境变量（gitignore）
├── README.md                     # 项目说明与快速开始
├── PROGRESS.md                   # 开发进度记录
└── requirements.md               # 本需求文档
```

---

## 5. 接口设计

### 5.1 REST API

所有接口需要在 Header 中携带 `X-API-Key`。

| 方法 | 路径 | 说明 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/` | 服务根信息 | — | `{ name, version, docs }` |
| GET | `/health` | 健康检查 | — | `{ status: "ok" }` |
| POST | `/tasks` | 创建转写任务 | `TaskCreate` | `TaskInfo` (202) |
| GET | `/tasks` | 任务列表 | `skip`, `limit` 查询参数 | `TaskInfo[]` |
| GET | `/tasks/{id}` | 任务详情 | — | `TaskInfo` |
| GET | `/tasks/{id}/result` | 获取结果数据（JSON 含 segments/full_text） | — | `TaskResult` |
| GET | `/tasks/{id}/download` | 下载结果文件 | — | 文件流 |

**TaskCreate 请求体**：
```json
{
  "url": "https://www.facebook.com/watch?v=123456",
  "language": "auto",
  "output_format": "json",
  "use_local": true,
  "model_size": "small",
  "device": "cpu"
}
```

**TaskInfo 响应**：
```json
{
  "id": "uuid",
  "status": "completed",
  "url": "https://...",
  "language": "zh",
  "output_format": "json",
  "use_local": true,
  "model_size": "small",
  "created_at": "2026-04-26T10:00:00",
  "updated_at": "2026-04-26T10:05:00",
  "completed_at": "2026-04-26T10:05:00",
  "error_message": null,
  "result_url": "/tasks/uuid/download",
  "progress": 100
}
```

### 5.2 WebSocket 接口

| 路径 | 说明 | 认证 |
|------|------|------|
| `WS /ws/tasks?api_key=xxx` | 实时任务进度推送 | Query 参数 `api_key` |

**消息格式**：
```json
{
  "task_id": "uuid",
  "status": "transcribing",
  "progress": 50
}
```

**心跳**：客户端可发送 `"ping"`，服务端回复 `"pong"`。

### 5.3 CLI 命令行接口

```bash
# 基本用法（默认 OpenAI API 模式）
python main.py "https://www.facebook.com/watch?v=123456" --output result.txt

# 指定输出格式
python main.py "<url>" --format srt --output result.srt

# 使用本地 Whisper（免费，无需 API Key）
python main.py "<url>" --local --model-size small --device cpu

# 指定语言（提升识别准确度）
python main.py "<url>" --language zh --output result.json

# 保留临时文件（调试用）
python main.py "<url>" --keep-temp
```

**CLI 参数**：
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `url` | 必填 | Facebook 视频链接 |
| `--output`, `-o` | `./output/result.txt` | 输出文件路径 |
| `--format`, `-f` | `txt` | 输出格式：txt, srt, vtt, json |
| `--language`, `-l` | `en` | 音频语言（auto 为自动检测） |
| `--temp-dir` | `./temp` | 临时文件目录 |
| `--keep-temp` | false | 保留临时文件 |
| `--local` | false | 使用本地 Whisper 模型 |
| `--model-size` | `small` | 本地模型：tiny/base/small/medium/large-v3 |
| `--device` | `cpu` | 推理设备：cpu/cuda |

---

## 6. 数据流与状态机

### 6.1 任务生命周期

```
PENDING ──▶ DOWNLOADING ──▶ EXTRACTING_AUDIO ──▶ TRANSCRIBING ──▶ SAVING ──▶ COMPLETED
   │            │                │                  │               │
   └────────────┴────────────────┴──────────────────┴───────────────┘
                                     │
                                     ▼
                                  FAILED
```

### 6.2 进度映射

| 阶段 | Celery State | 进度百分比 |
|------|-------------|-----------|
| 等待中 | PENDING | 0 |
| 下载中 | DOWNLOADING | 10 |
| 提取音频 | EXTRACTING_AUDIO | 30 |
| 语音识别 | TRANSCRIBING | 50 |
| 保存结果 | SAVING | 90 |
| 已完成 | SUCCESS | 100 |
| 失败 | FAILURE | — |

### 6.3 错误码定义

| 错误场景 | 描述 | 处理建议 |
|---------|------|---------|
| 链接格式无效 | URL 不匹配支持的 Facebook 视频模式 | 检查链接是否为公开 Facebook 视频 |
| 视频不可访问 | 视频非公开或已被删除 | 确认视频为公开可见 |
| 视频下载失败 | yt-dlp 下载出错 | 检查网络连接或视频是否被删除 |
| 音频提取失败 | ffmpeg 处理出错 | 检查视频文件完整性 |
| 未配置 API Key | 使用 API 模式但缺少 OPENAI_API_KEY | 配置环境变量或使用 --local 模式 |
| 语音识别失败 | Whisper 处理出错 | 检查音频文件或模型状态 |
| 处理超时 | Celery 任务超过 1 小时 | 尝试更短的视频或检查服务负载 |

---

## 7. 部署与运维

### 7.1 环境依赖

**开发环境**：
- Python 3.11+
- Node.js 20+
- Redis 7+
- ffmpeg（系统依赖）

**生产环境（Docker）**：
- Docker + Docker Compose
- 可选：NVIDIA Docker Runtime（用于 GPU 加速）

### 7.2 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_KEY` | `dev-api-key-change-me` | 团队共享的 API 认证 Key |
| `OPENAI_API_KEY` | — | OpenAI API Key（API 模式必填） |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接地址 |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery Broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Celery Backend |
| `TEMP_DIR` | `./temp` | 临时文件目录 |
| `OUTPUT_DIR` | `./output` | 结果输出目录 |
| `RESULT_RETENTION_DAYS` | `7` | Redis 任务元数据保留天数 |

### 7.3 部署方式

**方式一：Docker Compose（推荐）**
```bash
cp .env.example .env
# 编辑 .env，设置 API_KEY 和 OPENAI_API_KEY
docker-compose up -d
# 前端: http://localhost:8080
# API 文档: http://localhost:8000/docs
```

**方式二：本地开发**
```bash
# 后端
pip install -r requirements.txt
redis-server
cd api && uvicorn main:app --reload --port 8000
celery -A api.celery_app worker --loglevel=info

# 前端
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

### 7.4 日志规范

- 后端使用标准 Python logging
- 任务失败时自动保存详细 traceback 到 `output/{task_id}.error.log`
- Celery Worker 控制台输出任务执行日志

---

## 8. 已知限制与后续规划

### 8.1 当前限制

| 限制 | 说明 |
|------|------|
| 单点 API Key | 团队共享一个 Key，无用户隔离 |
| 无数据库 | 任务元数据存 Redis，结果存文件系统，依赖 Redis 持久化 |
| 无批量提交 | 仅支持单链接提交，不支持上传文件批量创建 |
| 无说话人分离 | 转写结果不含 speaker 标识 |
| 无文本摘要 | 未集成 LLM 自动生成摘要 |
| GPU 配置限制 | docker-compose 中 NVIDIA 设备配置在非 NVIDIA 环境需手动注释 |

### 8.2 后续规划

| 优先级 | 功能 | 说明 |
|--------|------|------|
| 高 | 用户系统 | JWT 多用户认证，任务归属到用户 |
| 高 | 数据库持久化 | PostgreSQL/SQLite 存储任务和结果 |
| 高 | 测试覆盖 | 后端 pytest 单元测试、前端 Vitest 组件测试 |
| 中 | 批量处理 | 支持上传 txt/csv 批量提交多个链接 |
| 中 | 说话人分离 | 集成 pyannote.audio |
| 中 | 文本摘要 | 基于 LLM 自动生成视频摘要 |
| 中 | Flower 监控 | Celery 任务队列监控面板 |
| 低 | 前端优化 | 暗黑模式、移动端适配、任务搜索筛选 |
| 低 | 运维监控 | Prometheus/Grafana、API 限流、日志聚合 |

---

## 9. 附录

### 9.1 参考资料

- [yt-dlp 文档](https://github.com/yt-dlp/yt-dlp)
- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [ffmpeg 文档](https://ffmpeg.org/documentation.html)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Celery 文档](https://docs.celeryq.dev/)

### 9.2 术语表

| 术语 | 说明 |
|-----|------|
| Diarization | 说话人分离，识别音频中不同说话人的片段 |
| SRT | SubRip Subtitle，常见字幕文件格式 |
| VTT | WebVTT，网页视频字幕格式 |
| Whisper | OpenAI 开源的语音识别模型 |
| faster-whisper | 基于 CTranslate2 优化的 Whisper 实现 |
| yt-dlp | 支持多平台的视频下载工具 |
| Celery | Python 分布式任务队列 |
| VAD | Voice Activity Detection，语音活动检测 |
