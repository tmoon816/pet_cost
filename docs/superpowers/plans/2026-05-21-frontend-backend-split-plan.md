# 宠物花费管理系统 — 前后端拆分实施计划

- 日期：2026-05-21
- 项目：pet_cost
- 关联 spec：[`docs/superpowers/specs/2026-05-21-frontend-backend-split-design.md`](../specs/2026-05-21-frontend-backend-split-design.md)
- 状态：待实施
- 受众：负责具体实施的 agent

---

## 0. 阅读须知

本计划把 spec 落到具体步骤、文件清单、命令和验收标准。**所有设计决策在 spec 第 9 节「附：决策清单」已锁定，实施时不要再改设计**。如发现 spec 缺漏或矛盾，先停下来跟用户确认，再继续。

每个 Phase 结束都对应一次 commit，commit message 用 spec 既有的 emoji + 短语风格（参考 `git log` 最近提交）。

### 起点状态（已确认）

- 仓库根：`/Users/tong.jia/Desktop/tmoon_github/pet_cost`
- 当前分支：`main`，工作树干净
- 已有结构：根目录直接放着 `src/`、`public/`、`index.html`、`package.json`、`vite.config.js`，是纯前端 Vite 项目
- 现有视图：`src/views/` 只有 `CostList.vue`、`Settings.vue`、`Stats.vue` 三个；store 只有 `costStore.js`（基于 localStorage）
- vite dev server 已固定 `127.0.0.1:3000`（见 `vite.config.js`）
- 依赖中已有 axios、Element Plus、ECharts、Pinia、Vue Router；前端不需要额外装包

### 不在本计划范围

详见 spec 第 8 节，重点重申：**v1 不做鉴权、不做 Docker、不做生产部署、不真接 MySQL、不写前端自动化测试**。

---

## 1. Phase 1 — 仓库重组与后端骨架

**目标**：把现有前端代码下沉到 `frontend/`，新建 `backend/` 起一个空的 FastAPI 服务，两端各自能独立跑起来。

### 1.1 步骤

1. **移动现有前端到 `frontend/`**
   用 `git mv` 保留历史。需要移动的条目（基于当前根目录）：
   - `src/` → `frontend/src/`
   - `public/` → `frontend/public/`
   - `index.html` → `frontend/index.html`
   - `package.json` → `frontend/package.json`
   - `package-lock.json` → `frontend/package-lock.json`
   - `vite.config.js` → `frontend/vite.config.js`
   - `node_modules/` → `frontend/node_modules/`（不进 git，但物理移动方便复用安装结果；如有问题可直接删了重装）

   保留在仓库根的：`docs/`、`README.md`、`.gitignore`、`.vscode/`、`.git/`、`.claude/`。

2. **`vite.config.js` 不需要改内容**
   `@` 别名 `./src` 在 `frontend/` 子目录里依然指向 `frontend/src`，路径相对 vite 配置文件，迁移后语义不变。

3. **新建 `frontend/.env.development`**
   ```
   VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
   ```
   把 `/api/v1` 直接放进 baseURL，前端 `api/*.js` 里只写资源段（`/customers`、`/pets`…），减少重复。

4. **建后端骨架** —— 详细文件清单见 1.2。

5. **更新顶层 `.gitignore`**
   在现有内容末尾追加 spec 第 2 节列出的后端忽略项，再追加一项 `frontend/node_modules`（保险起见，原 `node_modules` 仍生效，但显式更清晰）。

6. **写顶层 `README.md`**
   覆盖现有 README，按 spec 第 2 节要求包含：一句话简介、技术栈表、快速启动（前后端两段命令）、目录结构图、链接到 `backend/README.md`。

7. **`backend/README.md`**
   写后端单独的启动、迁移、seed、测试命令。是给开发者看的，别复制粘贴顶层 README。

### 1.2 后端骨架文件清单

```
backend/
├── pyproject.toml
├── .env.example
├── .python-version           # 可选，写 "3.11"
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── core/
│       ├── __init__.py
│       ├── config.py
│       └── database.py
├── alembic.ini               # Phase 2 才填
└── alembic/                  # Phase 2 才填
```

**`pyproject.toml`** 关键依赖（用 uv 管理）：

- 运行依赖：`fastapi`、`uvicorn[standard]`、`sqlalchemy>=2.0`、`alembic`、`pymysql`、`cryptography`（pymysql 依赖）、`pydantic-settings`、`python-dotenv`
- dev 依赖：`pytest`、`pytest-asyncio`、`httpx`（FastAPI TestClient 用）

`requires-python = ">=3.11"`。

**`app/core/config.py`** 用 `pydantic-settings.BaseSettings`，字段：

- `DATABASE_URL: str = "sqlite:///./dev.db"`
- `CORS_ORIGINS: list[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]`
- `DEBUG: bool = False`

读取顺序：环境变量 → `.env` 文件。

**`app/core/database.py`** 提供：

- `engine`：从 `settings.DATABASE_URL` 创建。**对 SQLite 必须开启外键**：
  ```python
  if settings.DATABASE_URL.startswith("sqlite"):
      from sqlalchemy import event
      @event.listens_for(engine, "connect")
      def _enable_sqlite_fk(dbapi_conn, _):
          dbapi_conn.execute("PRAGMA foreign_keys=ON")
  ```
- `SessionLocal = sessionmaker(...)`
- `Base = declarative_base()`
- `def get_db()`：FastAPI 依赖，yield + finally close

**`app/main.py`** Phase 1 内容（最小可跑）：

- 创建 `FastAPI(title="Pet Cost API", version="0.1.0")`
- 注册 CORS（`allow_origins=settings.CORS_ORIGINS`、`allow_methods=["*"]`、`allow_headers=["*"]`）
- 一个 `GET /health` 返回 `{"status": "ok"}`
- 一个 `GET /` 返回 `{"name": "pet-cost", "version": "0.1.0"}`
- Phase 2 再加 router include 和异常处理

**`.env.example`**：
```
DATABASE_URL=sqlite:///./dev.db
CORS_ORIGINS=["http://127.0.0.1:3000","http://localhost:3000"]
DEBUG=true
```

### 1.3 验收

```bash
# 终端 A
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
# 浏览器打开 http://127.0.0.1:8000/docs，能看到 health 接口

# 终端 B
cd frontend
npm install   # 如果 node_modules 没问题，可跳过
npm run dev
# 浏览器自动开 http://127.0.0.1:3000，旧的 CostList/Stats/Settings 页面照常工作
```

两端都能起来 → Phase 1 完成。Commit。

---

## 2. Phase 2 — 后端核心

**目标**：四张表、CRUD + 统计接口全部就绪，能在 `/docs` 跑完整 CRUD 流程。

### 2.1 实施顺序

按下面顺序写，每完成一段都能跑起来：

1. **ORM 模型**（spec 3.1–3.4）
2. **Alembic 初始化 + 第一份迁移**
3. **Pydantic schemas**
4. **CRUD 层**
5. **API 路由**（按依赖顺序：categories → customers → pets → costs → stats）
6. **`app/main.py` 注册路由 + 全局异常处理**
7. **seed 工具**
8. **测试**

### 2.2 ORM 模型要点

每张表的具体字段、索引、约束严格按 spec 第 3 节。下面只补细节：

- **MySQL 兼容**：每个 model class 里加
  ```python
  __table_args__ = (
      Index("idx_xxx", ...),
      {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
  )
  ```
  SQLite 会忽略这些参数，MySQL 生效。
- **DateTime 默认值**：`created_at` 用 `server_default=func.now()`；`updated_at` 用 `server_default=func.now()` + `onupdate=func.now()`（SQLAlchemy 层做，不依赖 MySQL 的 `ON UPDATE`，跨方言一致）。
- **Decimal**：`amount = Column(Numeric(10, 2), nullable=False)`，Python 侧用 `Decimal`，**不要转 float**。
- **关系**：
  - `Customer.pets = relationship("Pet", back_populates="customer", cascade="all, delete-orphan")`
  - `Pet.customer = relationship(...)`，`Pet.costs = relationship("CostRecord", back_populates="pet", cascade="all, delete-orphan")`
  - `CostRecord.pet = relationship(...)`
  - `CostRecord` 不建立到 `CostCategory` 的 ORM 关系（保持软引用）。
- **外键 ON DELETE CASCADE**：在 `ForeignKey("...", ondelete="CASCADE")` 里声明；同时 ORM 关系上 `cascade="all, delete-orphan"`，两层都做。

### 2.3 Alembic

1. **初始化**：`uv run alembic init alembic`
2. **改 `alembic/env.py`**：
   - 从 `app.core.config.settings` 读 `DATABASE_URL`，写到 `config.set_main_option("sqlalchemy.url", ...)`
   - `target_metadata = Base.metadata`，需 import 所有 model（建议 `from app.models import *`，`__init__.py` 再导出）
3. **生成第一份迁移**：`uv run alembic revision --autogenerate -m "initial schema"`
   - 生成后**人工审一遍**：四张表、索引、外键 ON DELETE CASCADE 都有；MySQL 字段长度 `VARCHAR(50)` 等正确；`Numeric(10,2)` 没退化成 `Float`
   - 在迁移末尾追加 `op.bulk_insert` 写入 5 个默认分类（spec 6.3）：
     ```python
     op.bulk_insert(cost_categories_table, [
         {"code": "food", "label": "粮食", "sort_order": 10},
         {"code": "medical", "label": "医疗", "sort_order": 20},
         {"code": "grooming", "label": "美容", "sort_order": 30},
         {"code": "toy", "label": "玩具", "sort_order": 40},
         {"code": "other", "label": "其他", "sort_order": 99},
     ])
     ```
     `cost_categories_table` 用 `sa.table(...)` + `sa.column(...)` 临时构造，避免 ORM 耦合。
   - `downgrade()` 里相应 `op.execute("DELETE FROM cost_categories WHERE code IN (...)")` 后再 `drop_table`。
4. **跑迁移**：`uv run alembic upgrade head`，验证 `dev.db` 有四张表 + 5 条分类。

> spec 4.0 要求**禁止 `Base.metadata.create_all()`**。所有建表只走 Alembic。

### 2.4 Pydantic schemas

按 spec 第 4 节字段。每个资源至少四个：

- `XxxBase`：所有可写字段
- `XxxCreate(XxxBase)`：含必填
- `XxxUpdate`：所有字段 `Optional`
- `XxxOut(XxxBase)`：含 `id`、时间戳，`model_config = ConfigDict(from_attributes=True)`

附加：

- `CustomerWithPets(CustomerOut)`：`pets: list[PetOut] = []`
- `Page[T]` 通用泛型：`{ items, total, page, page_size }`，写在 `schemas/common.py`
- 金额相关字段类型用 `Decimal`，FastAPI 会自动序列化为字符串（保精度），前端按字符串收
- 日期字段：`occurred_on: date`、`birthday: date | None`

### 2.5 CRUD 层

每个资源一个文件，函数命名 `get`、`get_multi`、`create`、`update`、`remove`。注意：

- **phone 冲突**：在 `customer.create` / `customer.update` 里查询 phone 是否已存在（且不是自己），存在就抛自定义 `ConflictError(detail={"detail": "phone_exists", "existing_id": ...})`，路由层捕获转 409。
- **category code 冲突**：同上，code 重复 → 409；同时 `category.remove` 前查 `cost_records` 是否有引用，有就 409 `{"detail": "category_in_use"}`。
- **筛选**：`cost.get_multi` 接收 `pet_id`、`customer_id`、`category_code`、`start`、`end`、`page`、`page_size`。`customer_id` 通过 join `pets` 表过滤。
- **分页**：返回 `(items, total)` 元组，路由层包装成 `Page` 响应。

### 2.6 API 路由

每个资源一个 `APIRouter(prefix="/customers", tags=["customers"])`，在 `app/main.py` 里
```python
app.include_router(customers.router, prefix="/api/v1")
```

**全局异常处理器**（`app/main.py`）：

```python
@app.exception_handler(ConflictError)
async def conflict_handler(request, exc):
    return JSONResponse(status_code=409, content=exc.detail)
```

`ConflictError` 在 `app/core/exceptions.py` 里定义。

### 2.7 统计接口（spec 4.6）

四个端点全部用 SQLAlchemy 的 `func.sum`、`func.count`、`extract` / `func.date_format` 做聚合。

注意：

- **跨方言月份分组**：MySQL 用 `DATE_FORMAT(occurred_on, '%Y-%m')`，SQLite 用 `strftime('%Y-%m', occurred_on)`。两套写法用 `engine.dialect.name` 分支。或者拉所有记录到 Python 端分组（数据量小可接受），但**首选数据库聚合**。
- **空时间窗**：`start`、`end` 都不传时不加 where 条件。
- **`by-category` 联结字典表**：left join `cost_categories` 拿 label，分类已被删的记录 label 显示 `code` 本身。
- **金额累加用 `Decimal`**，序列化字符串。

### 2.8 seed 工具

`backend/app/seed.py`，可执行：`uv run python -m app.seed`。

行为：

1. 用 `SessionLocal` 开 session
2. **按依赖反序**清空 `cost_records` → `pets` → `customers`（**不动 `cost_categories`**，字典由迁移管）
3. 插入 3 个客户 → 每客户 1–2 只宠物 → 每宠物 8–15 条花费记录
4. 花费 `occurred_on` 在过去 6 个月内随机；`category_code` 从 5 个内置分类随机取
5. `amount` 在 10–500 之间随机两位小数

**幂等**：每次跑都先清后插。

### 2.9 测试

按 spec 7.1，三类：

1. **`tests/conftest.py`**：
   - fixture `db`：`sqlite:///:memory:` 内存库 + `Base.metadata.create_all()`（**测试场景例外**，可用 create_all）+ 插入 5 个默认分类
   - fixture `client`：FastAPI `TestClient`，`override` `get_db` 依赖到 fixture `db`
2. **`tests/api/test_customers.py`**、`test_pets.py`、`test_costs.py`、`test_categories.py`：
   - 主路径 CRUD
   - 404
   - 422（缺字段）
   - 409（phone 重复 / category 重复 / 删被引用 category）
   - 级联删（删 customer 后查 pets/costs 都没了）
3. **`tests/test_stats.py`**：
   - 准备 fixture：1 客户、2 宠物、若干花费跨 3 个月、覆盖至少 3 个分类
   - 断言 4 个统计端点输出
   - 时间窗边界（`start = 月初`，`end = 月末`）
4. **`tests/test_migrations.py`**：
   - 起空 SQLite，`alembic upgrade head` 不报错
   - 跑完后 `Base.metadata` 与现有 schema 对比无差异（可用 `alembic.autogenerate.compare_metadata`）

### 2.10 验收

```bash
cd backend
uv run alembic upgrade head
uv run python -m app.seed
uv run pytest                      # 全绿
uv run uvicorn app.main:app --reload --port 8000
```

打开 `http://127.0.0.1:8000/docs`：
- 列出 5 个分类
- 创建客户、宠物、花费各一条
- 调用 4 个 stats 端点都有数据
- 删除客户能级联删宠物和花费

通过后 commit。

---

## 3. Phase 3 — 前端整合

**目标**：把现有 3 个视图改造成 7 个视图，全部走后端 API，跑通 spec 7.3 的手测清单。

### 3.1 实施顺序

1. **基础设施**：`api/http.js` + 各资源 api 文件
2. **store 重写**：4 个 store（customer / pet / cost / category），全部基于网络
3. **新视图**：`CustomerList`、`CustomerDetail`、`PetDetail`、`CostFormDialog`
4. **重写视图**：`CostList`、`Stats`、`Settings`
5. **路由调整**：`router/index.js` 按 spec 5.1
6. **手测清单走一遍**

### 3.2 `api/http.js`

```js
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
})

http.interceptors.response.use(
  (resp) => resp.data,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 409 && detail?.detail === 'phone_exists') {
      // 业务侧自己处理弹框，这里只把数据透传
      return Promise.reject(error.response.data)
    }
    const msg = typeof detail === 'string' ? detail : '请求失败'
    ElMessage.error(`${status || ''} ${msg}`)
    return Promise.reject(error)
  }
)

export default http
```

phone 冲突的「弹确认框引导查看已存在客户」逻辑在调用方（`CustomerList` 新增表单）里做，不要塞进拦截器。

### 3.3 资源 api 文件

每个文件导出函数，签名直白。例：

```js
// api/customers.js
import http from './http'
export const listCustomers = (params) => http.get('/customers', { params })
export const getCustomer = (id) => http.get(`/customers/${id}`)
export const createCustomer = (data) => http.post('/customers', data)
export const updateCustomer = (id, data) => http.patch(`/customers/${id}`, data)
export const deleteCustomer = (id) => http.delete(`/customers/${id}`)
```

其他四个资源（pets、costs、categories、stats）参照写。

### 3.4 store 重写

按 spec 5.3：

- store **不持有全量数据**，只缓存「当前页 items + total + page + 当前筛选 + 当前 detail」
- 所有翻页/筛选都重新 `await api.list(...)`
- `categoryStore` 例外：分类条目少且不常变，进入应用时拉一次缓存到 `state.list`，Settings 改动后手动刷新

旧 `costStore.js` 整个重写，**不要保留 localStorage 逻辑**。

### 3.5 视图

| 视图 | 关键交互 |
|---|---|
| `CustomerList` | 顶部搜索（`q`）+ 表格（分页）+ 「新增客户」对话框 |
| `CustomerDetail` | 上半客户信息（可编辑）+ 下半名下宠物表格（新增/编辑/删除宠物） |
| `PetDetail` | 上半宠物信息（可编辑）+ 下半该宠物花费列表（用 `CostFormDialog`） |
| `CostList` | 多维筛选条（客户/宠物/分类/时间窗）+ 表格 + 「新增花费」按钮（弹 `CostFormDialog`） |
| `CostFormDialog` | 客户级联宠物级联分类的两/三级选择 + 金额 + 日期 + 备注；外部传 `pet_id` 时锁定客户/宠物 |
| `Stats` | 时间窗筛选 + 4 个图（summary 卡片 + 分类饼图 + 月度柱图 + Top N 宠物） |
| `Settings` | 分类字典表格，行内编辑 label / sort_order，「删除」按钮调 API（被引用时显示 409 提示） |

实施提示：

- **金额展示**：后端给字符串，用 `Number(amount).toFixed(2)` 展示；提交时直接传字符串或数字皆可，FastAPI 都收。
- **日期**：el-date-picker 默认输出 Date 对象，用 `dayjs(d).format('YYYY-MM-DD')` 转 spec 要求格式后再传。
- **分页**：el-pagination 的 `current-page` 和 store 里 `page` 双向绑定即可。
- **级联选择**：客户下拉用 `listCustomers({ q, page_size: 50 })` + 远端搜索；选中客户后再加载该客户的 pets。
- **空状态**：保留现有项目的空状态视觉风格（参考 commit `93adbcd`）。

### 3.6 路由

`router/index.js` 按 spec 5.1 七个路由配齐，**保留** `/` → `/customers` 的 redirect（参考 commit `1d2edeb` 修过的 redirect 路由 bug，别再踩）。

旧路由（如 `/home`、单一花费视图）整段删掉。

### 3.7 验收

走 spec 7.3 手测清单全部 8 项，每项打勾。任何一项不通过都不能算 Phase 3 完成。

通过后 commit。

---

## 4. 跨期约定

### 4.1 commit 风格

参考最近提交：`fix: ...`、`✨ ...`、`🐛 ...`、`docs: ...`。每个 Phase 一个主 commit，必要时拆子 commit（比如 Phase 2 可拆「ORM + 迁移」「API + CRUD」「测试」）。

### 4.2 分支策略

直接在 `main` 上提交，不开 feature 分支（项目当前工作流就是这样）。如果用户后续要求改用 PR 流程再切换。

### 4.3 依赖追加

- 后端如缺包（spec 没列到的），先告知用户，得到确认再 `uv add`
- 前端**不得**新增依赖（已经齐了），如确实需要要先停下来问

### 4.4 Mock 边界提醒

SQLite 替身的限制（spec 6.2）必须在 `backend/README.md` 写清楚，避免后续被坑。

### 4.5 不要做的事

- 不要写鉴权代码（哪怕「先留个口子」）
- 不要写 Dockerfile / docker-compose
- 不要在 `main.py` 启动时自动 seed
- 不要用 `Base.metadata.create_all()` 替代 Alembic（除测试 conftest 内存库外）
- 不要写前端单元/E2E 测试
- 不要在金额上用 float
- 不要给 `category_code` 加数据库外键

---

## 5. 风险与回滚

| 风险 | 表现 | 处理 |
|---|---|---|
| `git mv` 后 vite 找不到入口 | `npm run dev` 报错 | 检查 `frontend/index.html` 的 `<script src="/src/main.js">` 路径正常；vite root 默认是 `frontend/` |
| Alembic autogenerate 漏字段 | 迁移生成后跑起来 schema 不全 | 人工对比 `models/*.py` 与 migration；必要时手补 `op.add_column` |
| SQLite 外键不级联 | 删 customer 后 pets 残留 | 确认 `database.py` 里 `PRAGMA foreign_keys=ON` 监听器生效 |
| CORS 报错 | 前端请求被浏览器拦 | 检查 `.env` 的 `CORS_ORIGINS` 是 JSON 数组格式；浏览器用 `127.0.0.1:3000` 而非 `localhost:3000`（或两者都加） |
| 金额精度丢失 | 求和结果末尾 `.0000001` | 全程 `Decimal`，不要中转 `float`；前端只做展示格式化 |
| Element Plus 组件主题被破坏 | 新视图样式与老页面不一致 | 沿用 `frontend/src/style.css` 与 commit `93adbcd` 的样式约定 |

每个 Phase 是独立 commit，出问题可以单 Phase `git revert`。

---

## 6. 完成定义（Definition of Done）

整个项目完成的标志：

- [ ] 三个 Phase 各自有 commit，可单独运行
- [ ] 顶层 README 启动命令照抄能跑通
- [ ] `uv run pytest` 全绿
- [ ] spec 7.3 手测清单 8 项全过
- [ ] `git status` 干净，没有 stray 文件、没有 `dev.db` 之类的进 git
