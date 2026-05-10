# 门窗工厂社媒运营管理工具

一款面向门窗制造工厂的社交媒体账号与内容运营管理平台，支持多平台账号管理、内容日历、选题库、数据分析等功能。

## 功能特性

- **账号管理** — 管理 TikTok、Instagram、YouTube、Facebook 等多平台社媒账号，支持自定义分组
- **内容日历** — 周视图/月视图双模式的内容排期日历，支持视频预览、状态流转（待制作 → 制作中 → 待发布 → 已发布）
- **选题库** — 视频选题的收集、脚本撰写、拍摄计划管理
- **用户权限** — 基于角色的权限控制（超级管理员 / 经理 / 运营），JWT 认证
- **数据看板** — 账号数据统计、内容产出分析
- **素材管理** — 支持产品素材、工厂素材、安装案例等多分类素材库
- **Excel/PDF 导出** — 内容计划、选题清单等支持导出

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 19 + TypeScript + Vite + Ant Design 5 + Zustand |
| 后端 | NestJS 11 + TypeScript + Prisma ORM |
| 数据库 | PostgreSQL 16 |
| 缓存 | Redis 7 |
| 部署 | Docker + Docker Compose |

## 快速开始

### 环境要求

- Node.js >= 22
- pnpm >= 10
- Docker & Docker Compose（用于数据库）

### 1. 克隆仓库

```bash
git clone https://github.com/wudake/Operation_Manage.git
cd Operation_Manage
```

### 2. 启动数据库

```bash
cd docker
docker-compose up -d
cd ..
```

### 3. 安装依赖

```bash
pnpm install
```

### 4. 初始化数据库

```bash
pnpm db:generate
pnpm db:migrate
pnpm db:seed
```

### 5. 启动开发服务

```bash
# 同时启动前后端
pnpm dev

# 或分别启动
pnpm dev:api   # http://localhost:3000
pnpm dev:web   # http://localhost:5173
```

### 6. 访问系统

- 前端页面: http://localhost:5173
- 后端 API: http://localhost:3000/api/v1
- Swagger 文档: http://localhost:3000/api/docs

**默认管理员账号**: `admin` / `admin123`

## 项目结构

```
Operation_Manage/
├── apps/
│   ├── api/              # NestJS 后端 API
│   │   ├── prisma/       # Prisma schema 与迁移
│   │   ├── src/          # 业务模块（auth, accounts, contents, topics, users）
│   │   └── .env          # 后端环境变量
│   └── web/              # React 前端
│       ├── src/
│       │   ├── api/      # API 请求封装
│       │   ├── pages/    # 页面组件
│       │   ├── layouts/  # 布局组件
│       │   └── stores/   # Zustand 状态管理
│       └── index.html
├── docker/               # Docker Compose 配置
├── package.json          # Monorepo 根配置
└── README.md
```

## 主要模块

| 模块 | 路径 | 说明 |
|------|------|------|
| 认证 | `apps/api/src/modules/auth` | JWT 登录、Token 刷新 |
| 账号管理 | `apps/api/src/modules/accounts` | 社媒账号 CRUD、分组、状态管理 |
| 内容管理 | `apps/api/src/modules/contents` | 内容计划、日历视图、视频预览 |
| 选题库 | `apps/api/src/modules/topics` | 选题收集、脚本、拍摄计划 |
| 用户管理 | `apps/api/src/modules/users` | 员工账号、角色权限 |

## 脚本命令

```bash
# 根目录
pnpm dev              # 同时启动前后端开发服务
pnpm dev:api          # 仅启动后端
pnpm dev:web          # 仅启动前端
pnpm build            # 构建前后端
pnpm db:migrate       # 执行数据库迁移
pnpm db:seed          # 导入种子数据

# 后端目录（apps/api）
pnpm db:generate      # 生成 Prisma Client
pnpm db:studio        # 打开 Prisma Studio
pnpm test             # 运行单元测试
```

## 部署文档

详见 [DEPLOY.md](./DEPLOY.md)。

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-05-02 | 初始版本，包含账号管理、内容日历、选题库、用户权限等核心功能 |

## 许可证

MIT
