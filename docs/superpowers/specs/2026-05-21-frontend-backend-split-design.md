# 宠物花费管理系统 — 前后端拆分与后端接入设计

- 日期：2026-05-21
- 项目：pet_cost
- 作者：tong.jia + Claude
- 状态：已通过 brainstorming，待生成实施计划

---

## 1. 背景与目标

当前 `pet_cost` 仓库是一个纯前端 Vue 3 + Vite 应用，数据存于浏览器 localStorage。
要将其改造为前后端分离的**宠物店/医院后台管理系统**，由管理员管理「客户（宠主） → 宠物 → 花费」三层数据。

### 业务场景
- 后台系统，**不对终端用户开放**，仅管理员使用
- 单台机器或内网部署，**v1 不需要登录鉴权**
- 数据模型：客户（宠主）→ 宠物 → 花费记录

### 推进路径
**先重组 + 后端骨架 + 增量替换**：
1. 把现有代码挪入 `frontend/`，新建 `backend/` 起 FastAPI 空骨架
2. 后端补齐数据模型、CRUD API、统计 API、seed 数据
3. 前端分两步改：先加「客户管理」相关页面，再把 CostList/Stats/Settings 接到后端

每一步都有可运行成果，可暂停、可回滚。

### 技术栈
| 层 | 选择 |
|---|---|
| 前端 | Vue 3 + Vite + Pinia + Vue Router + Element Plus + ECharts（保留现有依赖） |
| 后端 | Python + FastAPI + SQLAlchemy 2.x + Alembic |
| 数据库 | MySQL 8（目标）；开发期先用 SQLite 文件做 mock |
| 后端包管理 | `uv` |

---

## 2. 仓库结构

```
pet_cost/
├── frontend/                    # 现有前端代码全部下沉到此
│   ├── src/
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.development         # VITE_API_BASE_URL=http://127.0.0.1:8000
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口（注册路由、CORS、异常处理）
│   │   ├── core/
│   │   │   ├── config.py        # 读取 .env：DATABASE_URL、CORS_ORIGINS 等
│   │   │   └── database.py      # SQLAlchemy engine、SessionLocal、get_db 依赖
│   │   ├── models/              # SQLAlchemy ORM
│   │   │   ├── __init__.py
│   │   │   ├── customer.py
│   │   │   ├── pet.py
│   │   │   ├── cost.py
│   │   │   └── category.py
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   │   ├── customer.py
│   │   │   ├── pet.py
│   │   │   ├── cost.py
│   │   │   ├── category.py
│   │   │   └── common.py        # 分页响应、错误响应等通用 schema
│   │   ├── api/v1/              # 路由层
│   │   │   ├── customers.py
│   │   │   ├── pets.py
│   │   │   ├── costs.py
│   │   │   ├── categories.py
│   │   │   └── stats.py
│   │   ├── crud/                # 数据库操作层
│   │   │   ├── customer.py
│   │   │   ├── pet.py
│   │   │   ├── cost.py
│   │   │   └── category.py
│   │   └── seed.py              # 命令行运行的假数据填充
│   ├── alembic/                 # 数据库迁移
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── api/
│   │   │   ├── test_customers.py
│   │   │   ├── test_pets.py
│   │   │   ├── test_costs.py
│   │   │   └── test_categories.py
│   │   └── test_stats.py
│   ├── pyproject.toml           # uv 管理依赖
│   ├── .env.example
│   └── README.md
│
├── docs/
│   └── superpowers/specs/...
│
├── .gitignore                   # 顶层补充后端忽略项
└── README.md                    # 顶层快速启动 + 目录说明
```

### 顶层 README 必须包含
- 项目一句话简介
- 技术栈表
- 「快速启动」段（前后端分别 5 行命令）
- 目录结构图
- 链接到 `backend/README.md`

### 顶层 `.gitignore` 补充项
```
# 后端
backend/.env
backend/__pycache__/
backend/.venv/
backend/.pytest_cache/
backend/dev.db
backend/*.db-journal
```

---

## 3. 数据模型

四张表，关系：**Customer 1—N Pet 1—N CostRecord**；`CostCategory` 是字典表，被 `CostRecord.category_code` 软引用。

> 所有 ORM 模型按 **MySQL 8** 方言编写：显式字段长度、`charset=utf8mb4 collate=utf8mb4_unicode_ci`、显式外键约束。SQLite 只是开发期跑得起来的替身。

### 3.1 `customers` 客户/宠主
| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | BIGINT | PK, AUTO_INCREMENT | |
| name | VARCHAR(50) | NOT NULL | 宠主姓名 |
| phone | VARCHAR(20) | NULL | 手机号；普通索引；唯一性走应用层 |
| note | TEXT | NULL | 备注 |
| created_at | DATETIME | NOT NULL, default CURRENT_TIMESTAMP | |
| updated_at | DATETIME | NOT NULL, ON UPDATE CURRENT_TIMESTAMP | |

索引：`INDEX idx_customers_phone (phone)`、`INDEX idx_customers_name (name)`。

**应用层校验**：POST/PATCH 时若 `phone` 非空且数据库已存在另一条相同 phone 的记录，返回 `409 Conflict`，body：`{"detail": "phone_exists", "existing_id": 12}`。前端弹「已存在该手机号客户，是否查看？」。

### 3.2 `pets` 宠物
| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | BIGINT | PK, AUTO_INCREMENT | |
| customer_id | BIGINT | NOT NULL, FK → customers.id ON DELETE CASCADE | |
| name | VARCHAR(50) | NOT NULL | |
| species | VARCHAR(20) | NULL | "dog" / "cat" / "other" |
| breed | VARCHAR(50) | NULL | |
| gender | VARCHAR(10) | NULL | "male" / "female" / "unknown" |
| birthday | DATE | NULL | |
| note | TEXT | NULL | |
| created_at, updated_at | DATETIME | 同上 | |

索引：`INDEX idx_pets_customer (customer_id)`。

> `species` / `gender` 用字符串而非枚举类型，迁移成本低；前端用常量数组渲染下拉。

### 3.3 `cost_records` 花费记录
| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | BIGINT | PK, AUTO_INCREMENT | |
| pet_id | BIGINT | NOT NULL, FK → pets.id ON DELETE CASCADE | |
| category_code | VARCHAR(30) | NOT NULL | 软引用 `cost_categories.code` |
| amount | DECIMAL(10,2) | NOT NULL | 金额，元 |
| occurred_on | DATE | NOT NULL | 花费发生日期 |
| note | TEXT | NULL | |
| created_at, updated_at | DATETIME | 同上 | |

索引：
- `INDEX idx_costs_pet_date (pet_id, occurred_on DESC)` —— 列表查询主索引
- `INDEX idx_costs_category (category_code)`
- `INDEX idx_costs_occurred (occurred_on)` —— 跨宠物时间窗统计

### 3.4 `cost_categories` 花费分类字典
| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| code | VARCHAR(30) | PK | 'food' / 'medical' / 'grooming' / 'toy' / 'other' |
| label | VARCHAR(30) | NOT NULL | 显示名 |
| sort_order | INT | NOT NULL, default 0 | 排序 |

### 3.5 关键设计取舍

| 取舍 | 理由 |
|---|---|
| 金额用 `DECIMAL(10,2)`，不用 float | 钱不能有浮点误差 |
| `occurred_on` 用 `DATE`，不用 `DATETIME` | 用户只填「哪天」，时分秒无意义 |
| `category_code` 软引用字典表（不加 FK） | 字典 code 改名时不牵连历史记录；改用应用层校验 |
| `ON DELETE CASCADE`，不做软删除 | 单管理员后台，硬删够用，省一层逻辑 |
| `species` 用字符串非枚举 | 加新值不需要迁移 |

---

## 4. 后端 API

REST 风格，全部前缀 `/api/v1`。错误响应沿用 FastAPI 默认 `{"detail": "..."}`，部分场景 detail 可为对象（如 phone 冲突）。

### 4.1 通用响应

**分页响应统一格式**：
```json
{ "items": [...], "total": 123, "page": 1, "page_size": 20 }
```

**分页查询参数**：`page`（默认 1）、`page_size`（默认 20，最大 100）。

### 4.2 客户 `/customers`
| Method | Path | 说明 |
|---|---|---|
| GET | `/customers?q=&page=&page_size=` | 列表，`q` 模糊搜 name/phone |
| GET | `/customers/{id}` | 详情；响应附带 `pets: [...]` |
| POST | `/customers` | 新增；phone 冲突 → 409 |
| PATCH | `/customers/{id}` | 局部更新；phone 冲突 → 409 |
| DELETE | `/customers/{id}` | 删除（级联删宠物和花费） |

### 4.3 宠物 `/pets`
| Method | Path | 说明 |
|---|---|---|
| GET | `/pets?customer_id=` | 不传则返回全部；支持分页 |
| GET | `/pets/{id}` | |
| POST | `/pets` | body 必带 `customer_id` |
| PATCH | `/pets/{id}` | |
| DELETE | `/pets/{id}` | 级联删花费 |

### 4.4 花费 `/costs`
| Method | Path | 说明 |
|---|---|---|
| GET | `/costs?pet_id=&customer_id=&category=&start=&end=&page=&page_size=` | 多维筛选 |
| GET | `/costs/{id}` | |
| POST | `/costs` | body 必带 `pet_id`、`category_code`、`amount`、`occurred_on` |
| PATCH | `/costs/{id}` | |
| DELETE | `/costs/{id}` | |

### 4.5 分类字典 `/categories`
| Method | Path | 说明 |
|---|---|---|
| GET | `/categories` | 列表（按 sort_order） |
| POST | `/categories` | code 冲突 → 409 |
| PATCH | `/categories/{code}` | 只能改 label/sort_order；code 不可变 |
| DELETE | `/categories/{code}` | 若有花费记录引用 → 409 |

### 4.6 统计 `/stats`
| Method | Path | 响应示例 |
|---|---|---|
| GET | `/stats/summary?start=&end=` | `{"total_amount": "1234.56", "record_count": 42, "customer_count": 3, "pet_count": 5}` |
| GET | `/stats/by-category?start=&end=` | `[{"category": "food", "label": "粮食", "total": "...", "count": 10}]` |
| GET | `/stats/by-month?start=&end=` | `[{"month": "2026-05", "total": "..."}]` |
| GET | `/stats/by-pet?customer_id=&limit=&start=&end=` | `[{"pet_id": 1, "pet_name": "毛毛", "total": "..."}]` Top N |

时间窗参数说明：
- `start`、`end` 都是 `YYYY-MM-DD` 字符串
- 不传时默认查全部历史
- 包含端点：`occurred_on >= start AND occurred_on <= end`

### 4.7 错误码约定
| 状态码 | 场景 |
|---|---|
| 404 | 资源不存在 |
| 422 | FastAPI 请求体校验失败（自动） |
| 409 | 业务冲突：phone 重复、category code 重复、删除被引用的字典项 |
| 500 | 兜底 |

### 4.8 CORS
开发期允许 `http://127.0.0.1:3000` 和 `http://localhost:3000`。配置项放 `core/config.py`，读 `CORS_ORIGINS` env。

### 4.9 OpenAPI
FastAPI 自动生成；前端开发期可访问 `http://127.0.0.1:8000/docs`。

---

## 5. 前端改造

整体保留 Vue 3 + Pinia + Element Plus + ECharts，只换数据来源（localStorage → API）和加一层「客户」概念。

### 5.1 路由结构（新）

| 路径 | 视图 | 说明 |
|---|---|---|
| `/` | redirect → `/customers` | |
| `/customers` | CustomerList | 客户列表（搜索 + 分页 + 新增） |
| `/customers/:id` | CustomerDetail | 客户基本信息 + 名下宠物列表 |
| `/pets/:id` | PetDetail | 宠物基本信息 + 该宠物的花费列表 |
| `/costs` | CostList | 全部花费总览，多维筛选 |
| `/stats` | Stats | 统计图表 |
| `/settings` | Settings | 分类字典管理 |

> 旧 `home`、单一花费视图取消；首页 = 客户列表。

### 5.2 `frontend/src/` 目录布局

```
src/
├── api/
│   ├── http.js                 # axios 实例：baseURL、错误拦截、loading
│   ├── customers.js
│   ├── pets.js
│   ├── costs.js
│   ├── categories.js
│   └── stats.js
├── stores/
│   ├── customerStore.js        # 列表、筛选、当前选中
│   ├── petStore.js
│   ├── costStore.js            # 重写：去掉 localStorage
│   └── categoryStore.js        # 字典本地缓存（少请求）
├── views/
│   ├── customers/
│   │   ├── CustomerList.vue
│   │   └── CustomerDetail.vue
│   ├── pets/
│   │   └── PetDetail.vue
│   ├── costs/
│   │   ├── CostList.vue
│   │   └── CostFormDialog.vue  # 抽出复用：客户→宠物级联选择 + 花费字段
│   ├── Stats.vue               # 重写：调 /stats/*
│   └── Settings.vue            # 重写：管字典表
├── components/                 # 通用组件
├── router/index.js
├── App.vue
└── main.js
```

### 5.3 关键改造点

- **`api/http.js`**：axios 实例统一处理：
  - `baseURL` 来自 `import.meta.env.VITE_API_BASE_URL`
  - 响应拦截：4xx/5xx 弹 `ElMessage.error(detail)`，409 + phone_exists 特殊处理（弹确认框引导查看已存在客户）
  - 请求/响应 loading（可选，看是否影响体验）

- **Pinia store 不再持有全量数据**，只保留：
  - 当前列表 items + total + page
  - 当前筛选条件
  - 当前选中 detail
  - 翻页/筛选都重新请求

- **CostList 录入对话框**：必须先选「客户 → 宠物」级联选择器，再填分类/金额/日期。从 PetDetail 进入时客户/宠物默认填好。

- **Stats 页**：图表数据完全来自后端聚合接口，前端不再本地算 sum/group。时间窗 + 客户/宠物筛选作为统一筛选条。

- **Settings 页**：表格列出字典所有条目，每行操作真正调网络。

### 5.4 不变的部分
- 依赖：Element Plus、ECharts、Vue Router、Pinia、SASS
- 整体视觉风格保留（沿用前几次提交雕的样式）

---

## 6. 开发流程

### 6.1 启动两个服务

```bash
# Terminal 1 —— 后端
cd backend
uv sync
cp .env.example .env            # 编辑 DATABASE_URL（开发期默认 sqlite:///./dev.db）
uv run alembic upgrade head     # 建表
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 —— 前端
cd frontend
npm install
npm run dev                     # 跑在 127.0.0.1:3000
```

### 6.2 数据库

- **目标生产**：MySQL 8
- **开发 mock**：SQLite 文件（`backend/dev.db`），git 忽略
- **切换方式**：改 `backend/.env` 的 `DATABASE_URL`：
  - 开发：`sqlite:///./dev.db`
  - 生产：`mysql+pymysql://user:pass@host/pet_cost?charset=utf8mb4`

**Mock 边界（必须文档化）**：
- SQLite 不严格区分 varchar 长度
- SQLite 默认外键约束不生效（需开启 `PRAGMA foreign_keys=ON`）
- 并发能力有限，但开发够用
- 所有 ORM 模型 / 迁移按 MySQL 8 写，SQLite 只是替身。切换到真 MySQL 时跑 `alembic upgrade head` 即可。

**Alembic 配置要点**：
- `env.py` 里 dialect 不锁死（按 URL 推断），但 autogenerate 时建议开发者临时把 URL 指向 MySQL 实例生成迁移，避免 SQLite 推断丢失字段细节。
- 这条作为 README 提示，不是强制约束，因为 v1 还没有真 MySQL。

### 6.3 假数据 seed

`backend/app/seed.py` 提供命令：
```bash
uv run python -m app.seed
```

行为：**幂等**，每次先清空三张主表再重新插入。规模：
- 3 个客户
- 每个客户 1-2 只宠物
- 每只宠物 8-15 条花费记录，跨过去半年，覆盖各分类

> 不在 FastAPI 启动时自动 seed —— 启动逻辑保持纯净，seed 是开发工具。

字典表 `cost_categories` 通过 **Alembic 迁移**插入初始数据（不属于 seed 工具的范畴）：`food` / `medical` / `grooming` / `toy` / `other`。

### 6.4 数据库迁移

每次改 ORM 模型：
```bash
uv run alembic revision --autogenerate -m "add xxx"
uv run alembic upgrade head
```

**v1 不允许使用 `Base.metadata.create_all()`**，全部走 Alembic。

---

## 7. 测试策略

### 7.1 后端（pytest）

只测三类东西：

1. **API 集成测试** `tests/api/test_*.py`
   - FastAPI `TestClient`
   - 每个测试独立 SQLite 内存库（`sqlite:///:memory:`）+ override `get_db` 依赖
   - 覆盖：CRUD 主路径、级联删除、404、422、phone 重复 409、删除被引用的分类 409

2. **统计聚合测试** `tests/test_stats.py`
   - 准备 fixture 数据，断言四种聚合输出
   - 重点测：时间窗边界、空分组、金额累加精度

3. **迁移健康检查**（一个测试就够）
   - 起空 SQLite，跑 `alembic upgrade head` 不报错
   - ORM `metadata` 与迁移后 schema 一致

**不测**：单条 CRUD 函数（被集成测试覆盖）、Pydantic 校验（FastAPI 已测过）。

### 7.2 前端

**v1 不写自动化测试**，靠手测 + ESLint。理由：
- 单管理员后台，UI 行为稳定
- 跑一遍主流程比写 E2E 投入小
- 真出问题再补针对性测试

留 `frontend/test/` 占位目录和 README，标明「未来用 Vitest 加测试」。

### 7.3 手测清单

写进顶层或 frontend README，每次大改后过：
- [ ] 客户列表搜索、分页、新增、编辑、删除
- [ ] 客户详情看到名下宠物
- [ ] 宠物详情看到花费列表，能新增/编辑/删除花费
- [ ] 跨客户 `/costs` 页面的多维筛选
- [ ] 删客户能级联删宠物和花费（去 DB 确认）
- [ ] Stats 四种聚合视图都有数据，时间窗筛选生效
- [ ] Settings 改类别名后 Stats 显示同步
- [ ] Settings 删除有引用的类别被拒（前端弹 409 提示）

---

## 8. 不在本 spec 范围内

明确**不做**的事，避免实施时跑偏：

- 用户登录 / 鉴权 / 角色（v1 完全开放）
- Docker / docker-compose 配置（v1 不需要）
- 生产部署脚本、CI/CD（之后单独立项）
- 真实接入 MySQL（v1 用 SQLite mock）
- 前端单元/E2E 测试
- 多语言、暗色模式
- 软删除、审计日志、操作记录
- 文件上传（宠物头像等）
- 报表导出（CSV/Excel）

---

## 9. 实施分期

按推进路径 A 拆分，每期独立可运行：

**Phase 1 — 仓库重组**
- 现有前端代码挪入 `frontend/`
- 新建 `backend/` 空骨架（FastAPI hello world、`/health` 端点、`uv` 配置）
- 顶层 README、.gitignore 更新
- 验收：两个服务都能起来

**Phase 2 — 后端核心**
- ORM 模型（4 张表）+ Alembic 初始迁移（含字典初始数据）
- CRUD + Schema + 路由：customers / pets / costs / categories
- 统计接口 4 个
- seed 工具
- 后端测试
- 验收：`/docs` 页能完整跑一轮 CRUD + 统计

**Phase 3 — 前端整合**
- `api/` 客户端、`http.js` 拦截器
- 客户管理新页面（CustomerList / CustomerDetail）
- PetDetail 页面
- CostList 改造：去 localStorage、加级联选择
- Stats 改造：调后端聚合接口
- Settings 改造：管字典表
- 路由调整 + 旧路由清理
- 手测清单走一遍
- 验收：所有手测项通过

每个 Phase 结束都是一次 commit/PR。

---

## 附：决策清单（实施时不需再问）

| 决策 | 选择 |
|---|---|
| 仓库布局 | 同一 repo，frontend/ + backend/ |
| 后端栈 | Python + FastAPI + SQLAlchemy 2.x + Alembic |
| 后端包管理 | uv |
| 数据库（生产） | MySQL 8 |
| 数据库（开发） | SQLite 文件 mock |
| 鉴权 | 不做 |
| 业务模型 | Customer 1—N Pet 1—N CostRecord，CostCategory 字典 |
| phone 唯一性 | 应用层校验，DB 层只建普通索引 |
| 删除策略 | 硬删 + ON DELETE CASCADE |
| 金额类型 | DECIMAL(10,2) |
| 分类管理 | 字典表 + 软引用 |
| 前端测试 | v1 不做 |
| 启动方式 | 两个 terminal 手动起 |
| Seed | 命令行触发，幂等 |
