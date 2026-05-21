# 宠物花费管理系统 — 假数据接真接口+预算模块实施计划
- 日期：2026-05-21
- 预期工时：4小时
- 状态：待审核
---
## 前置说明
- 开发分支：仅在`dev`分支开发，不新建分支
- 提交规范：每个Task单独commit，按约定加emoji前缀
- 测试要求：每个Task提交前必须通过对应测试环节
---
## Task 1: 预算后端模块开发
### 实施步骤
1. 新建ORM模型：`backend/app/models/budget.py`，注册到`__init__.py`
2. 新建Pydantic Schema：`backend/app/schemas/budget.py`
3. 新建CRUD层：`backend/app/crud/budget.py`
4. 新建API路由：`backend/app/api/v1/budgets.py`，注册到main.py
5. 生成Alembic迁移文件：`uv run alembic revision --autogenerate -m "add budget table"`
6. 人工审核迁移文件，确保MySQL兼容（字段长度、字符集、索引正确）
7. 新建pytest测试用例：`backend/tests/api/test_budgets.py`
### 文件清单
```
backend/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   └── budget.py
│   ├── schemas/
│   │   └── budget.py
│   ├── crud/
│   │   ├── __init__.py
│   │   └── budget.py
│   └── api/v1/
│       ├── __init__.py
│       └── budgets.py
├── alembic/versions/
│   └── xxx_add_budget_table.py
└── tests/api/
    └── test_budgets.py
```
### 验收命令
```bash
# 后端测试全过
cd backend && uv run pytest
# 迁移跑通
cd backend && uv run alembic upgrade head
# 接口文档可访问
curl http://127.0.0.1:8000/docs | grep "budgets"
```
### 提交信息
`✨ 新增预算后端模块（model+schema+crud+api+pytest）`
---
## Task 2: Dashboard.vue接真接口
### 实施步骤
1. 替换所有setTimeout模拟数据的代码为真实API调用
2. 绑定四个统计接口：getSummary()、getByCategory()、getByMonth()、getByPet()
3. 适配接口返回字段到现有图表组件
4. 增加加载状态、异常空状态处理
5. 确保现有UI交互完全不变
### 文件清单
```
frontend/src/views/Dashboard.vue
```
### 验收命令
```bash
# 前端编译通过
cd frontend && npm run build
# 页面加载无报错，图表显示真实数据（手动验证）
```
### 提交信息
`✨ Dashboard.vue对接真实统计接口`
---
## Task 3: PetList.vue接真接口
### 实施步骤
1. 替换假宠物列表数据为getPets()接口调用
2. 绑定新增按钮调用createPet()接口
3. 绑定编辑按钮调用updatePet()接口
4. 绑定删除按钮调用deletePet()接口
5. 适配接口返回字段到现有卡片组件
6. 增加分页、加载状态处理
### 文件清单
```
frontend/src/views/pets/PetList.vue
```
### 验收命令
```bash
cd frontend && npm run build
# 手动验证：列表加载正常，新增/编辑/删除功能正常
```
### 提交信息
`✨ PetList.vue对接真实宠物接口`
---
## Task 4: BillList.vue接真接口
### 决策前置确认
BillList与现有CostList不合并：BillList是全量账单管理页面，CostList是宠物详情页的子组件，复用同一个BillForm组件即可，不需要合并逻辑，减少改动风险
### 实施步骤
1. 替换假账单列表数据为getCosts()接口调用
2. 绑定筛选条件（时间、分类、宠物）到接口参数
3. 绑定新增按钮调用createCost()接口
4. 绑定编辑按钮调用updateCost()接口
5. 绑定删除按钮调用deleteCost()接口
6. 适配接口返回字段到现有表格组件
7. 增加分页、加载状态处理
### 文件清单
```
frontend/src/views/bills/BillList.vue
```
### 验收命令
```bash
cd frontend && npm run build
# 手动验证：列表加载正常，筛选功能正常，新增/编辑/删除功能正常
```
### 提交信息
`✨ BillList.vue对接真实消费接口，确认与CostList不合并，复用表单组件`
---
## Task 5: CategoryList.vue接真接口
### 实施步骤
1. 替换假分类列表数据为getCategories()接口调用
2. 绑定新增按钮调用createCategory()接口
3. 绑定编辑按钮调用updateCategory()接口
4. 绑定删除按钮调用deleteCategory()接口
5. 适配接口返回字段到现有卡片组件
6. 增加加载状态处理
### 文件清单
```
frontend/src/views/categories/CategoryList.vue
```
### 验收命令
```bash
cd frontend && npm run build
# 手动验证：列表加载正常，新增/编辑/删除功能正常
```
### 提交信息
`✨ CategoryList.vue对接真实分类接口`
---
## Task 6: Budget.vue接后端接口
### 实施步骤
1. 新增`src/api/budgets.js` API客户端
2. 新增`src/stores/budgetStore.js`状态管理
3. 替换假预算数据为getBudgets()接口调用
4. 绑定新增预算按钮调用createBudget()接口
5. 绑定编辑预算按钮调用updateBudget()接口
6. 绑定删除预算按钮调用deleteBudget()接口
7. 适配超支警示逻辑为接口返回的overspent字段
8. 保持现有UI完全不变
### 文件清单
```
frontend/src/
├── api/
│   └── budgets.js
├── stores/
│   └── budgetStore.js
└── views/budget/Budget.vue
```
### 验收命令
```bash
cd frontend && npm run build
# 手动验证：预算列表加载正常，新增/编辑/删除功能正常，超支警示正常
```
### 提交信息
`✨ Budget.vue对接预算接口，完成预算模块全功能`
---
## Task 7: 编写交付验收清单
### 实施步骤
1. 编写`docs/superpowers/plans/handoff-checklist.md`，列出用户本地拉代码后需要执行的所有步骤
2. 包含环境准备、数据库迁移、服务启动、功能验收清单
### 文件清单
```
docs/superpowers/plans/handoff-checklist.md
```
### 验收命令
```bash
# 文档检查无误
cat docs/superpowers/plans/handoff-checklist.md
```
### 提交信息
`📝 新增项目交付验收清单文档`
---
## 全流程验收（提交前必须执行）
```bash
# 1. 后端全量测试通过
cd backend && uv run pytest
# 2. 前端全量编译通过
cd frontend && npm run build
# 3. 冒烟测试全流程通过
# 创建客户 → 创建宠物 → 创建消费记录 → 查看Dashboard统计 → 设置预算 → 验证超支警示
```
---
## 最终交付物
- 设计文档：`docs/superpowers/specs/2026-05-21-mock-to-real-and-budget-design.md`
- 实施计划：`docs/superpowers/plans/2026-05-21-mock-to-real-and-budget-plan.md`
- 交付清单：`docs/superpowers/plans/handoff-checklist.md`
- 全量功能代码，所有测试通过，可直接运行
