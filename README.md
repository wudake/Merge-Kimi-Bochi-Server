# Boswindor 整合控制台

三个核心项目共用一套基础设施与统一入口的轻量整合方案。

| 模块 | 路径 | 技术栈 | 职责 |
|------|------|--------|------|
| 运营管理 | `/op/` | NestJS + React | 账号管理、内容日历、选题库、数据看板 |
| 脚本提取 | `/fbse/` | FastAPI + Celery | Facebook / YouTube / Ads Library 视频转文字 |
| 视频自动化 | `/dva/` | Flask + FFmpeg | 视频下载、AI 配音、智能剪辑、9:16 适配 |

---

## 快速开始

```bash
# 1. 复制环境变量
cp .env.example .env
# 编辑 .env: 设置 MAIN_DOMAIN、PG_PASSWORD、JWT_SECRET、OPENAI_API_KEY(可选)

# 2. 申请 SSL 证书并放到 nginx/ssl/
#    fullchain.pem + privkey.pem

# 3. 启动全部服务
docker compose up -d --build

# 4. 验证
docker compose ps
docker compose logs -f nginx opman_api fbse_backend dva_app
```

---

## 目录结构

```
.
├── docker-compose.yml      # 全系统编排,按 Phase 逐步启用服务
├── .env.example            # 环境变量模板
├── docs/
│   └── 轻量整合设计.md     # 完整架构设计文档
├── infra/
│   ├── postgres/
│   │   └── init.sql        # PG 初始化 (uuid-ossp, pgcrypto)
│   └── migrations/         # 跨项目数据迁移脚本 (Phase 5)
├── nginx/
│   ├── nginx.conf          # 主配置 (HTTP→HTTPS, TLS, 入口路由)
│   ├── locations/
│   │   ├── op.conf         # /op/ 路由 (Phase 2 启用)
│   │   ├── fbse.conf       # /fbse/ 路由 (Phase 3 启用)
│   │   └── dva.conf        # /dva/ 路由 (Phase 4 启用)
│   └── ssl/                # SSL 证书挂载目录
├── portal/
│   ├── index.html          # 统一入口页 (三模块卡片 + 登录态检测)
│   └── assets/style.css    # Portal 样式
└── projects/
    ├── Operation_Manage/     # git submodule (NestJS+React)
    ├── Facebook-Script-Extract/ # git submodule (FastAPI+Celery)
    └── Dake-Video-Auto/      # git submodule (Flask+FFmpeg)
```

---

## 实施路线图

| Phase | 内容 | 工期 | 状态 |
|-------|------|------|------|
| 1 | 基础设施 (postgres, redis, nginx, portal 骨架) | 0.5 天 | **已完成** |
| 2 | Operation_Manage 接入 + SSO 打通 | 1.5 天 | **已完成** |
| 3 | Facebook-Script-Extract 接入 | 2 天 | **已完成** |
| 4 | Dake-Video-Auto 接入 | 3~4 天 | **已完成** |
| 5 | 数据迁移 + 联调 + Portal 完善 + 测试验证 | 2 天 | **已完成** |
| 6 | 域名切换 + 线上观察 | 1 天 | **待用户操作** |

> 详见 `docs/轻量整合设计.md` 第 11 节。

---

## Release V1.0.0 (2026-05-10)

**整合完成标记**：三项目已完成 SSO 鉴权打通、子路径部署、共享基础设施配置，并通过单元测试与构建验证。

### 测试验证结果
- **OPMan 后端**：84/84 通过
- **OPMan 前端**：Vite 生产构建通过 (`base: '/op/'`)
- **FB-SE 后端**：180/183 通过（3 个预存失败与整合无关）
- **FB-SE 前端**：Vite 生产构建通过 (`base: '/fbse/'`)
- **DVA 鉴权层**：新增 8 个集成测试全部通过

### 关键改造摘要
- **SSO 统一鉴权**：OPMan JWT 签发 → Nginx `auth_request` → 子项目 `X-User-Id` / `X-User-Role` header
- **子路径部署**：`/op/`、`/fbse/`、`/dva/` 独立运行，互不影响
- **Redis 隔离**：DB 0=OPMan, DB 1=FB-SE, DB 2=DVA 预留
- **移除硬编码密码**：FB-SE 移除 API_KEY，DVA 移除 USERS 字典

---

## 上线前准备 (用户侧)

1. **DNS**: 添加 A 记录 `app.<你的主域名>` → 服务器 IP
2. **SSL**: 在服务器上通过 acme.sh 或 certbot 申请 `app.<你的主域名>` 证书,放到 `nginx/ssl/`
3. **MAIN_DOMAIN**: 将 `.env` 中的 `MAIN_DOMAIN` 改为实际域名
4. **防火墙**: 开放 80/443,关闭其他端口的外网访问

---

## 技术要点

- **统一鉴权**: Operation_Manage 的 JWT 作为 SSO 唯一签发源,Nginx `auth_request` 代理验证,子项目通过 `X-User-Id` / `X-User-Role` 头获取身份。
- **共享基础设施**: PostgreSQL 16 + Redis 7,FB-SE 用 Redis DB 1,DVA 预留 DB 2。
- **子路径部署**: 每个项目改造为在 `/op/`、`/fbse/`、`/dva/` 下运行,前端 Vite `base` + 后端路径前缀适配。
