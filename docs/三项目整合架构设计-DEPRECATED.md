# 三项目整合架构设计

> 文档版本：v1.0
> 日期：2026-05-08
> 范围：Dake-Video-Auto、Facebook-Script-Extract、Operation_Manage 整合方案

---

## 1. 现状全景

### 1.1 项目画像

| 维度 | Dake-Video-Auto | Facebook-Script-Extract | Operation_Manage |
|------|----------------|------------------------|------------------|
| **定位** | 视频自动化生产 | 视频脚本提取 | 社媒运营管理后台 |
| **语言** | Python | Python | TypeScript (Node.js) |
| **框架** | Flask 2.x | FastAPI 0.110 + Celery 5.3 | NestJS 11 + React 19 |
| **数据库** | SQLite (任务队列) | Redis (元数据 + 队列) | PostgreSQL 16 + Prisma |
| **认证** | Session + 硬编码密码 | Header API Key | JWT + RBAC (3 角色) |
| **前端** | Jinja2 模板 (vanilla JS) | React + Vite (独立) | React 19 + Ant Design 5 |
| **任务队列** | 自研 SQLite + threading | Celery + Redis Pub/Sub | 无 (同步 CRUD) |
| **Whisper** | openai-whisper | faster-whisper / OpenAI API | 无 |
| **服务对象** | AT-Machining / Boswindor | 同上 | Boswindor 门窗工厂 |

### 1.2 核心发现：高度重叠的 Python 能力

两个 Python 项目共享大量底层能力，但各自重复实现：

| 能力 | DVA 实现 | FB-SE 实现 | 建议统一后 |
|------|---------|-----------|-----------|
| 视频下载 | `downloader_pw.py` (Playwright + requests + yt-dlp 备用) | `src/downloader.py` (yt-dlp + Playwright Ads) | 统一为 `media.downloader`，支持多平台 |
| 浏览器自动化 | Playwright (小红书) | Playwright (FB Ads Library) | 共用 Playwright 实例池 |
| 音频提取 | FFmpeg subprocess | `src/audio_extractor.py` (FFmpeg) | 统一 FFmpeg 封装 |
| 语音识别 | `openai-whisper` (base) | `faster-whisper` (tiny~large-v3, CPU/CUDA) | 统一为 `faster-whisper` |
| TTS 语音 | `edge-tts` (22 种英文音色) | 无 | 保留并扩展 |
| 字幕生成 | Whisper → SRT (9 种样式) | 无 | 保留并扩展 |
| 任务队列 | 自研 SQLite + threading | Celery + Redis | 统一为 Celery + Redis |
| 视频编辑 | `editor_advanced.py` (FFmpeg filter_complex) | 无 | 保留 |

**关键结论**：两个 Python 项目必须合并为一个 `media-service`，消除重复依赖和运维负担。

### 1.3 关键问题诊断

1. **三重认证**：运营人员需要记 3 套密码，权限无法打通（DVA 只有一个 admin，FB-SE 只有一个 API Key）。
2. **三重前端**：三个 UI 风格完全不同，切换成本高。
3. **数据孤岛**：选题在 Operation_Manage 里，素材在 DVA 文件系统里，参考脚本在 FB-SE Redis 里，没有关联。
4. **任务队列不一致**：DVA 用 SQLite + threading（难扩展、难观测），FB-SE 用 Celery + Redis（成熟）。
5. **Whisper 双轨**：DVA 用 `openai-whisper`（慢、大、不支持 int8），FB-SE 用 `faster-whisper`（快、小、支持 CUDA）。应统一为后者。
6. **文件管理缺失**：DVA 和 FB-SE 都把结果写本地文件，没有统一的资产管理和生命周期策略。

---

## 2. 整合目标

### 2.1 用户体验目标

- **一个入口**：统一域名，单点登录，Ant Design 风格一致
- **一条工作流**：选题 → 脚本提取/撰写 → 视频生产 → 排期发布 → 数据回收，全流程在一个系统内闭环
- **一个权限体系**：SUPER_ADMIN / MANAGER / OPERATOR 三角色控制所有功能可见性

### 2.2 技术目标

- **双服务架构**：NestJS (业务主控) + Python media-service (媒体计算)
- **统一队列**：所有异步任务走 Celery + Redis
- **统一存储**：业务数据走 PostgreSQL，任务状态走 Redis，文件走对象存储或共享卷
- **可观测**：统一的日志、任务进度追踪、错误通知

---

## 3. 目标架构

### 3.1 总体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                             │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│                     Nginx (网关)                             │
│  · /               → React 静态资源 (Operation_Manage web)   │
│  · /api/v1/*       → NestJS (业务 API)                      │
│  · /api/media/*    → media-service (FastAPI)                │
│  · /ws/media/*     → media-service WebSocket                │
│  · /assets/*       → MinIO / 共享卷 (文件下载)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼─────┐ ┌──────▼───────┐
│  NestJS API  │ │ media-   │ │   Redis      │
│  (业务主控)   │ │ service  │ │  · Celery    │
│              │ │(媒体计算) │ │    Broker    │
│ · Auth/JWT   │ │          │ │  · Pub/Sub   │
│ · RBAC       │ │ · FastAPI│ │  · 缓存      │
│ · Prisma/ORM │ │ · Celery │ └──────────────┘
│ · Content    │ │ · FFmpeg │
│ · Calendar   │ │ · faster-│
│ · Topic      │ │   whisper│
│ · Account    │ │ · edge-  │
│ · Dashboard  │ │   tts    │
│ · Lead       │ │ · Play-  │
│              │ │   wright │
└───────┬──────┘ └────┬─────┘
        │             │
┌───────▼─────────────▼───────┐
│      PostgreSQL 16          │
│  · 用户、权限                │
│  · 账号、选题、内容计划       │
│  · 媒体任务、媒体资产         │
│  · 线索、数据看板            │
└─────────────────────────────┘
```

### 3.2 职责边界

| 职责 | NestJS (业务主控) | media-service (媒体计算) |
|------|------------------|-------------------------|
| **认证授权** | JWT 颁发 + 校验 + RBAC | 校验 NestJS 转发的 Service Token |
| **业务数据** | User / Account / Content / Topic / Lead 等全量 CRUD | 不持有业务表，只存任务参数和结果摘要 |
| **异步任务编排** | 接收用户请求 → 生成 `MediaTask` 记录 → 调用 media-service → 轮询/监听进度 → 更新 Content 状态 | 接收任务 → Celery 执行 → 推送进度 → 返回结果 |
| **文件生命周期** | 记录 `MediaAsset` 元数据（URL、大小、类型） | 负责文件读写（下载、剪辑、生成） |
| **前端渲染** | AntD React，包含内容日历、选题库、数据看板 | 不提供独立前端，所有页面嵌入 NestJS 前端 |
| **消息通知** | 任务完成/失败时发系统通知 | 只推送原始进度事件 |

---

## 4. 数据模型扩展（Prisma）

在现有 `Operation_Manage` schema 基础上扩展，增加媒体任务和资产追踪。

```prisma
// ========== 新增枚举 ==========
enum MediaTaskType {
  SCRIPT_EXTRACT    // 视频脚本提取（原 FB-SE）
  VIDEO_DOWNLOAD    // 视频下载（小红书/抖音等）
  VIDEO_EDIT        // 视频剪辑（Logo/BGM/TTS/字幕/调色）
  TTS_GENERATE      // TTS 语音生成
  SUBTITLE_GENERATE // 字幕生成
}

enum MediaTaskStatus {
  PENDING
  RUNNING
  COMPLETED
  FAILED
  CANCELLED
}

enum AssetType {
  VIDEO_RAW
  VIDEO_EDITED
  AUDIO_EXTRACTED
  AUDIO_TTS
  SCRIPT_TXT
  SCRIPT_SRT
  SCRIPT_VTT
  SCRIPT_JSON
  SUBTITLE_SRT
  LOGO
  BGM
  THUMBNAIL
}

// ========== 新增模型 ==========
model MediaTask {
  id            String          @id @default(uuid())
  contentId     String?         @map("content_id")
  taskType      MediaTaskType   @map("task_type")
  status        MediaTaskStatus @default(PENDING)
  progress      Int             @default(0) // 0-100

  // 任务参数（JSON，包含 URL、配置项等）
  params        Json?

  // 结果摘要
  result        Json?
  errorMessage  String?         @map("error_message") @db.Text

  // 关联的媒体资产
  assets        MediaAsset[]

  createdAt     DateTime        @default(now()) @map("created_at")
  updatedAt     DateTime        @updatedAt @map("updated_at")
  completedAt   DateTime?       @map("completed_at")

  // 关联内容计划
  content       Content?        @relation(fields: [contentId], references: [id], onDelete: SetNull)

  @@index([contentId])
  @@index([status, taskType])
  @@map("media_tasks")
}

model MediaAsset {
  id          String    @id @default(uuid())
  taskId      String    @map("task_id")
  assetType   AssetType @map("asset_type")

  // 文件存储路径或 URL
  storagePath String    @map("storage_path") @db.VarChar(500)
  publicUrl   String?   @map("public_url") @db.VarChar(500)

  fileSize    BigInt?   @map("file_size")
  mimeType    String?   @map("mime_type") @db.VarChar(100)
  duration    Decimal?  @db.Decimal(8, 2) // 音视频时长（秒）
  metadata    Json?     // 扩展元数据（如 Whisper segments、字幕样式等）

  createdAt   DateTime  @default(now()) @map("created_at")

  task        MediaTask @relation(fields: [taskId], references: [id], onDelete: Cascade)

  @@index([taskId])
  @@index([assetType])
  @@map("media_assets")
}

// ========== Content 模型扩展 ==========
// 现有 Content 模型新增字段（用于关联媒体产物）
// 不改动现有字段，只做增量：
//
// model Content {
//   ...existing fields...
//   mediaTasks   MediaTask[]  // 一个内容计划可包含多个媒体任务
// }
```

### 4.1 Content 状态机与 MediaTask 的映射

```
Content.status          MediaTask 状态流转
─────────────────────────────────────────────────
PENDING    ──选题已创建，未开始生产──
    │
    ▼ 用户发起脚本提取 / 视频下载 / 剪辑
PRODUCING  ──MediaTask 创建，状态为 RUNNING──
    │
    ▼ MediaTask 全部完成
READY      ──产物已就绪，待发布──
    │
    ▼ 运营人员发布到社媒平台
PUBLISHED  ──已发布，进入数据回收阶段──
    │
    ▼ 数据归档
ARCHIVED
```

---

## 5. media-service 设计（Python）

### 5.1 项目结构

合并后的 `media-service` 基于 FB-SE 的 FastAPI + Celery 骨架，吸收 DVA 的核心模块：

```
media-service/
├── api/
│   ├── main.py                 # FastAPI 入口
│   ├── celery_app.py           # Celery 配置（保留 FB-SE）
│   ├── core/
│   │   ├── config.py           # Pydantic Settings
│   │   └── security.py         # Service Token 校验
│   ├── models/
│   │   └── schemas.py          # 请求/响应模型（扩展 DVA 的 TTS/Edit）
│   ├── routers/
│   │   ├── health.py
│   │   ├── tasks.py            # 任务 REST API（扩展）
│   │   ├── tts.py              # TTS 生成 API（来自 DVA）
│   │   ├── edit.py             # 视频剪辑 API（来自 DVA）
│   │   ├── download.py         # 视频下载 API（来自 DVA）
│   │   └── ws.py               # WebSocket 进度推送
│   └── tasks/
│       └── worker.py           # Celery 任务分发器
├── src/
│   ├── __init__.py
│   ├── downloader.py           # yt-dlp 下载（FB-SE）+ 小红书 Playwright（DVA）
│   ├── ads_extractor.py        # FB Ads Library 抓取（FB-SE）
│   ├── xhs_extractor.py        # 小红书下载（DVA 迁移）
│   ├── audio_extractor.py      # FFmpeg 提取音频（FB-SE）
│   ├── transcriber.py          # faster-whisper 本地转写（FB-SE，替换 DVA 的 openai-whisper）
│   ├── openai_transcriber.py   # OpenAI Whisper API 备用（FB-SE）
│   ├── tts_generator.py        # edge-tts（DVA 迁移）
│   ├── video_editor.py         # FFmpeg 视频剪辑（DVA editor_advanced 迁移）
│   ├── subtitle_generator.py   # 字幕生成（DVA 迁移）
│   ├── formatter.py            # TXT/SRT/VTT/JSON 输出（FB-SE）
│   ├── qr_generator.py         # 二维码生成（DVA 迁移）
│   └── utils.py                # URL 校验、文件工具
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### 5.2 Celery 任务类型扩展

现有 FB-SE 只有 `process_video`（下载→提取音频→转写）。合并后扩展为：

| 任务签名 | 来源 | 说明 |
|---------|------|------|
| `process_script_extract` | FB-SE | 下载 → 提取音频 → faster-whisper → 格式化输出 |
| `process_video_download` | DVA | Playwright/yt-dlp 下载 → 存为原始视频 |
| `process_video_edit` | DVA | FFmpeg filter_complex：裁剪、调速、镜像、Logo、BGM、TTS 混音、字幕、9:16 |
| `process_tts_generate` | DVA | edge-tts 生成语音 → 可选 Whisper 同步生成 SRT |
| `process_subtitle_generate` | DVA | 对已有视频/音频做 Whisper 转写 → SRT |

所有任务统一通过 Redis Pub/Sub 推送进度（百分比 + 状态 + 消息），NestJS 监听后写回 `MediaTask` 记录。

### 5.3 安全设计

- media-service **不直接面向用户**，只接受 NestJS 的内网请求。
- 认证方式：NestJS 在调用 media-service 时携带 `X-Service-Token`（预共享密钥或短期 JWT）。
- media-service 的 `/docs` 在生产环境关闭或加 Basic Auth。
- 文件访问：media-service 不写公开 URL，只写相对路径；NestJS 根据用户权限生成带签名的临时下载链接（或走 Nginx 内部转发）。

---

## 6. NestJS 扩展设计

### 6.1 新增模块

```
apps/api/src/modules/
├── auth/               # 现有（JWT + RBAC）
├── users/              # 现有
├── accounts/           # 现有
├── contents/           # 现有（需扩展 MediaTask 关联）
├── topics/             # 现有
├── media/              # 新增：媒体任务管理模块
│   ├── media.module.ts
│   ├── media.controller.ts
│   ├── media.service.ts
│   └── dto.ts
└── notifications/      # 现有（扩展：任务完成通知）
```

### 6.2 MediaService 核心逻辑

```typescript
// 伪代码，说明职责
class MediaService {
  // 用户发起"提取脚本"
  async createScriptExtractTask(contentId: string, dto: ScriptExtractDto, user: User) {
    // 1. 权限校验：OPERATOR 只能操作自己的 Content
    // 2. 创建 MediaTask 记录（status=PENDING）
    // 3. 调用 media-service POST /tasks/script-extract
    // 4. media-service 返回 taskId，更新 MediaTask.externalTaskId
    // 5. 更新 Content.status = PRODUCING
    // 6. 返回任务信息给前端
  }

  // WebSocket / 轮询接收进度
  async onProgressUpdate(externalTaskId: string, progress: number, status: string) {
    // 1. 更新 MediaTask.progress / status
    // 2. 若 COMPLETED：解析 result，创建 MediaAsset 记录，更新 Content.status = READY
    // 3. 若 FAILED：记录 errorMessage，发系统通知给操作人
    // 4. 推送 WebSocket 消息给在线用户（NestJS 网关）
  }
}
```

### 6.3 API 路由扩展

| 方法 | 路径 | 说明 | 角色 |
|------|------|------|------|
| POST | `/api/v1/media/script-extract` | 发起脚本提取任务 | MANAGER / OPERATOR |
| POST | `/api/v1/media/video-download` | 发起视频下载任务 | MANAGER / OPERATOR |
| POST | `/api/v1/media/video-edit` | 发起视频剪辑任务 | MANAGER / OPERATOR |
| POST | `/api/v1/media/tts` | 发起 TTS 生成任务 | MANAGER / OPERATOR |
| GET | `/api/v1/media/tasks` | 当前用户的媒体任务列表 | 所有角色 |
| GET | `/api/v1/media/tasks/:id` | 任务详情 + 进度 | 所有角色 |
| DELETE | `/api/v1/media/tasks/:id` | 取消/删除任务 | MANAGER / 本人 |
| GET | `/api/v1/media/assets/:id/download` | 下载产物（带权限校验） | 所有角色 |
| WS | `/api/v1/ws/media` | 实时进度推送 | 已登录用户 |

---

## 7. 统一入口与模块导航设计

### 7.1 设计原则

用户登录后，不再直接进入某一个具体页面，而是先看到一个**统一门户（Portal）**。门户以卡片/图标形式展示所有可用功能模块，用户根据当前工作意图自行选择进入。这样既保留了各模块的独立性，又避免了"不知道功能在哪"的困惑。

### 7.2 模块定义

整合后系统划分为 **6 大功能模块**：

| 模块 | 图标 | 说明 | 来源 | 可见角色 |
|------|------|------|------|---------|
| **运营看板** | Dashboard | 数据概览、待办提醒、最近任务、快捷入口 | Operation_Manage | 所有角色 |
| **内容计划** | Calendar | 内容日历、排期管理、发布状态流转 | Operation_Manage | 所有角色 |
| **选题库** | Lightbulb | 选题收集、脚本撰写、拍摄计划、参考脚本提取 | Operation_Manage + FB-SE | 所有角色 |
| **媒体中心** | VideoCamera | 视频下载、脚本提取、TTS 配音、视频剪辑、素材库 | DVA + FB-SE | MANAGER / OPERATOR |
| **账号管理** | Team | 多平台社媒账号、分组、数据看板 | Operation_Manage | MANAGER / SUPER_ADMIN |
| **系统设置** | Setting | 用户权限、媒体引擎参数、通知配置 | Operation_Manage | SUPER_ADMIN / MANAGER |

OPERATOR 看不到"账号管理"和"系统设置"模块卡片；SUPER_ADMIN 能看到全部。

### 7.3 门户页面布局

```
┌─────────────────────────────────────────────────────────────┐
│  🏠 Boswindor 社媒运营平台        👤 张三  [通知🔔] [退出]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  欢迎回来，今天是 2026-05-08，你有 3 个待处理任务              │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 📊 运营看板  │  │ 📅 内容计划  │  │ 💡 选题库    │         │
│  │ 数据驱动决策 │  │ 本周 5 条待  │  │ 12 个待拍摄  │         │
│  │             │  │ 发布         │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 🎬 媒体中心  │  │ 👥 账号管理  │  │ ⚙️ 系统设置  │         │
│  │ 3 个任务运行 │  │ 8 个活跃账号 │  │             │         │
│  │ 中          │  │             │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ───────────────────── 最近动态 ─────────────────────        │
│  │ [14:32] 视频剪辑任务 #a3f2 已完成                       │
│  │ [13:15] 脚本提取任务 #b8e1 失败 — 链接失效               │
│  │ [11:00] 内容计划 "新品发布" 状态变为 READY              │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**交互细节：**
- 模块卡片悬停时上浮 + 阴影，点击后进入对应模块首页
- 卡片右下角显示该模块的"活跃数/待办数"徽标（如内容计划的待发布数）
- 最近动态区按时间倒序展示当前用户相关的系统事件（任务完成、失败、状态变更）
- 顶部导航栏始终保留，进入具体模块后左侧展开二级菜单

### 7.4 侧边栏导航结构

进入任一模块后，左侧侧边栏显示该模块的二级菜单。顶部面包屑显示：门户 > 模块 > 页面。

```
登录 → 门户（选择模块）
              │
              ├──→ 运营看板
              │      ├── 数据概览
              │      └── 我的待办
              │
              ├──→ 内容计划
              │      ├── 月视图日历
              │      ├── 周视图日历
              │      └── 内容列表
              │
              ├──→ 选题库
              │      ├── 选题列表
              │      ├── 脚本撰写
              │      └── 参考脚本提取
              │
              ├──→ 媒体中心
              │      ├── 任务总览（所有媒体任务）
              │      ├── 🎙️ 脚本提取
              │      ├── 📥 视频下载
              │      ├── ✂️ 视频剪辑
              │      ├── 🎤 TTS 配音
              │      └── 🗂️ 素材库
              │
              ├──→ 账号管理
              │      ├── 账号列表
              │      ├── 分组管理
              │      └── 数据统计
              │
              └──→ 系统设置
                     ├── 用户管理
                     ├── 角色权限
                     ├── 媒体引擎配置
                     └── 通知设置
```

### 7.5 快捷操作：全局悬浮按钮

无论用户在哪个模块，右下角始终有一个**全局快捷操作按钮（FAB）**：

```
[ + ] 点击展开：
  ├── 🎙️ 快速提取脚本
  ├── 📥 快速下载视频
  ├── ✂️ 快速剪辑视频
  └── 🎤 快速生成 TTS
```

点击后弹出对应功能的简化版提交抽屉（Drawer），无需跳转页面即可发起任务。

### 7.6 路由设计

```typescript
// 门户路由
/portal                  # 统一入口首页（登录后默认跳转）

// 各模块路由前缀
/dashboard               # 运营看板
/contents                # 内容计划
/topics                  # 选题库
/media                   # 媒体中心
  /media/tasks           # 媒体任务总览
  /media/script-extract  # 脚本提取
  /media/video-download  # 视频下载
  /media/video-edit      # 视频剪辑
  /media/tts             # TTS 配音
  /media/assets          # 素材库
/accounts                # 账号管理
/settings                # 系统设置

// 嵌套内容页（从任意模块进入）
/content/:id             # 内容详情（含关联媒体任务）
/task/:id                # 媒体任务详情（跨模块通用）
```

### 7.7 权限控制实现

前端在路由守卫层校验：
1. 用户登录后，调用 `GET /api/v1/auth/me` 获取当前用户角色和可访问模块列表
2. 门户页面根据返回的 `accessibleModules` 动态渲染卡片（无权限的模块不显示）
3. 直接访问无权限路由时，重定向到 `/portal` 并提示"无权访问"
4. 侧边栏菜单同样根据权限动态生成

---

## 8. 前端统一方案

### 8.1 页面规划

在 Operation_Manage 现有的 Ant Design 前端中新增以下模块：

```
apps/web/src/pages/
├── login/                    # 现有（统一登录）
├── portal/                   # 新增：统一入口门户
│   └── index.tsx             # 模块卡片 + 最近动态 + 快捷入口
├── dashboard/                # 现有（数据看板，新增媒体任务统计卡片）
├── accounts/                 # 现有
├── contents/                 # 现有（内容日历，新增"发起生产"按钮）
│   └── components/
│       └── ContentProductionModal.tsx  # 选择：脚本提取 / 视频下载 / 视频剪辑
├── topics/                   # 现有（选题库，新增"提取参考脚本"入口）
├── media/                    # 新增：媒体中心
│   ├── tasks/                # 任务列表（仿 FB-SE 任务页，AntD 风格）
│   ├── task-detail/          # 任务详情 + 进度 + 日志 + 下载
│   ├── script-extract/       # 脚本提取提交页
│   ├── video-download/       # 视频下载提交页
│   ├── video-edit/           # 视频剪辑配置页（迁移 DVA 的剪辑面板）
│   ├── tts/                  # TTS 生成页（音色选择 + 试听）
│   └── assets/               # 我的素材库（ Logo / BGM / TTS / 成品视频）
├── settings/                 # 现有（新增"媒体引擎设置"：模型大小、设备、API Key）
└── materials/                # 现有
```

### 8.2 被废弃的前端

- Dake-Video-Auto 的 Jinja2 模板 (`templates/index.html`) → **废弃**
- Facebook-Script-Extract 的独立 React Vite 前端 → **废弃**
- 两者功能全部迁移到 Operation_Manage 的 AntD 前端中

### 8.3 UI 组件关键设计

**视频剪辑页**（原 DVA 最复杂的功能）：
- 左侧：视频预览 + 时间轴
- 右侧：配置面板（分段表单）
  - Logo：上传 + 位置选择 + 大小滑块
  - BGM：从素材库选择 + 音量 + 循环开关
  - TTS：文案输入 + 音色选择 + 语速 + 试听
  - 效果：镜像开关、速度滑块、调色三轴
  - 字幕：内容输入 + 样式预设 + 时间范围
  - 输出：9:16 开关、裁剪首尾
- 底部：提交剪辑任务 → 跳转任务列表看进度

**脚本提取页**（原 FB-SE）：
- 输入框：粘贴 Facebook / YouTube / FB Ads Library 链接
- 选项：语言、输出格式、本地/API 引擎、模型大小
- 提交 → 任务列表实时刷新

---

## 9. 文件存储与资产流转

### 9.1 存储选型

| 方案 | 优点 | 缺点 | 建议 |
|------|------|------|------|
| **共享卷 (Docker Volume)** | 简单、零成本 | 单点、难扩容、无 CDN | 阶段一使用 |
| **MinIO (S3-compatible)** | 自建对象存储、URL 签名、可扩容 | 多一个服务 | 阶段二迁移 |
| **云对象存储 (OSS/S3)** | 可靠、有 CDN | 有费用、需外网 | 长期推荐 |

**阶段一（整合期）**：使用 Docker Volume `media-assets`，挂载到 media-service 和 NestJS。

**路径约定**：
```
/media-assets/
  ├── tasks/{task_id}/          # 任务临时文件
  │   ├── raw_video.mp4
  │   ├── audio.wav
  │   └── transcript.json
  ├── contents/{content_id}/    # 内容计划关联的永久资产
  │   ├── edited_video.mp4
  │   ├── subtitles.srt
  │   └── tts_audio.mp3
  ├── shared/
  │   ├── logos/                # 全局 Logo 素材
  │   ├── bgm/                  # 全局 BGM 素材
  │   └── tts/                  # TTS 生成缓存
```

### 9.2 资产生命周期

1. media-service 完成任务后，将产物移动到 `contents/{content_id}/`。
2. NestJS 创建 `MediaAsset` 记录，指向 storagePath。
3. 用户通过 NestJS 的 `/api/v1/media/assets/:id/download` 下载（权限校验后内部转发或重定向）。
4. 定期清理脚本：`contents/{content_id}/` 保留 90 天，`tasks/{task_id}/` 保留 7 天后自动删除。

---

## 10. 认证与权限统一

### 10.1 认证流

```
用户登录 → NestJS AuthService → 颁发 JWT (accessToken + refreshToken)
    │
    ▼
前端所有请求携带 Authorization: Bearer <JWT>
    │
    ├─→ NestJS API：直接校验 JWT + RBAC
    │
    └─→ media-service：NestJS 以 Service Account 调用，
                       携带 X-Service-Token（预共享密钥）
                       media-service 不直接面向用户
```

### 10.2 权限矩阵

| 功能 | SUPER_ADMIN | MANAGER | OPERATOR |
|------|-------------|---------|----------|
| 管理所有媒体任务 | ✅ | ✅ | ❌（仅自己的） |
| 发起脚本提取 | ✅ | ✅ | ✅ |
| 发起视频剪辑 | ✅ | ✅ | ✅ |
| 下载他人产物 | ✅ | ✅ | ❌ |
| 删除他人任务 | ✅ | ✅ | ❌ |
| 配置媒体引擎参数 | ✅ | ❌ | ❌ |
| 查看系统日志 | ✅ | ❌ | ❌ |

---

## 11. 部署架构

### 11.1 Docker Compose（阶段一）

```yaml
# 顶层 docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes: ["./nginx.conf:/etc/nginx/nginx.conf"]

  web:
    build: ./apps/web
    # React 静态资源，Nginx 直接代理

  api:
    build: ./apps/api
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/opman
      - REDIS_URL=redis://redis:6379/0
      - MEDIA_SERVICE_URL=http://media-service:8000
      - MEDIA_SERVICE_TOKEN=${MEDIA_SERVICE_TOKEN}

  media-service:
    build: ./media-service
    environment:
      - SERVICE_TOKEN=${MEDIA_SERVICE_TOKEN}
      - REDIS_URL=redis://redis:6379/1
      - CELERY_BROKER_URL=redis://redis:6379/1
      - TEMP_DIR=/tmp/media-tasks
      - OUTPUT_DIR=/media-assets
    volumes:
      - media-assets:/media-assets
      - media-temp:/tmp/media-tasks
    # GPU 支持（可选）
    # deploy:
    #   resources:
    #     reservations:
    #       devices: [{ driver: nvidia, count: 1, capabilities: [gpu] }]

  media-worker:
    build: ./media-service
    command: celery -A api.celery_app worker -l info -c 2
    environment:
      - REDIS_URL=redis://redis:6379/1
      - CELERY_BROKER_URL=redis://redis:6379/1
    volumes:
      - media-assets:/media-assets
      - media-temp:/tmp/media-tasks
    # 同样可配 GPU

  postgres:
    image: postgres:16-alpine
    volumes: ["postgres_data:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    volumes: ["redis_data:/data"]

volumes:
  media-assets:
  media-temp:
  postgres_data:
  redis_data:
```

### 11.2 环境变量清单

| 变量 | 服务 | 说明 |
|------|------|------|
| `DATABASE_URL` | NestJS | PostgreSQL 连接串 |
| `REDIS_URL` | NestJS / media-service | Redis 连接串 |
| `JWT_SECRET` | NestJS | JWT 签名密钥 |
| `MEDIA_SERVICE_URL` | NestJS | media-service 内网地址 |
| `MEDIA_SERVICE_TOKEN` | NestJS + media-service | 服务间认证密钥 |
| `OPENAI_API_KEY` | media-service | OpenAI Whisper API 备用 |
| `CELERY_BROKER_URL` | media-service | Celery Broker |
| `TEMP_DIR` | media-service | 任务临时目录 |
| `OUTPUT_DIR` | media-service | 产物输出目录 |

---

## 12. 迁移路线图

### Phase 1：基础建设（1 周）

1. **创建 unified-monorepo**
   - 将三个项目代码平移进来：
     ```
     unified/
     ├── apps/
     │   ├── api/              # Operation_Manage NestJS
     │   └── web/              # Operation_Manage React
     └── services/
         └── media-service/    # 新建，先 copy FB-SE 代码
     ```
   - 配置顶层 `docker-compose.yml` + `package.json` workspaces。

2. **数据库迁移**
   - 在 Prisma schema 中增加 `MediaTask`、`MediaAsset` 模型。
   - 生成并执行迁移：`pnpm db:migrate`。

3. **服务间通信**
   - NestJS 新增 `MediaService` HTTP 客户端（axios）。
   - media-service 新增 `X-Service-Token` 校验中间件。

### Phase 2：media-service 合并（1.5 周）

1. **吸收 DVA 核心模块**
   - 将 `core/downloader_pw.py` → `src/xhs_extractor.py`
   - 将 `core/editor_advanced.py` → `src/video_editor.py`
   - 将 `core/tts_generator.py` → `src/tts_generator.py`
   - 将 `core/qr_generator.py` → `src/qr_generator.py`
   - 将 `core/subtitle_generator.py` 逻辑合并到 `src/transcriber.py` 周边

2. **统一 Whisper**
   - 删除 DVA 中的 `openai-whisper` 依赖。
   - 确保 `src/transcriber.py`（faster-whisper）覆盖所有语音识别场景：脚本提取、字幕生成、TTS 同步字幕。

3. **扩展 Celery 任务**
   - 在 `api/tasks/worker.py` 中新增 `process_video_download`、`process_video_edit`、`process_tts_generate`。
   - 统一进度推送格式：
     ```json
     {"task_id": "...", "status": "running", "progress": 45, "stage": "transcribing", "message": "..."}
     ```

4. **扩展 FastAPI 路由**
   - 新增 `/tasks/download`、`/tasks/edit`、`/tasks/tts`。
   - 保留原有 `/tasks/script-extract`。

### Phase 3：NestJS 业务对接（1 周）

1. **新增 `media` 模块**
   - Controller + Service + DTO。
   - 实现任务创建、列表、详情、取消、下载接口。

2. **WebSocket 网关**
   - NestJS 新增 `MediaGateway`，监听 Redis Pub/Sub 的进度事件，推送给在线用户。

3. **通知集成**
   - 任务完成/失败时，写入 `Notification` 表，前端右上角红点提示。

4. **Content 关联**
   - 在创建 Content 时，支持直接绑定 `topicId` 并发起关联媒体任务。
   - Content 详情页显示关联的 MediaTask 列表和产物预览。

### Phase 4：前端迁移（1.5 周）

1. **新建 `media/` 页面模块**
   - 任务列表页（AntD Table + Tag 状态 + 进度条）
   - 任务详情页（步骤条 + 日志 + 下载按钮）
   - 脚本提取提交页
   - 视频下载提交页
   - 视频剪辑配置页（最复杂，需要把 DVA 的表单逻辑搬过来）
   - TTS 生成页（音色下拉 + 试听播放器）
   - 素材库页（Logo / BGM / 成品视频管理）

2. **改造现有页面**
   - `topics/`：选题详情页增加"提取参考脚本"按钮（调用 media-service）。
   - `contents/`：内容日历增加"发起生产"按钮；Content 卡片显示媒体任务状态徽标。
   - `dashboard/`：增加媒体任务统计（今日任务数、成功率、待下载产物数）。

3. **废弃旧前端**
   - 删除 DVA 的 `templates/` 和 `static/`。
   - 删除 FB-SE 的 `frontend/`。

### Phase 5：验证与优化（1 周）

1. **端到端测试**
   - 选题 → 脚本提取 → 视频下载 → 视频剪辑 → 内容计划排期 → 发布，全流程跑通。

2. **性能测试**
   - 并发 3 个 Celery Worker，验证 Redis 队列不丢任务。
   - 大视频（>500MB）剪辑测试超时和内存。

3. **数据迁移**
   - 若 DVA 和 FB-SE 有历史任务/文件需要保留，写一次性脚本导入到 NestJS 的 `MediaTask` / `MediaAsset` 表中。

4. **文档与交接**
   - 更新 README、DEPLOY.md、API 文档。
   - 给运营人员写操作手册。

---

## 13. 风险与应对

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| **视频剪辑逻辑迁移复杂** | Phase 2/4 延期 | 中 | 先保留 DVA 独立运行作为 fallback，media-service 的 edit 任务先跑 shadow 测试 |
| **faster-whisper 替代 openai-whisper 后字幕质量下降** | 用户投诉 | 低 | 保留模型大小可配置（base / small / medium），让用户选；保留 OpenAI API 作为最高质量备选 |
| **NestJS 与 media-service 网络不通** | 任务提交失败 | 低 | Docker Compose 内网 + health check + 重试机制 |
| **文件存储单点故障** | 数据丢失 | 中 | 阶段二尽快迁移到 MinIO 或云存储；定期备份卷 |
| **前端工作量大** | Phase 4 超期 | 高 | DVA 的剪辑页可先 iframe 嵌入，再逐步迁移；或保留 DVA 独立入口作为过渡 |
| **Celery Worker 内存泄漏** | 服务不稳定 | 中 | Worker 配置 `--max-tasks-per-child=50`，配合监控自动重启 |
| **运营人员抗拒新界面** | 采纳率低 | 中 | 灰度发布，先让 1 个运营试用，收集反馈再全量推 |

---

## 14. 关键决策记录（ADR）

### ADR-001：为什么不把 NestJS 也改写成 Python？

- **反对理由**：Operation_Manage 已经具备完整的 JWT/RBAC、Prisma ORM、TypeScript 类型安全、测试覆盖。重写为 FastAPI 需要 4-6 周，且 NestJS 的依赖注入、模块组织、GraphQL 扩展性在 Node 生态更成熟。
- **结论**：保留 NestJS 作为业务主控，通过 HTTP 调用 media-service。

### ADR-002：为什么 media-service 用 FastAPI 而不是 Flask？

- **FB-SE 已经是 FastAPI**：有成熟的 Pydantic 模型、自动 OpenAPI 文档、异步原生支持。
- **DVA 的 Flask 是同步的**：视频处理如果用 threading/subprocess，可扩展性差。
- **结论**：以 FB-SE 的 FastAPI 为骨架，吸收 DVA 模块。

### ADR-003：为什么 faster-whisper 替代 openai-whisper？

- **性能**：faster-whisper 用 CTranslate2，比 openai-whisper 快 3-4 倍，模型更小（int8 量化）。
- **功能**：支持 VAD 过滤、条件生成、CUDA 加速。
- **兼容性**：两者输出格式一致（segments + full_text）。
- **结论**：统一使用 faster-whisper，保留 OpenAI API 作为云端备选。

### ADR-004：文件存储为什么先不用 MinIO？

- **阶段一目标是最小可行整合**，不是基础设施升级。
- Docker Volume 足够支撑 3-5 人团队的文件量（预估 < 100GB/月）。
- **结论**：阶段一用共享卷，阶段二再评估 MinIO。

---

## 附录 A：技术债务清理清单

### Dake-Video-Auto
- [ ] 删除 `app_simple.py`、`app.py`、`app_multi_user.py` 中的硬编码密码 `Boswindor123$%`
- [ ] 删除自研 SQLite 任务队列 `core/task_queue.py`
- [ ] 删除 `openai-whisper` 依赖
- [ ] 删除 `douyin_downloader.py` 等废弃下载器（保留 yt-dlp 通用方案）
- [ ] 删除 `editor.py`、`editor_v2.py`（保留 `editor_advanced.py` 逻辑）
- [ ] 将 `core/` 模块的 `sys.path.insert` 改为相对导入

### Facebook-Script-Extract
- [ ] 删除独立前端 `frontend/`
- [ ] 删除 CLI 入口 `main.py`（或保留为 `scripts/cli.py` 供调试）
- [ ] 将 API Key 认证改为 Service Token 认证
- [ ] 统一错误处理格式（与 NestJS 的 `ApiException` 对齐）

### Operation_Manage
- [ ] 无重大技术债务，主要工作是增量扩展
