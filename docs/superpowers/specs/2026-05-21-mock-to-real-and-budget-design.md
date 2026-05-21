# 宠物花费管理系统 — 假数据接真接口+预算模块设计
- 日期：2026-05-21
- 项目：pet_cost
- 状态：待审核
---
## 1. 背景与目标
当前前后端分离结构已完成，后端API已全部实现，前端部分页面仍在用setTimeout模拟假数据。本次迭代目标：
1. **全页面接真后端接口**：替换所有页面的模拟数据，打通前后端完整链路
2. **新增预算管理模块**：实现月度预算设置、超支预警功能
3. **功能对齐**：保持现有UI交互完全不变，只替换数据层，无用户感知改动
---
## 2. 本次迭代范围
### ✅ 必须完成：
1. Dashboard.vue：替换假统计数据为真实后端/stats接口数据
2. PetList.vue：替换假宠物列表为真实后端/pets接口数据，支持CRUD操作
3. BillList.vue：替换假账单列表为真实后端/costs接口数据，支持CRUD操作（确认BillList与现有CostList不重复，BillList面向全量账单的管理场景，CostList保留为宠物详情页的子组件）
4. CategoryList.vue：替换假分类列表为真实后端/categories接口数据，支持CRUD操作
5. Budget.vue：替换假预算数据为新开发的预算模块接口，实现预算设置、超支预警功能
6. 后端新增完整预算模块：数据模型、迁移、CRUD、API、pytest测试
### ❌ 不在本次范围：
- 不需要修改现有UI样式
- 不需要新增其他页面
- 不需要修改现有客户管理相关逻辑
- 不需要鉴权、部署相关改动
---
## 3. 数据模型设计（新增预算表）
### 3.1 `budgets` 预算表
> 支持两种预算粒度：全局月度总预算、按宠物/按分类的细分预算
| 字段 | 类型 | 约束 | 说明 | MySQL兼容要求 |
|---|---|---|---|---|
| id | BIGINT | PK, AUTO_INCREMENT | | |
| type | VARCHAR(20) | NOT NULL, INDEX | 预算类型：`global`（全局总预算）、`pet`（单宠物预算）、`category`（分类预算） | VARCHAR长度显式指定 |
| target_id | VARCHAR(50) | NULL, INDEX | 预算目标ID：type=pet时存pet_id，type=category时存category_code，type=global时为NULL | 用VARCHAR兼容不同类型的目标ID |
| year | INT | NOT NULL, INDEX | 预算年份 | |
| month | INT | NOT NULL, INDEX | 预算月份（1-12） | |
| amount | DECIMAL(10,2) | NOT NULL | 预算金额，元 | |
| created_at | DATETIME | NOT NULL, server_default=func.now() | | 用数据库端默认值，不写Python端lambda |
| updated_at | DATETIME | NOT NULL, server_default=func.now(), onupdate=func.now() | | |
### 3.2 索引设计
```sql
INDEX idx_budgets_year_month (year, month)
INDEX idx_budgets_type_target (type, target_id)
UNIQUE INDEX uk_budgets_unique (type, target_id, year, month) -- 同一个目标同一月份只能有一个预算
```
### 3.3 外键与删除策略
- 不建立物理外键（避免关联逻辑复杂），用应用层校验目标存在性
- 删除宠物/分类时，同步删除对应预算（应用层实现）
---
## 4. 后端API设计（新增预算相关接口）
### 4.1 预算模块API（前缀/api/v1/budgets）
| Method | Path | 说明 | 请求/响应示例 |
|---|---|---|---|
| GET | `/budgets?year=&month=` | 查询指定年月的所有预算 | 响应：`[{"id":1,"type":"global","target_id":null,"year":2026,"month":5,"amount":"5000.00","spent":"3200.00","remaining":"1800.00","overspent":false}]`（自动计算已花金额、剩余、是否超支） |
| GET | `/budgets/{id}` | 查询单个预算详情 | |
| POST | `/budgets` | 新建预算 | 请求体：`{"type":"global","target_id":null,"year":2026,"month":5,"amount":"5000.00"}`；同一目标同一月份重复创建返回409 |
| PATCH | `/budgets/{id}` | 更新预算金额 | |
| DELETE | `/budgets/{id}` | 删除预算 | |
### 4.2 统计接口扩展（已有接口兼容）
- 现有`/stats/*`接口保持不变，预算模块需要的已花金额直接复用现有统计逻辑
---
## 5. 前端改动点
### 5.1 公共改动
- 新增`src/api/budgets.js`：预算模块API客户端
- 新增`src/stores/budgetStore.js`：预算数据状态管理
### 5.2 页面改动
| 页面 | 改动点 |
|---|---|
| Dashboard.vue | 1. 替换所有setTimeout模拟数据为真实API调用：`getSummary()`、`getByCategory()`、`getByMonth()`、`getByPet()`；2. 保留现有图表渲染逻辑完全不变；3. 异常情况显示空状态 |
| PetList.vue | 1. 替换假宠物列表为`getPets()`接口数据；2. 绑定新增/编辑/删除按钮调用真实API；3. 保留现有卡片UI、表单完全不变 |
| BillList.vue | 1. 替换假账单列表为`getCosts()`接口数据；2. 绑定新增/编辑/删除按钮调用真实API；3. 筛选条件对接接口参数；4. 保留现有表格UI、表单完全不变 |
| CategoryList.vue | 1. 替换假分类列表为`getCategories()`接口数据；2. 绑定新增/编辑/删除按钮调用真实API；3. 保留现有卡片UI、表单完全不变 |
| Budget.vue | 1. 替换假预算数据为`getBudgets()`接口数据；2. 实现预算新增/编辑/删除功能对接API；3. 超支警示逻辑根据接口返回的`overspent`字段显示；4. 保留现有UI完全不变 |
### 5.3 复用现有组件
- 已有的PetForm.vue、BillForm.vue、CategoryForm.vue直接复用，不需要修改
---
## 6. 决策清单（实施时不需再问）
| 决策 | 选择 | 理由 |
|---|---|---|
| BillList与CostList是否合并 | 不合并 | BillList是全量账单管理页面，CostList是宠物详情页的子组件，定位不同，保留两份逻辑但复用同一个Form组件 |
| 预算粒度支持 | 支持全局/宠物/分类三种粒度 | 覆盖用户所有预算场景需求，不做过度设计 |
| 预算已花金额计算方式 | 接口查询时实时计算，不存冗余字段 | 数据一致性优先，计算量小无性能问题 |
| 重复预算校验 | 唯一索引+应用层校验 | 避免同一目标同一月份多个预算冲突 |
| 前端改动范围 | 只换数据层，UI完全不动 | 保证用户体验无感知，降低改动风险 |
| 测试范围 | 新增预算pytest，后端全量pytest，前端全量build | 保证既有功能不被破坏 |
---
## 7. MySQL兼容红线
1. 所有字符串字段显式指定VARCHAR长度
2. DateTime默认值用SQLAlchemy的`server_default=func.now()`，不使用Python端lambda
3. 不使用SQLite专属语法
4. Alembic迁移文件人工审核，确保类型正确、长度完整
5. 表默认字符集utf8mb4，排序规则utf8mb4_unicode_ci
