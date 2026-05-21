# 宠物店管理系统 — CRUD 修复 + 业务定位转型 实施计划

- 日期：2026-05-22
- 项目：pet_cost（dev 分支）
- 配套 spec：`docs/superpowers/specs/2026-05-22-crud-fix-and-petshop-pivot-design.md`
- 状态：**待用户批准**
- 工作流约束：dev 分支、每 Task 单独 commit（emoji 前缀）、每个 commit 前 `pytest` + `npm build` 全过、不动 main、不发 PR、不 force push

## Task 1 — 字段对齐审计交付（文档已写入 spec §3）

### 内容
spec §3 已穷举每个资源的后端权威字段、前端误用、决策。本 Task 不产生代码改动，仅作为后续 Task 的依据。

### 验收
- 用户审核 spec §3 + §7 决策清单，回复"批准"或指出要改的决策
- spec/plan 已 push 到 dev：`docs/superpowers/{specs,plans}/2026-05-22-*.md`

### Commit
`📝 spec(docs): 宠物店转型 + CRUD 修复 设计与计划`（合并 spec + plan + 本 plan，单 commit）

## Task 2 — 后端最小改动（cost.pet_name 联表 + budget crud 安全化）

### 实施
1. `app/schemas/cost.py`：`CostOut` 增 `pet_name: Optional[str] = None`
2. `app/crud/cost.py` `list_paginated`：始终 outerjoin Pet，select 中加 `Pet.name.label("pet_name")`；按 `(CostRecord, pet_name)` 元组迭代，构造返回 list 时把 pet_name 挂到对象/dict
3. `app/api/v1/costs.py`：list_costs 返回保持 Page schema 不变（pet_name 走 CostOut 字段）
4. `app/crud/budget.py`：把"动态属性挂载到 ORM"重构为"构造 dict 返回"；schema/budget.py 的 `Budget` 模型字段不变；router 改为 `response_model=Budget` 包装 dict
5. `backend/tests/api/test_costs.py`：增加 `test_list_costs_returns_pet_name` 用例
6. `backend/tests/api/test_budgets.py`：保持现有测试全过

### 验收
- `cd backend && uv run pytest`：**全过**（新增 1 个用例）
- `curl /api/v1/costs?page_size=5`：响应 items[].pet_name 存在

### Commit
`✨ feat(api): costs 列表返回 pet_name，budget crud 返 dict 避免污染 ORM`

## Task 3 — Alembic 迁移 + seed.py 分类扩展（宠物店）

### 实施
1. 新建 `backend/alembic/versions/8aaa_extend_categories_for_petshop.py`
   - up：`UPDATE cost_categories SET label='洗护美容', sort_order=10 WHERE code='grooming'` 等
   - up：`INSERT INTO cost_categories (code, label, sort_order) VALUES ('boarding','寄养',20), ('training','训练',40), ('retail','商品零售（综合）',50)`（带 ON CONFLICT/IF NOT EXISTS 兼容写法用 `op.execute` 或先 SELECT 判断）
   - down：删除新增 code，恢复旧 label
   - 注意：String / DateTime / 主键写法遵守 MySQL 红线（本迁移只 UPDATE/INSERT data，无 schema 变更，红线主要看 bulk_insert 是否带长度，使用 `sa.column('code', sa.String(30))` 显式声明）
2. `app/seed.py`：CUSTOMER_PROFILES、PET_TEMPLATES note 文案改为宠物店客户口吻（"会员积分 3200"、"常客每周洗澡"、"VIP 会员"），保持原数量
3. `backend/tests/test_migrations.py`：若有，确保 head 升级通过；否则新增冒烟测试

### 验收
- `cd backend && uv run alembic upgrade head`：成功
- `cd backend && uv run pytest`：全过
- `cd backend && uv run python -m app.seed`：可执行无报错（仅本地 dev，CI 不跑）

### Commit
`✨ feat(db): 扩展 cost_categories 为宠物店服务项目；seed 改宠物店客户语境`

## Task 4 — 前端字段对齐：PetForm / PetList 重写

### 实施
1. `src/components/PetForm.vue`：
   - form 字段全 snake_case：`customer_id / name / species / breed / gender / birthday / note`
   - 删除 `weight / healthRecord`
   - species 选项 value 改为 `dog/cat/other/hamster/rabbit/bird`，label 中文
   - gender 选项 value 改为 `male/female/unknown`，label 中文
   - el-col 全部改 `:span="12"` 数字绑定
   - fetchPet 回填用 snake_case
   - 提交前清理空字段
2. `src/views/pets/PetList.vue`：
   - `listPets()` 返回 `Page{items,total}`，必须取 `res.items`；按客户/分页过滤
   - 删除 weight / healthRecord / thisMonthCost / avatar 渲染（保留 emoji，但根据 species code 取值映射）
   - 年龄计算加 null 守卫：`pet.birthday ? Math.floor(...) + '岁' : '-'`
   - species 显示 label 而非 code（用一个本地 map）
   - 新增/编辑/删除/详情链路绑 PetForm
   - 表格化（卡片网格保留也行，但加分页）

### 验收
- `cd frontend && npm run build`：全过
- 浏览器手动 25 项动作中本模块 5 项通过

### Commit
`🐛 fix(pet): PetForm/PetList 字段对齐 snake_case；删 weight/healthRecord；修空生日 NaN`

## Task 5 — 前端字段对齐：BillList 重写（弃用 BillForm，复用 CostFormDialog）

### 实施
1. `src/views/bills/BillList.vue` 整页重写：
   - 引入 CostFormDialog（已存在，字段对的）
   - listCosts 参数：`page / page_size / pet_id / customer_id / category / start / end`（全 snake_case）
   - 表格列：日期(occurred_on) / 分类(label by code) / 所属宠物(pet_name) / 金额 / 备注 / 操作
   - 删除"类型"列、"支付方式"列
   - 筛选区：按客户(联动 pets)、按宠物、按分类、按日期范围（参考 CostList.vue 的现有实现）
   - 删除/编辑/新增链路通过 CostFormDialog
2. 不再 import BillForm（保留文件，加注释 `<!-- @deprecated 用 CostFormDialog -->`，下个版本删）
3. el-col 全部 `:span`

### 验收
- `cd frontend && npm run build`：全过
- 浏览器手动 5 项动作

### Commit
`🐛 fix(bill): BillList 改用 CostFormDialog，字段 snake_case；删 type/payType；显示 pet_name`

## Task 6 — 前端字段对齐：CategoryList / CategoryForm 重写

### 实施
1. `src/components/CategoryForm.vue`：
   - form 字段 snake_case：`code / label / sort_order`
   - 删除 icon / status 表单项
   - el-col 修正
   - fetchCategory / submit 全部 snake_case
2. `src/views/categories/CategoryList.vue`：
   - listCategories 返回是数组（不是 Page）
   - 卡片只展示后端有字段：code / label / sort_order
   - icon 用本地 emoji map by label fallback（不发到后端）
   - 删除"启用/禁用"开关 + handleStatusChange
   - 删除"总消费"
   - 排序按 sort_order 升序
   - 新增/编辑/删除链路绑 CategoryForm

### 验收
- `npm run build` 全过
- 浏览器 5 项动作

### Commit
`🐛 fix(category): CategoryList/Form 字段对齐；删 status/totalUsed/icon 后端不存在字段`

## Task 7 — 前端字段对齐：Budget.vue 重写

### 实施
1. `src/views/budget/Budget.vue` 整页重写：
   - 当前月份默认取 `new Date().getFullYear() / getMonth()+1`，非硬编码 2024-05
   - fetchBudgetData：listBudgets({ year, month })，处理 global/pet/category 三类预算
   - target_id 用 snake_case
   - 弹窗重写：
     - type 由点击按钮上下文决定（global / pet / category），进入弹窗时不可改
     - 宠物下拉：从 listPets() 取
     - 分类下拉：从 categoryStore.list 取
     - 金额：el-input-number
     - 年月：el-date-picker type="month" 或 year/month 两个 number
     - **保存真正调 createBudget / updateBudget API**
     - **删除真正调 deleteBudget API**
   - 卡片使用率/超支预警保留（spent/remaining/overspent 字段已正确）

### 验收
- `npm run build` 全过
- 浏览器 5 项动作

### Commit
`🐛 fix(budget): Budget 重写 CRUD 全链路；弹窗真实提交；删假数据/硬编码下拉`

## Task 8 — 前端字段对齐：Dashboard / Stats 修复

### 实施
1. `src/views/Dashboard.vue`：
   - getSummary：响应字段改为 `total_amount / record_count / customer_count / pet_count`
   - 卡片：
     * 卡 1：本月营业额（用 stats/summary + start/end=本月首末日参数）→ total_amount
     * 卡 2：订单数 → record_count
     * 卡 3：会员数 → customer_count
     * 卡 4：在册宠物数 → pet_count
   - 删原"本月收入/预算剩余"假数据卡
   - getByCategory：`item.category / item.total / item.count`
   - getByMonth：`item.month / item.total`
   - getByPet：`item.pet_id / item.pet_name / item.total`
   - listCosts 近期账单：`item.occurred_on / category_code / pet_name / amount / note`
2. `src/views/Stats.vue`：
   - 修 import：`getSummary / getByCategory / getByMonth / getByPet`，调用名同步改

### 验收
- `npm run build` 全过
- 浏览器：Dashboard 数据真实显示、Stats 页面不再 ReferenceError

### Commit
`🐛 fix(dashboard): 卡片/图表字段对齐后端 stats schema；Stats 页 import 名修正`

## Task 9 — 前端业务定位转型（菜单 / 文案 / Logo / 路由）

### 实施
1. `src/App.vue`：
   - logo 文字"宠物账本" → "宠物店管家"
   - menuItems 文案：
     * 数据大盘 → 营业概览
     * 收支账单 → 服务订单
     * 宠物档案 保持
     * 消费分类 → 服务项目
     * 月度预算 → 经营预算
     * 系统设置 保持
   - 新增菜单项：会员/客户档案 → /customers（路由也加）
2. `src/router/index.js`：
   - 加 `/customers` 路由（视图 CustomerList.vue 已存在）+ `/customers/:id` 路由（视图 CustomerDetail.vue 已存在）
   - meta.title 全部按映射表更新
   - document.title 后缀改"宠物店管理系统"
3. `frontend/index.html`：title 改"宠物店管理系统"

### 验收
- 浏览器：所有菜单文案、标题、logo 已切换；点新菜单"会员/客户档案"能进 CustomerList 页面

### Commit
`✨ feat(brand): 菜单/标题/Logo 切换为宠物店管理系统；新增会员菜单`

## Task 10 — README + 文档更新 + handoff checklist

### 实施
1. `README.md`：
   - 标题改"宠物店管理系统"
   - 一句话定位（见 spec §6）
   - 模块清单按新文案
2. `功能交付清单.md`：在末尾加"## v2 更新（2026-05-22）"段，描述本轮改动概要 + 一句话总结：CRUD 链路打通 + 业务定位转向宠物店
3. `部署文档.md`：加 v2 提示 — 升级时要跑 `uv run alembic upgrade head`（迁移 8aaa_extend_categories...）
4. `docs/superpowers/plans/handoff-checklist.md`：
   - 列本轮所有改动文件
   - 用户本地拉下来要做的：`git pull`、`cd backend && uv sync && uv run alembic upgrade head`、`cd frontend && npm install && npm run dev`
   - 浏览器 25 项验收清单（5 模块 × 5 动作，见下）

### 浏览器 25 项验收清单（顺序执行）

**Customers（会员/客户档案，新增菜单进入）**
1. 列表加载 + 翻页 + 搜索"张伟"
2. 新增客户「测试客户A，手机 13800000000」→ dialog 打开 → 提交 → 列表刷新出现
3. 编辑「测试客户A」→ dialog 回填正确 → 改名「测试客户B」→ 列表显示新名
4. 删除「测试客户B」→ 确认弹框 → 接口成功 → 列表不再有
5. 点列表行进入详情 → 显示客户信息 + 名下宠物表

**Pets（客户宠物档案）**
6. 列表加载（卡片网格）
7. 新增宠物「测试宠物，customer_id=1，dog，公，2023-01-01」→ 提交成功 → 出现
8. 编辑「测试宠物」→ 回填正确 → 改名「测试宠物2」→ 卡片更新
9. 删除「测试宠物2」→ 确认 → 卡片消失
10. 点「查看详情」→ 进入 PetDetail → 显示信息 + 该宠物的花费记录

**Costs/Bills（服务订单）**
11. 列表加载 + 翻页
12. 按客户/宠物/分类/日期筛选，确认 SQL where 生效（条数变化）
13. 新增订单（选客户→选宠物→选服务项目→金额 100→今天）→ 成功 → 列表第一行
14. 编辑该订单 → 金额改 200 → 列表显示 200
15. 删除该订单 → 确认 → 列表无

**Categories（服务项目）**
16. 列表加载（按 sort_order 排序）
17. 新增服务项目「code=test_svc, label=测试项目, sort_order=80」→ 成功 → 出现
18. 编辑「测试项目」→ 改 label「测试项目2」→ 卡片更新
19. 删除「测试项目2」→ 成功（若无引用）
20. 排序变化：再新增一个 sort_order=5 的项目，刷新页面看是否排到前面

**Budget（经营预算）**
21. 切换月份（默认本月）→ listBudgets({year,month}) 触发
22. 新增 global 预算 5000 → 成功 → 总预算卡显示 5000，已用金额非 0
23. 新增 pet 预算（选某只宠物，1000）→ 成功 → 宠物预算卡片显示
24. 新增 category 预算（选「医疗」，500）→ 成功 → 分类预算卡片显示
25. 编辑/删除任一预算 → 成功

### Commit
`📝 docs(handoff): README/部署/交付清单 v2；25 项浏览器验收 checklist`

## 全流程验收（最后一次推 dev 前）

```bash
cd backend && uv run pytest -q            # 必须全过（基线 36 + 本轮 ≥1 新增）
cd frontend && npm run build              # 必须全过，无 warning explosion
git log --oneline -20                     # 检查所有 commit message 解释了"为什么"
```

## 何时停下来问人

- D1（type/payType 删/保）、D2（status/totalUsed 删/保）、D3（文案表）、D4（seed 分类）需要在 spec 审批阶段拍板；进入实施阶段不再问
- 同一字段多处冲突需要重新决策时
- pytest 改 3 次还过不了时
- 任何超出 spec 范围的衍生需求

## 时间估算（参考）

- Task 2（后端 cost.pet_name + budget crud）：30 分钟
- Task 3（迁移 + seed）：30 分钟
- Task 4（PetForm/PetList）：40 分钟
- Task 5（BillList）：40 分钟
- Task 6（CategoryList/Form）：30 分钟
- Task 7（Budget 重写）：50 分钟
- Task 8（Dashboard/Stats）：30 分钟
- Task 9（菜单/路由/文案）：20 分钟
- Task 10（README/checklist）：20 分钟
- 每个 Task 前后跑测试 + commit：约 10 分钟 × 9 = 90 分钟
- **合计：~6 小时**

## 风险

| 风险 | 缓解 |
|---|---|
| 云端 uv 解析依赖慢/卡 | 用 `uv sync --offline` 优先；若必须联网会在 Task 2 前提示并等待 |
| pytest 引入的 cost.pet_name 字段变更打断既有 36 测试 | 仅给 CostOut 加可选字段，旧测试不读 pet_name 不受影响；新增专用测试 |
| Element Plus 弹窗 dialog 内 form 重置时机 | 用 `@closed` 钩子统一 reset，避免内存泄漏 |
| Budget 弹窗 type 锁定后用户想换：拒绝 vs 重开 | 本轮：弹窗内 type 只读，要换 type 需关闭重新点对应按钮（与 spec D7 一致） |
