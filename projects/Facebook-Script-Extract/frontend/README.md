# Frontend — Video Script Extractor

React 19 + TypeScript + Vite 8 + TailwindCSS v3 单页应用，是 Video Script Extractor 团队版的 Web 入口。

> 完整的安装与部署说明请见仓库根目录的 [README.md](../README.md) 与 [docs/INSTALL.md](../docs/INSTALL.md)。

## 快速开始

```bash
# 1. 安装依赖
npm install

# 2. 配置登录凭据（构建期注入）
cp .env.example .env.local
# 编辑 .env.local：填入 VITE_ADMIN_USERNAME / VITE_ADMIN_PASSWORD

# 3. 启动开发服务器（默认 http://localhost:5173）
npm run dev
```

`vite.config.ts` 已经把 `/api` 和 `/ws` 代理到 `http://localhost:8000`，开发时无需关心跨域，确保后端在该端口运行即可。

## 常用脚本

| 命令 | 说明 |
|------|------|
| `npm run dev`     | 启动 Vite 开发服务器（HMR） |
| `npm run build`   | 类型检查 + 生产构建到 `dist/` |
| `npm run preview` | 本地预览生产构建结果 |
| `npm run lint`    | 跑 ESLint |

## 目录结构

```
src/
├── api/client.ts                 Axios 客户端 + 类型定义
├── components/
│   ├── Layout.tsx                导航 + 路由出口
│   └── ProtectedRoute.tsx        登录门控
├── hooks/useWebSocket.ts         WebSocket Hook
├── pages/
│   ├── LoginPage.tsx             登录页
│   ├── SubmitPage.tsx            新建任务
│   ├── TasksPage.tsx             任务列表
│   ├── TaskDetailPage.tsx        任务详情
│   ├── CompletedScriptsPage.tsx  已完成脚本聚合
│   └── SettingsPage.tsx          API Key 设置
├── utils/
│   ├── auth.ts                   登录态管理（localStorage，7 天）
│   └── validation.ts             URL 校验
├── App.tsx                       路由
├── main.tsx                      React 入口
└── index.css                     Tailwind 入口
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `VITE_ADMIN_USERNAME` | ✅ | 登录用户名 |
| `VITE_ADMIN_PASSWORD` | ✅ | 登录密码 |
| `VITE_API_BASE_URL`   |    | 跨域部署时指向后端绝对地址，同域留空即可 |

> Vite 在构建期把 `VITE_*` 变量内联到 JS bundle，所以 **改 `.env.local` 后必须重启 dev server 或重新 `npm run build`** 才会生效。
