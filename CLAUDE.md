# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

宠物店管理系统（前后端分离）。核心业务模型三层级联：
**Customer（会员）→ Pet（宠物）→ Cost（服务订单流水）**，外加 `CostCategory`（服务项目字典）和 `Budget`（支持全店/单宠物/分项目三种粒度）。

栈：Vue 3 + Vite + Pinia + Element Plus（前端） / FastAPI + SQLAlchemy 2.x + Alembic（后端） / SQLite（开发）+ MySQL 8（生产）。

## 常用命令

### 后端（位于 `backend/`，包管理用 `uv`）

```bash
uv sync                                      # 安装依赖
uv run alembic upgrade head                  # 跑迁移建表
uv run python -m app.seed                    # 灌假数据（会清空 customer/pet/cost，不动分类字典）
uv run uvicorn app.main:app --reload --port 8000   # 启动，访问 /docs
uv run pytest                                # 跑全部测试
uv run pytest tests/test_costs.py::test_xx   # 跑单个用例
uv run alembic revision --autogenerate -m "xxx"    # 改 ORM 后生成迁移
uv run alembic downgrade -1                  # 回滚一格
```

### 前端（位于 `frontend/`，用 npm）

```bash
npm install
npm run dev                                  # 起开发服 http://127.0.0.1:3000
npm run build                                # 生产构建（提交前必跑，CONTRIBUTING 强制）
```

### 提交前的硬性自测（CONTRIBUTING.md 规定）

1. 后端：`uv run pytest` 全过
2. 前端：`npm run build` 无报错
3. 冒烟主流程：创建客户 → 创建宠物 → 创建服务订单 → 营业概览数据正确 → 经营预算计算正确

## 代码架构

### 后端分层（`backend/app/`）

请求路径：`api/v1/*.py`（路由 + HTTP 校验）→ `crud/*.py`（DB 操作）→ `models/*.py`（ORM）。
`schemas/*.py` 是 Pydantic v2 请求/响应模型，所有路由统一通过 `_validate_refs` 类的辅助函数做外键存在性校验，再下沉到 crud。

- 路由全部在 `app/main.py` 里集中挂载到 `/api/v1` 前缀
- `core/config.py`：环境配置（`DATABASE_URL`、`CORS_ORIGINS`），从 `.env` 读
- `core/exceptions.py`：自定义 `ConflictError` → 409，统一异常 handler 在 main.py
- `crud/budget.py` 返回 dict（不是 ORM 对象），含 `used`/`remaining`/`usage_rate`/`is_over` 等聚合字段
- `crud/cost.py` 列表查询联表 Pet 注入 `pet_name`，前端依赖此字段
- 测试用内存 SQLite，不影响 `dev.db`

### 前端分层（`frontend/src/`）

- `api/*.js`：每个资源一个 axios 模块，统一走 `http.js` 的 axios 实例
- `stores/*.js`：Pinia store，持有列表/分页/loading 状态
- `views/`：页面组件，命名按业务而非数据模型（`bills/` = 服务订单流水、`categories/` = 服务项目，业务术语和后端字段不一致）
- `router/`：菜单 `meta.title` 是浏览器标签页标题来源
- `style.css`：全局设计变量（颜色、间距、圆角），CONTRIBUTING 禁止硬编码样式值

Vite 别名 `@` → `src/`。

### 字段命名约定（重要）

**前后端字段全部 snake_case 对齐**（`pet_id`、`category_code`、`occurred_on`、`total_amount`、`last_visit_at` 等）。v2 已经把前端历史的 camelCase 全部改掉，新代码不要再写 `petId`/`categoryCode`。

`categoryStore` 同时暴露 `list`/`fetch` 主接口和 `categories`/`fetchCategories` 别名，是为了兼容旧调用，新代码用主接口即可。

### 数据库注意事项

- 开发 SQLite 已强制 `PRAGMA foreign_keys=ON`
- 所有 ORM 和迁移按 MySQL 8 标准写，切换只改 `DATABASE_URL`
- 分类字典用业务 `code` 做主键（`grooming`/`medical`/`food`/`toy`/`other`/`boarding`/`training`/`retail`），历史 cost 引用旧 code 不删，迁移用 `INSERT WHERE NOT EXISTS` 保证幂等

## Git 工作流

- `dev` 是日常开发分支，`main` 仅在上线后合并，**禁止直接提交到 main**
- 提交信息必须带 emoji 前缀：✨ 新功能 / 🐛 修复 / ♻️ 重构 / 💄 样式 / 📝 文档 / 🔧 配置
- 后端 `uv.lock` 和前端 `package-lock.json` 必须提交，锁版本

## 自驱循环基础设施（`docs/superpowers/`）

仓库挂了两条云端 cron agent：
- **PM cron**：读 `pm/vision.md`，写 `pm/proposals.md`（产品提案，不动代码）
- **Task cron**：读 `task/todo.md`，挑任务实施 → push dev → 满足条件 ff-only 合 main

碰到这俩目录前先读 `docs/superpowers/README.md` 和 `task/policy.md`：
- `task/policy.md` 是 agent 红线，不要随便改
- 暂停整个循环：把 `task/todo.md` frontmatter `enabled` 改 `false`
- 暂停自动合 main：把 `auto_merge_main` 改 `false`
- 设计文档落 `specs/`，实施计划落 `plans/`，两个目录的现有文件**禁止删除**（policy 红线）

人手动开发时不要碰 cron agent 正在处理的任务（看 `task/todo.md` 里 `status: in_progress` 的条目）。

## 一些容易踩的坑

- `crud/cost.py` 列表必须返回 `pet_name`，前端账单页直接展示，删了会报错
- `<el-col>` 的 `span` 用数字绑定要写 `:span="12"`，写字符串 `span="12"` 在新版 Element Plus 下表现异常
- 改 ORM 模型后必须 `alembic revision --autogenerate` 生成迁移，不要手改 schema
- `app.seed` 会清空 customer/pet/cost 表，生产库别跑
