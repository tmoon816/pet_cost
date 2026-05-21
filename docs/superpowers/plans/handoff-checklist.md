# Handoff Checklist — v2（2026-05-22）

> 配套 spec：`docs/superpowers/specs/2026-05-22-crud-fix-and-petshop-pivot-design.md`
> 配套 plan：`docs/superpowers/plans/2026-05-22-crud-fix-and-petshop-pivot-plan.md`

## 1. 本轮改动文件清单

### 后端
- `backend/pyproject.toml` — 加 `[tool.setuptools] packages = ["app"]`，修云端 uv sync 包发现冲突
- `backend/app/schemas/cost.py` — CostOut 增 `pet_name: Optional[str] = None`
- `backend/app/schemas/budget.py` — class Config → ConfigDict（消除 Pydantic v2 警告）
- `backend/app/crud/cost.py` — list_paginated 始终 join Pet，元组返回 + setattr 注入 pet_name
- `backend/app/crud/budget.py` — 整体重构：返 dict 不污染 ORM
- `backend/app/api/v1/budgets.py` — 适配 crud 新签名
- `backend/app/seed.py` — 客户备注宠物店化
- `backend/alembic/versions/8a1c9d2e4f01_extend_categories_for_petshop.py` — **新文件**：扩展分类
- `backend/tests/api/test_costs.py` — 新增 `test_list_costs_returns_pet_name`

### 前端
- `frontend/index.html` — title
- `frontend/src/router/index.js` — 文案 + 加 /customers 路由
- `frontend/src/App.vue` — 菜单/Logo
- `frontend/src/stores/categoryStore.js` — 双套命名兼容 + sort_order 排序
- `frontend/src/components/PetForm.vue` — snake_case + 删 weight/healthRecord + species/gender code
- `frontend/src/components/CategoryForm.vue` — snake_case + 删 icon/status
- `frontend/src/views/pets/PetList.vue` — 字段对齐 + 空生日年龄守卫 + 分页 + 客户筛选
- `frontend/src/views/bills/BillList.vue` — 改用 CostFormDialog + 字段对齐 + 删 type/payType
- `frontend/src/views/categories/CategoryList.vue` — 字段对齐 + 删 status/totalUsed
- `frontend/src/views/budget/Budget.vue` — 重写 CRUD 全链路 + 真实弹窗下拉
- `frontend/src/views/Dashboard.vue` — 卡片/图表全部对齐 stats schema + 删假数据卡
- `frontend/src/views/Stats.vue` — import 名修正

### 文档
- `README.md` — 标题 + 一句话定位
- `功能交付清单.md` — v2 更新段
- `部署文档.md` — v2 升级提示
- `docs/superpowers/specs/2026-05-22-crud-fix-and-petshop-pivot-design.md` — **新文件**
- `docs/superpowers/plans/2026-05-22-crud-fix-and-petshop-pivot-plan.md` — **新文件**
- `docs/superpowers/plans/handoff-checklist.md` — **新文件（本文件）**

## 2. 用户本地拉下来要做的事

```bash
# 1. 拉代码
git checkout dev
git pull --ff-only

# 2. 后端
cd backend
uv sync
uv run alembic upgrade head    # 关键：跑新迁移 8a1c9d2e4f01
uv run pytest -q                # 确认 37/37 全过
uv run uvicorn app.main:app --reload --port 8000

# 3. 前端（新开终端）
cd frontend
npm install
npm run dev                     # 访问 http://127.0.0.1:3000
```

⚠️ **第一次 sync 慢的话**：云端用了清华源（`~/.config/uv/uv.toml`）。本地若慢可参考相同做法。

## 3. 浏览器手动验收清单（25 项 = 5 模块 × 5 动作）

按顺序点：

### 会员/客户档案（点新菜单进入）

1. **列表加载 + 翻页 + 搜索**：搜「张伟」能找到 seed 数据
2. **新增**：点「新增客户」→ 填「测试客户A、13800000000」→ 保存 → 列表出现
3. **编辑**：点测试客户A 行的「编辑」→ dialog 填充正确 → 改名「测试客户B」→ 保存 → 列表显示新名
4. **删除**：点「删除」→ 确认弹框 → 列表不再有
5. **详情**：点列表行 → 进入详情 → 显示客户信息 + 名下宠物表

### 宠物档案

6. **列表加载**：卡片网格显示 seed 的几只宠物
7. **新增**：点「新增宠物」→ 客户ID 1，名「测试宠物」，犬，公，2023-01-01 → 保存 → 卡片出现
8. **编辑**：点编辑 → dialog 回填 customer_id/name/species 正确 → 改名「测试宠物2」→ 卡片更新
9. **删除**：点删除 → 确认弹框 → 卡片消失
10. **详情**：点「查看详情」→ 进入 PetDetail → 显示宠物信息 + 该宠物的服务订单列表

### 服务订单（菜单：服务订单）

11. **列表加载 + 翻页**：seed 数据应有几十条订单
12. **筛选**：选客户「张伟」→ 联动加载该客户名下宠物 → 选宠物 → 列表条数变化；选服务项目「医疗」筛选；选日期范围筛选
13. **新增**：点「新增订单」→ 选客户/宠物/服务项目/金额 100/今天 → 保存 → 列表第一行
14. **编辑**：点编辑 → 金额改 200 → 列表显示 200
15. **删除**：点删除 → 确认 → 列表无该行

### 服务项目（菜单：服务项目）

16. **列表加载**：按 sort_order 升序显示 8 个服务项目（迁移后含 boarding/training/retail）
17. **新增**：code=test_svc，label=测试项目，sort_order=80 → 保存 → 卡片出现
18. **编辑**：改 label「测试项目2」→ 卡片更新（code 不可改）
19. **删除**：删「测试项目2」→ 成功（无引用情况下）
20. **排序**：再新增 sort_order=5 的项目，刷新页面看是否排到最前

### 经营预算（菜单：经营预算）

21. **切换月份**：默认显示当前月，切到当前月触发 listBudgets({year,month})
22. **新增全店营收目标**：点「营收目标」→ 弹窗 → 金额 5000 → 保存 → 总卡显示 5000；本月已营收数会自动计算
23. **新增单宠物预警**：点「单宠物预警」→ 选宠物 → 金额 1000 → 保存 → 单宠物卡片显示
24. **新增服务项目目标**：点「服务项目目标」→ 选「医疗」→ 金额 500 → 保存 → 服务项目卡片显示
25. **编辑/删除任一预算**：编辑只能改 amount（type/target/月份锁定）；删除有确认弹框

## 4. 测试验收

```bash
cd backend && uv run pytest -q           # 应该 37 passed
cd frontend && npm run build              # 应该 ✓ built（chunk size warning 是正常的，未做 splitting）
```

## 5. 已知限制 / 不在本轮范围

- 鉴权未做，所有 API 是 open
- 报表导出 / 打印小票 / 预约 / 排班 / 库存 / 会员卡未做
- 前端 BillForm.vue 已弃用但保留文件（下一版本可删）
- Dashboard 月度趋势图是全量数据（未做时间窗筛选 UI）
- 验收过程中若发现 pet 添加时 customer_id 没下拉只能输入数字 — 是设计取舍（侧重保持表单简洁），如要下拉选择请在下一轮加

## 6. 何时回退本轮

如果在你本地 alembic 升级失败，回退方式：

```bash
cd backend
uv run alembic downgrade 7dd7aae05221    # 回到上一个 revision
git revert 473f3a0                        # revert 迁移那一个 commit
```

如果只是前端 build 失败，单 revert 对应 commit 即可。
