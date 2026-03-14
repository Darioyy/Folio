-- Folio 数据库初始化脚本
-- 版本: v3.4.x
-- 仅负责创建数据库；所有表结构由 SQLAlchemy ORM（db.create_all）在应用启动时自动创建。
-- 升级已有数据库请执行 backend/migrations/ 下对应的迁移文件。

CREATE DATABASE IF NOT EXISTS folio
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
