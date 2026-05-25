# DESIGN.md — 宠物店管理系统设计文档

> 本文是面向开发者的系统设计说明，描述「项目长什么样、为什么这么长」。
> 操作命令、提交规范、Git 流程见 `CLAUDE.md` / `CONTRIBUTING.md`，本文不重复。

---

## 1. 项目定位

面向中小型宠物店的业务后台，覆盖**门店日常运营全链路**：

会员档案 → 宠物档案 → 服务订单流水 → 服务项目字典 → 经营预算 → 营业看板

不是 SaaS、不是收银系统、不是会员卡积分平台。核心目标是给单店店长一个能查、能录、能复盘的工具。

技术上前后端完全分离，后端纯 JSON API（FastAPI），前端 SPA（Vue 3 + Vite），DB 开发用 SQLite、生产 MySQL 8。

---

## 2. 领域模型

### 2.1 三层主线

```
Customer (会员/客户)
   └── 1:N ──► Pet (宠物)
                  └── 1:N ──► CostRecord (服务订单/账单流水)
```

- **Customer**：会员档案。一条记录对应现实中一个客户（不是一笔业务）。手机号可空，因为线下场景常常只留姓名。
- **Pet**：客户名下的宠物。`customer_id` 强制非空 + 级联删除（删客户 → 自动删宠物 → 自动删订单），用 ORM `cascade="all, delete-orphan"` + DB 外键 `ON DELETE CASCADE` 双重保证。
- **CostRecord**：每一次服务消费的流水。`pet_id` 关联宠物，`category_code` 关联服务项目字典。前端语境叫「账单 / 服务订单」，DB 字段叫 `cost_records`，命名上的差异是历史遗留，新代码统一按 DB 字段名走。

### 2.2 字典 & 预算

- **CostCategory**：服务项目字典。**主键是业务 `code`**（`grooming` / `medical` / `food` / `toy` / `other` / `boarding` / `training` / `retail`），不是自增 id。这样 cost 表存的是语义化字符串，迁移和导出更稳。删除分类时，历史 cost 记录里旧 code 不动（迁移用 `INSERT WHERE NOT EXISTS` 保证幂等）。
- **Budget**：预算单元。一张表覆盖三种粒度，靠 `(type, target_id)` 区分：
  - `type=global, target_id=null` → 全店总预算
  - `type=pet, target_id=<pet_id 字符串>` → 单宠物预算
  - `type=category, target_id=<category_code>` → 分项目预算

  唯一约束 `uk_budgets_unique(type, target_id, year, month)` 保证「同一目标同一月份」只能有一条预算。`spent`/`remaining`/`overspent` 是查询时实时算出来的（见 `crud/budget.py`），不落库。

### 2.3 拼音检索字段

`Customer` 和 `Pet` 都有 `name_pinyin` / `name_initials` 两个生成字段，用 SQLAlchemy `before_insert` / `before_update` 钩子自动同步（`core/pinyin.py`）。这两列加了独立索引，让全局搜索能命中「lucky」/「ll」这种用户高频输入的拼音/首字母。

---

## 3. 后端架构

### 3.1 分层

```
HTTP 请求
   │
   ▼
api/v1/*.py        ← 路由 + HTTP 校验（path/query 参数、HTTPException）
   │                  请求体由 schemas/ 的 Pydantic v2 模型解析
   ▼
crud/*.py          ← DB 操作。所有 SQL 只在这一层写
   │                  返回 ORM 对象 或 dict（budget 例外，它返回 dict）
   ▼
models/*.py        ← SQLAlchemy 2.x ORM
   │
   ▼
SQLite (dev) / MySQL 8 (prod)
```

**`schemas/` 是 API 契约层**：所有 request/response 都过 Pydantic 模型，路由层不直接吐 ORM 对象。

**外键存在性校验**：放在路由层（如 `costs.py:_validate_refs`），不下沉到 crud。原因是路由层能直接抛 `HTTPException(404)`，crud 层只用 `return None` 表达「找不到」，分层更干净。

### 3.2 路由挂载

`app/main.py` 集中 import 所有路由模块，循环挂到 `/api/v1` 前缀。新加路由模块只需要在 `main.py` 的 import 元组里加一项。

```python
for module in (budgets, categories, costs, customers, pets, search, stats):
    app.include_router(module.router, prefix="/api/v1")
```

### 3.3 API 模块边界

| 模块 | 路径前缀 | 职责 |
|---|---|---|
| `customers.py` | `/api/v1/customers` | 客户 CRUD、详情聚合（CustomerSummary）、最近到店、CSV 导出、xlsx 批量导入（template/preview/commit 三段式） |
| `pets.py` | `/api/v1/pets` | 宠物 CRUD，按 `customer_id` 过滤 |
| `costs.py` | `/api/v1/costs` | 服务订单 CRUD，列表支持 pet/customer/category/日期范围联合过滤，自带 CSV 导出 |
| `categories.py` | `/api/v1/categories` | 服务项目字典 CRUD，主键是 `code` |
| `budgets.py` | `/api/v1/budgets` | 预算 CRUD，按 (year, month) 列出。重复创建返 409 |
| `stats.py` | `/api/v1/stats` | 营业看板聚合：summary / by-category / by-month / by-pet / customer-acquisition / dormant-customers / top-customers |
| `search.py` | `/api/v1/search` | 全局搜索：扫客户 name/phone、宠物 name、消费记录 note，统一返回 `{type, id, title, subtitle, url}` 给前端搜索框用 |

### 3.4 异常处理

- **业务 409**：用自定义 `ConflictError`（`core/exceptions.py`），main.py 注册全局 handler 转 `JSONResponse(status_code=409, content={"detail": ...})`。如手机号重复、预算重复创建。
- **404 / 422**：用 FastAPI 原生 `HTTPException` / 校验机制。
- 前端 `http.js` 拦截器对 409 单独放行（不弹消息条），由业务页面接管处理（如手机号冲突弹引导框）。

### 3.5 数据库注意点

- 开发期 SQLite 在 `core/database.py` 强制开 `PRAGMA foreign_keys=ON`，否则级联不生效。
- ORM 和 Alembic 迁移按 MySQL 8 标准写（`utf8mb4` 字符集、`BigInteger` 主键 `with_variant(Integer, "sqlite")` 兼容）。切换到 MySQL 只改 `DATABASE_URL`。
- 改 ORM 后必须 `alembic revision --autogenerate`，**不要手改 schema**。

---

## 4. 前端架构

### 4.1 分层

```
views/*.vue              ← 页面（按业务命名，不按数据模型）
   │
   ├─► components/*.vue  ← 跨页复用：BillForm / PetForm / CategoryForm / EChart
   │
   ├─► stores/*.js       ← Pinia store：列表/分页/筛选/loading 状态
   │      │
   │      ▼
   │   api/*.js          ← 每资源一个模块，全部走 http.js 的 axios 实例
   │
   └─► router/index.js   ← 哈希路由 + meta.title 驱动浏览器标题
```

Vite 别名 `@` → `src/`，所有组件 import 用 `@/...`。

### 4.2 页面 vs 数据模型的命名差异（重要）

| 路由 / 目录 | 业务名 | 后端资源 |
|---|---|---|
| `/bills`、`views/bills/` | 服务订单 | `cost_records` (`/api/v1/costs`) |
| `/categories`、`views/categories/` | 服务项目 | `cost_categories` (`/api/v1/categories`) |
| `/customers` | 会员/客户 | `customers` |
| `/pets` | 宠物 | `pets` |
| `/budget` | 经营预算 | `budgets` |
| `/dashboard` | 营业概览 | `stats/*` |

**为什么不对齐**：后端字段是历史遗留的中性词（cost / category），前端是直接给店长看的，必须用门店术语。这层「业务术语 ↔ 数据模型」的翻译只在 view 文件名和菜单文案做，API/store/字段名一律保持后端 snake_case。

### 4.3 字段命名约定

**前后端字段全部 `snake_case` 对齐**：`pet_id`、`category_code`、`occurred_on`、`total_amount`、`last_visit_at` …

历史 v1 前端用 camelCase，v2 已经全量改过来，新代码不要再写 `petId`/`categoryCode`，否则跟后端响应对不上。

`categoryStore` 保留了 `categories` / `fetchCategories` 别名指向 `list` / `fetch`，是过渡期兼容老调用，新代码用主接口。

### 4.4 样式规范

- 全局设计变量在 `src/style.css` 的 `:root`：色板（`--primary` 暖橙 `#FFA62B` / `--bg` / `--text-*`）、间距工具类、字体层级。
- Element Plus 组件全局重写圆角、阴影、hover 态，统一 Notion 风格。
- **CONTRIBUTING 强制：禁止硬编码颜色/间距/圆角**。新组件用 `var(--primary)` 不要写 `#FFA62B`。

### 4.5 HTTP 客户端约定

`src/api/http.js`：

- `baseURL` 走 `import.meta.env.VITE_API_BASE_URL`（开发期通常指 `http://127.0.0.1:8000/api/v1`）
- 响应拦截器自动 `return resp.data`，业务代码拿到的就是后端 JSON 主体
- 422 错误把 Pydantic 校验明细拼成可读字符串，统一弹 `ElMessage.error`
- 409 不弹消息条，原样 `reject({ status, detail, raw })`，由业务页面处理（如手机号冲突）

---

## 5. 关键业务流

### 5.1 创建一笔服务订单（核心主流程）

```
店长在前端 BillList → 点「新增」打开 BillForm
   │
   ├─ 选客户：联想搜 /api/v1/customers?q=xxx
   │
   ├─ 选宠物：基于客户 id 拉 /api/v1/pets?customer_id=xx
   │
   ├─ 选服务项目：从 categoryStore（首屏预加载）拿
   │
   └─ 提交 POST /api/v1/costs
         │
         ▼
      路由层 _validate_refs：先验 pet_id / category_code 是否真存在
         │
         ▼
      crud.create：写库
         │
         ▼
      201 + CostOut（含 pet_name —— 列表页要展示）
```

**坑**：`crud/cost.py` 列表查询必须联表 Pet 注入 `pet_name`，前端账单页直接读这个字段，删了会报错。详见 `crud/cost.py:list_paginated` 注释。

### 5.2 营业概览（Dashboard）

聚合 7 个 stats 接口，一次性出：

- **summary**：总营收 / 订单数 / 服务客户数 / 服务宠物数（去重）
- **by-category**：分项目营收占比饼图
- **by-month**：月度营收趋势线图
- **by-pet**：宠物贡献排行
- **customer-acquisition**：当月新客 vs 回头客（口径见 `crud/stats.py:customer_acquisition` 文档字符串）
- **dormant-customers**：≥N 天未到店预警
- **top-customers**：累计消费 Top N

时间窗口靠 `start` / `end` query 参数控制，前端默认本月。**清空日期时要回退到本月，不要传空字符串**（已知坑：空串触发 422，已修，见 commit `3d2c78b`）。

### 5.3 预算计算

`Budget` 表只存元数据（`amount`），`spent`/`remaining`/`overspent` 在 GET 时按 `(type, target_id, year, month)` 实时聚合 cost_records。

- `type=global`：当月全表 sum
- `type=pet`：当月 `pet_id=target_id` sum
- `type=category`：当月 `category_code=target_id` sum

实现在 `crud/budget.py:_calculate_spent`，月末日期处理靠字符串拼接（`2026-12` → `2027-01-01` 作为右开区间），简单但够用。

### 5.4 客户批量导入

三段式 API（`customers.py`）：

1. `GET /import/template` — 下 xlsx 模板（带表头 + 示例 + 说明）
2. `POST /import/preview` — dry-run 解析校验，返回 `{ok, errors, total}`，不写库
3. `POST /import/commit` — 正式写库，**任一行有错就整批 rollback**（原子性）

文件大小限制 2MB（`MAX_IMPORT_BYTES`），门店量级足够。

---

## 6. 测试策略

- **后端**：`pytest` + 内存 SQLite。每个路由模块对应一个 `tests/test_*.py`。覆盖正常路径 + 边界（404 / 409 / 422 / 级联删除 / 拼音同步）。
- **前端**：暂无单元测试，靠 `npm run build` 类型/语法把关 + 手动冒烟。
- **冒烟主流程**（提交前必跑）：
  > 创建客户 → 创建宠物 → 创建服务订单 → 营业概览数据正确 → 经营预算计算正确

---

## 7. 部署形态

| 组件 | 开发 | 生产 |
|---|---|---|
| 前端 | `npm run dev` (Vite, port 3000) | `npm run build` 出 `dist/` 静态资源，nginx/CDN |
| 后端 | `uvicorn --reload` (port 8000) | uvicorn / gunicorn + uvicorn-worker |
| DB | SQLite `dev.db` | MySQL 8 |
| 配置 | `backend/.env` | 环境变量注入 `DATABASE_URL` / `CORS_ORIGINS` |

切环境只改 `DATABASE_URL` 和 `CORS_ORIGINS`，代码不动。详见根目录 `部署文档.md`。

---

## 8. 自驱循环（cron agents）

仓库挂了两条云端 agent，详细规则见 `docs/superpowers/README.md` 和 `task/policy.md`：

- **PM cron**：读 `pm/vision.md` → 写 `pm/proposals.md`（只产提案，不改代码）
- **Task cron**：读 `task/todo.md` → 实施 → push dev → 满足条件 ff-only 合 main

人手开发时**避开 `task/todo.md` 里 `status: in_progress` 的任务**，避免和 cron 抢工作区。
暂停整个循环把 `task/todo.md` frontmatter `enabled` 改 `false`。

---

## 9. 已知约束 & 易踩坑

1. `crud/cost.py` 列表必须返回 `pet_name`，前端账单页强依赖。
2. `<el-col :span="12">` 必须用 `:span` 数字绑定，`span="12"` 字符串在新版 Element Plus 表现异常。
3. SQLite 外键默认关，靠 `core/database.py` 钩子打开，本地直接 `sqlite3` 命令行连进去测时要自己 `PRAGMA foreign_keys=ON`。
4. `app.seed` 会清空 `customer/pet/cost` 三张表，**生产库别跑**。分类字典不会被清。
5. 改 ORM 模型 → 必跑 `alembic revision --autogenerate`，不要手写 schema。
6. `dev` 是日常分支，`main` 仅上线后合并，**禁止直接提交 main**。
7. 后端 `uv.lock` 和前端 `package-lock.json` 必须提交，锁版本。

---

## 10. 文档地图

- `README.md` — 项目门面 + 快速启动
- `CLAUDE.md` — 给 Claude Code session 用的 onboarding 指南（命令 / 架构 / 坑点速查）
- `CONTRIBUTING.md` — 开发规范 + 提交红线
- `DESIGN.md` — 本文（设计说明）
- `部署文档.md` / `功能交付清单.md` — 上线 & 验收
- `docs/superpowers/specs/` — 历史设计 spec
- `docs/superpowers/plans/` — 历史实施计划
- `pm/` / `task/` — cron agent 工作目录
