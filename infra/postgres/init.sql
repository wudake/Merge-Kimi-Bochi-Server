-- ─────────────────────────────────────────────────────────────────────────────
-- PostgreSQL 初始化脚本
-- 仅在 postgres_data volume 首次创建时执行(由 docker-entrypoint-initdb.d 自动调用)
--
-- 默认通过 docker-compose 的 POSTGRES_DB=opman 已创建主数据库
-- 这里只追加一些扩展和预留 schema
-- ─────────────────────────────────────────────────────────────────────────────

\c opman

-- 启用常用扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 预留 schema(后续如需要跨项目元数据可使用)
-- CREATE SCHEMA IF NOT EXISTS shared_metadata;

-- 注:OPMan 自身的表由 Prisma migration 创建(在 opman_api 容器启动时执行)
-- 这个脚本不要管理具体表结构,仅做扩展和 schema 准备
