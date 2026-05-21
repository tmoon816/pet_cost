# 宠物店管理系统 — CRUD 修复 + 业务定位转型 设计文档

- 日期：2026-05-22
- 项目：pet_cost（dev 分支）
- 状态：**待用户批准**
- 上游：补丁式承接 `2026-05-21-mock-to-real-and-budget-*.md`（mock→真接口骨架已落但字段对不齐、文案错位）

---

## 0. 一句话总结

上一轮把页面接到了真接口，但**前端字段普遍用 camelCase 调后端 snake_case，5 模块 CRUD 几乎都断**；同时整套文案是「个人记账」口吻，与「宠物店管理系统」业务定位不符。本轮目标：**字段对齐 → CRUD 全链路修通 → 业务文案/seed 数据切换到宠物店视角**，不扩边界、不加新业务模块。

---

## 1. 用户反馈的真实问题（按现场证据复述）

| # | 现象 | 根因（已读源码定位） |
|---|------|----------------------|
| 1 | 各页面「新增」点了 dialog 打开但提交失败 | 前端 payload 字段名大多是 camelCase（`customerId/petId/categoryCode/occurredOn/sortOrder/payType/type` 等），后端 Pydantic schema 是 snake_case，FastAPI 直接 422 |
| 2 | 编辑回填错乱 | `getXxx()` 返回 snake_case，前端组件直接 `data.customerId / data.categoryCode / data.weight / data.healthRecord` 取空，回填全 null |
| 3 | 表格字段空 | 同上：`BillList.vue` 取 `item.occurredOn / item.categoryCode / item.petId / item.petName / item.payType / item.type`，全部对不上后端 `CostOut(occurred_on, category_code, pet_id, …)`；后端根本没有 `pet_name / pay_type / type` 字段 |
| 4 | 删除/编辑/详情不通 | PetList 调 `listPets()` 然后做 `.map(item => …)`，但 `listPets()` 返回 `Page{items,total,…}` 不是数组 → `res.map is not a function` 直接异常 |
| 5 | 文案/字段是「个人记账」 | 菜单「数据大盘/收支账单/月度预算/消费分类」+ 顶部 logo「宠物账本」+ Dashboard「本月总支出/本月收入」+ seed 分类「粮食/医疗/美容/玩具/其他」，全是个人养宠记账口吻 |

额外发现（顺手要修，列入 Task 2 范围）：

- **Stats.vue 必崩**：使用 `statsApi.statsSummary / statsByCategory / statsByMonth / statsByPet`，但 `api/stats.js` 实际只 export `getSummary / getByCategory / getByMonth / getByPet`。整个数据中心页面打开即 ReferenceError。
- **`<el-col span="12">` 字符串绑定**：`PetForm.vue` `BillForm.vue` 中大量出现，Element Plus 会按 NaN 处理，列宽错乱。
- **PetList 年龄 NaN**：`Math.floor((new Date() - new Date(pet.birthday)) / …)`，`birthday=null` 时 `NaN岁`。
- **Dashboard 卡片**：`predicate 写死 totalBudget=4000、isOverBudget` 等假数据；Budget.vue 弹窗里宠物/分类下拉直接硬编码「旺财/年糕/food/medical/beauty」。
- **Settings 页与 CategoryList 页冲突**：两套分类管理 UI（旧 Settings 已对接，CategoryList 接口字段不对），仅保留两个但功能不一致；本轮不删除，但要保证两边都不再崩，方案后述。

---

## 2. 范围与不做清单

### ✅ 本轮做

1. **字段对齐审计**：定义「API 边界一律 snake_case」原则，列出每个资源前端用错的字段并给最终决策表。
2. **修 5 模块 CRUD 全链路**：customers / pets / costs(bills) / categories / budget — 列表/新增/编辑/删除/详情五动作走通。
3. **顺手清的低级 bug**：`<el-col :span="12">`、年龄 null、Stats 页 import 名、Budget 页假数据 + 硬编码下拉、`<el-card title=…>`（Element Plus 不支持 title 属性，会被忽略，不影响功能但顺手改 header slot）。
4. **业务定位转型**：
   - 菜单/路由 meta 文案改为宠物店口吻（**映射表见 §6，需用户确认**）
   - 顶部 logo / 浏览器标题改为「宠物店管理系统」
   - Dashboard 卡片改为「营业概览」语义
   - seed 分类扩展为典型宠物店服务（保留旧 code 兼容老数据）
   - README / 顶层文档「宠物消费管理系统」→「宠物店管理系统」
5. **后端按需小改**：仅当字段对齐审计确认「该字段对宠物店业务必要」才加，否则前端删字段；新增字段须出迁移 + 更新 model/schema/crud/test。
6. **文档与交付**：`docs/superpowers/plans/handoff-checklist.md` 更新本轮改动；README 改产品定位；保留旧的 `功能交付清单.md / 部署文档.md` 加 v2 段。

### ❌ 本轮不做

- 不加鉴权、不加角色权限
- 不加报表导出、不加打印小票
- 不加预约/排班/库存/会员卡等新业务模块
- 不动 main 分支、不发 PR、不 force push、不 --no-verify
- 不装 MySQL，不跑 e2e，只跑 SQLite pytest + npm build
- 不删除「BillList vs CostList」「CategoryList vs Settings」中任一页面（沿用上一轮决策，仅修复字段对齐）

---

## 3. 字段对齐审计（权威）

> 原则：**API 边界一律 snake_case，与后端 Pydantic schema 完全一致**。组件内部 ref/computed 想用 camelCase 可以，但 axios payload / 响应处理必须按 snake_case。

### 3.1 Customer（客户 / 会员）

| 后端字段（schema/customer.py） | 类型 | 必填 | 前端用错的地方 | 决策 |
|---|---|---|---|---|
| name | str ≤50 | ✅ | CustomerList、Detail 正确 | 保持 |
| phone | str ≤20 | - | 正确 | 保持 |
| note | str | - | 正确 | 保持 |
| id / created_at / updated_at | - | 读 | 正确 | 保持 |

**审计结论**：customers 模块字段无错，CRUD 通。

### 3.2 Pet（宠物）

| 后端字段（schema/pet.py） | 类型 | 必填 | 前端用错的地方 | 决策 |
|---|---|---|---|---|
| customer_id | int | ✅ | PetForm.vue 全程用 `customerId` | **改前端**为 `customer_id` |
| name | str ≤50 | ✅ | 正确 | 保持 |
| species | str ≤20 | - | PetForm 选项 `狗/猫/仓鼠/兔子/鹦鹉/其他`；后端无枚举但 seed/CustomerDetail 用 `dog/cat/other` | **改前端**：选项 value 统一用 seed 一致的英文 code（dog/cat/other/hamster/rabbit/bird），label 中文显示 |
| breed | str ≤50 | - | 正确 | 保持 |
| gender | str ≤10 | - | PetForm 用 `公/母/未知`；CustomerDetail/PetDetail 用 `male/female/unknown` | **改前端**：统一 `male/female/unknown`，label 中文 |
| birthday | date | - | PetForm 传 Date 对象，但有 `value-format="YYYY-MM-DD"` 兜底 | 保持 |
| note | str | - | 正确 | 保持 |
| ~~weight~~ | — | — | PetForm.vue 有 `weight`；PetList.vue 显示 pet.weight | **删前端字段**（个人记账概念，后端无） |
| ~~healthRecord~~ | — | — | PetForm.vue 有；PetList.vue 显示 | **删前端字段**（同上） |
| ~~thisMonthCost~~ | — | — | PetList 显示「本月花费」，期待 listPets 返回；后端不返回 | **删前端字段**（要做的话需要后端 N+1 改造，超范围） |
| ~~avatar~~ | — | — | PetList 客户端 emoji 兜底 | 保留为前端 derived，不发到后端 |

**审计结论**：PetForm + PetList **不通**，需重写字段映射。PetDetail / CustomerDetail 已用对字段，仅 species/gender 值需要统一。

### 3.3 Cost / Bill（消费记录 / 服务订单）

| 后端字段（schema/cost.py） | 类型 | 必填 | 前端用错的地方 | 决策 |
|---|---|---|---|---|
| pet_id | int | ✅ | BillForm `petId`；BillList `item.petId` | **改前端**为 `pet_id` |
| category_code | str ≤30 | ✅ | BillForm `categoryCode`；BillList `item.categoryCode` | **改前端**为 `category_code` |
| amount | Decimal(10,2) | ✅ | 正确（但 BillForm 用 `v-model.number`，提交时需 toString） | 改：提交时 `String(form.amount)` |
| occurred_on | date | ✅ | BillForm `occurredOn`；BillList `item.occurredOn` | **改前端**为 `occurred_on` |
| note | str | - | 正确 | 保持 |
| ~~type（收入/支出）~~ | — | — | BillForm 有「类型」radio，BillList 按 type 显示+/-；后端无 | **删前端字段**（个人记账概念。宠物店流水只有"客户消费"=支出。如保留，需说明） |
| ~~payType~~ | — | — | BillForm 有支付方式；BillList 列；后端无 | **删前端字段**（v2 如必要再加，本轮不加） |
| ~~petName~~ | — | — | BillList、Dashboard 显示 `item.petName \|\| 宠物${petId}` | **删前端字段**：改用前端 join（listPets 取 pets map 反查）或直接显示 `#pet_id`；本轮选「后端 listCosts 增加 pet_name 联表返回」（小改 schema，零字段冲突） |

**审计结论**：BillForm + BillList **不通**，必须重写。CostFormDialog（pets 详情页用的对话框）字段是对的，CostList 也对。**决策点 #1**（需用户确认）：是删 type/payType 还是后端加？默认**删**，让宠物店流水回归"客户消费=支出"语义。

### 3.4 Category（分类 / 服务项目）

| 后端字段（schema/category.py） | 类型 | 必填 | 前端用错的地方 | 决策 |
|---|---|---|---|---|
| code | str ≤30 | ✅ create | 正确 | 保持 |
| label | str ≤30 | ✅ | 正确 | 保持 |
| sort_order | int | - default 0 | CategoryList、CategoryForm 用 `sortOrder` | **改前端**为 `sort_order` |
| ~~icon~~ | — | — | CategoryList、CategoryForm 有 | **删前端字段**（默认在前端按 label 映射 emoji，不入库；v2 可选加） |
| ~~status~~ | — | — | CategoryList 显示启用开关 | **删前端字段**（后端无；想要的话需要加 model 字段 + 迁移，本轮不加） |
| ~~totalUsed~~ | — | — | CategoryList 显示「总消费」 | **删前端字段**（后端 listCategories 不返回；要做需 N+1 联表，超范围） |

**审计结论**：CategoryList 严重不通（status/totalUsed/icon 全是前端编出来的）。Settings.vue 是对的，本轮以 Settings 为参考重写 CategoryList。**决策点 #2**（需用户确认）：是否本轮加 status/totalUsed？默认**不加**，前端只展示后端有的字段，状态开关删除、总消费列删除。

### 3.5 Budget（经营预算）

| 后端字段（schema/budget.py） | 类型 | 必填 | 前端用错的地方 | 决策 |
|---|---|---|---|---|
| type | str ≤20 | ✅ create | Budget.vue 区分 `pet/category` 但表单没真正提交 | 重写表单，type 由按钮上下文决定 |
| target_id | str ≤50 | - | Budget.vue 读 `b.targetId` 但后端返 `target_id` | **改前端**为 `target_id` |
| year | int | ✅ | Budget.vue 拼月份字符串 currentMonth `2024-05`，已 split 出 year/month | 保持，但默认月份要改成"当前年月"，不能写死 2024-05 |
| month | int | ✅ | 同上 | 保持 |
| amount | Decimal | ✅ | Budget.vue 弹窗 totalBudget 直接复用页面顶级 ref，不区分新增/编辑/不同 type，**完全是死代码** | **重写预算弹窗**：独立 form ref，区分 global/pet/category 三种 type，下拉真的从 categoryStore / petStore 拉 |
| id / spent / remaining / overspent / created_at / updated_at | - | 读 | Budget.vue 用 `b.spent / b.amount`（数字字段对）但 `b.targetId` 错 | 改 target_id |

**审计结论**：Budget 页面表单弹窗是个**装饰品**——保存按钮调 handleFormSuccess 直接 close 而不发请求；删除是改 ref 数组而不调 deleteBudget。整个交互链路全是假的。**必须重写**。

### 3.6 Stats / Dashboard 返回字段（后端 schema/stats.py 是权威）

| 接口 | 后端字段 | 前端误用 | 决策 |
|---|---|---|---|
| `/stats/summary` | `total_amount / record_count / customer_count / pet_count` | Dashboard.vue 期望 `currentMonthAmount / budgetRemain / monthChange / totalIncome`；这些后端**根本没有** | **删前端假期望**：Dashboard 卡片改为展示后端真有的 4 个字段（"累计营业额/订单数/会员数/在册宠物数"），月度同比/预算剩余两个卡片删掉或后端 stats 增强（本轮**删掉**，不增强后端） |
| `/stats/by-category` | `category / label / total / count` | Dashboard 用 `categoryCode / totalAmount` | **改前端**为 `category / total` |
| `/stats/by-month` | `month / total` | Dashboard 用 `month / totalAmount / count` | **改前端**为 `month / total`；count 删除 |
| `/stats/by-pet` | `pet_id / pet_name / total` | Dashboard 用 `petId / petName / totalAmount / count` | **改前端**为 `pet_id / pet_name / total`；count 删除 |
| Stats.vue 引入 | `statsSummary / statsByCategory / statsByMonth / statsByPet` | api/stats.js 只导出 `getSummary / getByCategory / getByMonth / getByPet`，**整页崩** | **改前端**：Stats.vue 改 import 名 |

---

## 4. 命名规范（强制）

- **HTTP 边界**：请求 body / 响应 body / query 参数一律 snake_case，与 FastAPI Pydantic schema 一一对应。
- **组件内部**：reactive form / ref / computed 允许 camelCase，但提交前必须做 `{ pet_id: form.petId, category_code: form.categoryCode, occurred_on: form.occurredOn }` 这种显式映射，**不能依赖 spread 同名传递**。
- **store 层**：直接持有后端原样字段（snake_case），不做中间层转换，减少心智负担。
- **路由 query / 持久化 query 串**：snake_case，与后端 list 接口参数一致。
- **本轮选择**：直接把组件内部 ref 也改为 snake_case，省掉显式映射层 —— 减少 bug 面、改动更小。

---

## 5. 后端改动清单

### 5.1 必须改

| # | 改动 | 原因 | 文件 |
|---|---|---|---|
| 1 | `/api/v1/costs` list 响应增加 `pet_name` 字段（联表 Pet） | 前端账单列表要显示「所属宠物」，否则只能展示 `#pet_id`；属于宠物店核心展示，前端 join 成本高 | `app/crud/cost.py` `list_paginated` 改 join + select；`app/schemas/cost.py` `CostOut` 增 `pet_name: Optional[str] = None` |
| 2 | seed.py 扩展分类、调整描述 | 业务定位转型 | `app/seed.py`、迁移 `8xxx_extend_categories.py` |
| 3 | Alembic 新迁移：扩展 cost_categories 默认分类（保留旧 code，加新 code） | seed 是 dev 数据，正式分类要走迁移 | `alembic/versions/8xxx_extend_categories_for_petshop.py` |
| 4 | 新迁移要求：`BigInteger().with_variant(Integer(), "sqlite")`、`server_default=func.now()`、VARCHAR 显式长度 | MySQL 兼容红线 | 同上 |
| 5 | budget.py crud bug 兜底：`spent / remaining / overspent` 直接挂载到 ORM 对象属性是危险的（多次查询会污染）；改成返回 dict 或 Pydantic 模型实例填充 | 当前实现是给 ORM 对象动态加属性，序列化时凑活；本轮顺手修，因为 Budget.vue 重写时会更敏感 | `app/crud/budget.py` `_calculate_spent` 后改为构造 `BudgetOut(... spent=..., remaining=..., overspent=...)` |

### 5.2 不做

- 不加 `pets.weight` / `pets.health_record`：个人宠物记账概念，宠物店关心的是消费而非体检
- 不加 `cost_categories.icon` / `status`：icon 前端 fallback 即可；status 启停超出本轮
- 不加 `cost_records.type` / `pay_type`：宠物店流水语义就是"客户消费=支出"
- 不加 `cost_records.customer_id` 反范式：通过 pet→customer 反查已够用
- 不动 customers / pets / categories 三表 schema

---

## 6. 文案 / 业务术语映射表（**用户必须审核**）

> 这是决策点 #3。下表是默认方案，用户回复时如要改某一项请直接说"第 X 行改成 XXX"。

| 区域 | 旧 | 新（默认方案） |
|---|---|---|
| 浏览器标题 | 宠物花费管理系统 | 宠物店管理系统 |
| 顶部 logo 文字 | 宠物账本 | 宠物店管家 |
| 顶部 H1（页头） | 跟随 menu | 不变 |
| 侧边菜单 1 | 数据大盘 | 营业概览 |
| 侧边菜单 2 | 收支账单 | 服务订单 |
| 侧边菜单 3 | 宠物档案 | 宠物档案（保留） |
| 侧边菜单 4 | 消费分类 | 服务项目 |
| 侧边菜单 5 | 月度预算 | 经营预算 |
| 侧边菜单 6 | 系统设置 | 系统设置（保留） |
| 客户管理（暂未在侧边） | — | 「会员/客户档案」单独菜单项 → 加入 nav |
| Dashboard 卡 1 | 本月总支出 | 本月营业额 |
| Dashboard 卡 2 | 本月收入 | **删除**（"收入"在本系统无对应数据） |
| Dashboard 卡 3 | 预算剩余 | **删除**（后端 stats/summary 无此字段，加它要扩 API） |
| Dashboard 卡 4 | 宠物数量 | 在册宠物数 |
| Dashboard 副卡（新增） | — | 「订单总数」「会员数」（来自现有 stats/summary 的 record_count / customer_count） |
| PetList 页 H2 | 宠物档案 | 客户宠物档案 |
| PetList 卡片底部 | 本月花费 | **删除**（后端不返回） |
| BillList → 更名 | 收支账单 / 账单列表 | 服务订单 / 订单流水 |
| BillList 表头「类型」 | 收入/支出 | **删除列**（统一支出语义） |
| BillList 表头「支付方式」 | — | **删除列**（后端无） |
| BillList 表头「所属宠物」 | 宠物${id} 兜底 | 后端返 pet_name 后改为名字 |
| CategoryList 页 H2 | 消费分类 | 服务项目（宠物店提供的服务类型） |
| CategoryList 卡片「总消费」 | — | **删除**（后端不返回） |
| CategoryList 卡片状态开关 | 启用/禁用 | **删除**（后端无 status 字段） |
| Budget 页 H2 | 月度预算 | 经营预算 |
| Budget 页"总预算" | — | 「店铺月度营收目标」副标题"店铺整月营业额上限/目标，超出会预警" |
| Budget 页"宠物预算" | — | 「单宠物消费预警」副标题"针对单只宠物的累计消费预警额度（适用于长期寄养/疗养客户）" |
| Budget 页"分类预算" | — | 「服务项目营收目标」 |
| README 标题 | 宠物花费管理系统 | 宠物店管理系统 |
| README 一句话定位 | — | "面向中小型宠物店的客户/宠物档案 + 服务订单流水 + 经营预算 + 营业看板系统" |

**seed.py 分类扩展（默认）**：

| code | 旧 label | 新 label | sort_order |
|---|---|---|---|
| food | 粮食 | 商品零售（粮食） | 60 |
| medical | 医疗 | 医疗 | 30 |
| grooming | 美容 | 洗护美容 | 10 |
| toy | 玩具 | 商品零售（玩具） | 70 |
| other | 其他 | 其他 | 99 |
| **boarding**（新）| — | 寄养 | 20 |
| **training**（新）| — | 训练 | 40 |
| **retail**（新，可选）| — | 商品零售（综合） | 50 |

旧 code 全部保留（不删），避免历史 cost_records 引用断裂；只更名 label + 加新 code。**决策点 #4**：用户是否同意保留 `food/toy` code 并改 label，还是希望新 code 完全替代旧 code？默认**保留旧 code**。

---

## 7. 决策清单（实施前需用户确认 / 实施时不再问）

| # | 决策点 | 默认方案 | 需要用户拍板？ |
|---|---|---|---|
| D1 | cost_records 是否保留 `type/payType` | **删前端字段**，后端不加 | **是** |
| D2 | cost_categories 是否加 `status/totalUsed/icon` | **不加**，前端只显示后端有的 | **是** |
| D3 | 整张文案映射表（§6） | 见上表 | **是**（用户审核每行） |
| D4 | seed.py 分类扩展方式 | 保留旧 code 改 label + 加新 code | **是** |
| D5 | listCosts 是否补 `pet_name` 联表字段 | **加**（最小后端改动，让账单列表可读） | 默认通过，用户反对再调 |
| D6 | 是否新增独立"会员/客户档案"菜单（当前侧边没有 /customers，只能从 Dashboard 进） | **加菜单项**，路由 `/customers` 已存在视图（CustomerList.vue） | 默认通过 |
| D7 | Budget 弹窗的下拉数据源 | global 不需要、pet 从 listPets() 拉、category 从 listCategories() 拉 | 默认通过 |
| D8 | Dashboard 删 "本月收入 / 预算剩余" 卡 | **删** | 默认通过 |
| D9 | PetList 删 weight / healthRecord / thisMonthCost | **删** | 默认通过 |
| D10 | BillList 与 CostList 共存策略 | BillList = 总订单管理页（路由 /bills）；CostList = 宠物详情子组件；同时存在，复用 CostFormDialog（不再用 BillForm） | 默认通过 |
| D11 | 是否本轮删 BillForm.vue 和 CategoryList.vue 旧版 | **保留 BillForm 但弃用**（BillList 改用 CostFormDialog），CategoryList **重写**字段对齐版本 | 默认通过 |

> 用户回复"批准"即视为同意默认方案；如对 D1/D2/D3/D4 有不同意见请显式指出。

---

## 8. MySQL 兼容红线（写代码盯死）

1. String 必给长度（VARCHAR(n)）
2. 主键统一 `BigInteger().with_variant(Integer(), "sqlite")`
3. DateTime 默认值用 `server_default=func.now()`，不用 Python lambda
4. 不用 SQLite 专属语法（如 `INSERT OR REPLACE`）
5. 新迁移人工审核字段类型 / 长度 / 索引正确
6. 表默认 `mysql_charset="utf8mb4"`、`mysql_collate="utf8mb4_unicode_ci"`

---

## 9. 验收标准

- 后端 `cd backend && uv run pytest`：**全过**（包含新增 cost.pet_name 测试）
- 前端 `cd frontend && npm run build`：**全过**
- 浏览器手动验收清单：见 plan 文档 Task 2 末尾 25 项动作
- 文案验收：用户拉下代码后打开浏览器，所有页面无"个人记账"残留
