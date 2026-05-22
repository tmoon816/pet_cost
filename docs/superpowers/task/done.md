# 已完成任务归档

由 cron agent 在任务完成后自动追加。最新的在最上面。

---

## T-018: 宠物详情页补消费记录表格
- completed_at: 2026-05-22T23:25:30+08:00
- commit: cd4dbbc
- category: feature
- auto_approve: false
- attempt: 1
- result: no-op — PetDetail.vue 已有完整消费记录表格（日期/分类/金额/备注列 + el-pagination），npm run build 通过。

## T-024: 后端 idna 依赖 patch 升级 v3.15 → v3.16
- completed_at: 2026-05-22T21:42:00+08:00
- commit: 151b42d
- category: dep-patch
- auto_approve: true
- attempt: 1
- result: done — uv lock --upgrade-package idna，idna v3.15→v3.16（仅 uv.lock 3 行变动）。pytest 100/102 pass（2 个失败是预存 dirty test_stats.py 引入，非本次变更引起）。

## T-017: 全局搜索 — 顶部搜索框接线
- completed_at: 2026-05-22T16:47:35+08:00
- commit: f042771
- category: feature
- auto_approve: false
- attempt: 1
- result: done — 后端新增 GET /api/v1/search?q=，扫 customer name/phone、pet name、cost note，各组 LIMIT 5 最多 15 条；前端 App.vue 搜索框绑定 v-model + @input debounce 300ms 调搜索 API，结果分三组（客户/宠物/账单）下拉面板展示，点击跳详情页、回车跳第一个、路由变化自动关闭。pytest 69 全过，npm run build 通过。

## T-002: 后端 starlette 依赖 patch 升级 1.0.0 → 1.0.1
- completed_at: 2026-05-22T12:42:00+08:00
- commit: dcb58d9
- category: dep-patch
- auto_approve: true
- attempt: 1
- result: done — uv add starlette>=1.0.1，uv.lock 更新 starlette 1.0.0→1.0.1（仅 1 个顶层依赖变动）。pytest 67 全过。

## T-016: 后端 database.py 模块覆盖率补测试（69% → 100%）
- completed_at: 2026-05-22T13:42:15+08:00
- commit: ae3b474
- category: test
- auto_approve: true
- attempt: 1
- result: done — 新增 tests/test_database.py（2 个测试用例），覆盖 SQLite FK PRAGMA 启用路径与 get_db() 生成器。覆盖率 69%→100%（miss 行 15,22-26 → 全绿）。pytest 67→69 全过，npm run build 通过，不修改业务源码。
---

## T-005: 前端 vue-router 依赖 major 升级 4.6.4 → 5.0.7
- completed_at: 2026-05-22T11:42:00+08:00
- commit: ffbb41f
- category: feature
- auto_approve: false
- merge_to_main_after: true
- attempt: 1
- result: done — npm install vue-router@5.0.7，createRouter/createWebHashHistory/beforeEach 全部兼容，router/index.js 无需修改。npm run build 通过，backend pytest 67 全过。package.json diff 仅 vue-router 一行变动。

---

## T-003: 前端 sass 依赖升级 1.99.0 → 1.100.0
- completed_at: 2026-05-22T14:32:00+08:00
- commit: (本提交)
- category: feature
- auto_approve: false
- merge_to_main_after: true
- attempt: 1
- result: done — npm install sass@1.100.0，npm ls sass 确认为 1.100.0，npm run build 通过，pytest 69 全过，无新增警告

---

## T-001: Dashboard 主 chunk 体积超 500KB，做路由级 code-split
- completed_at: 2026-05-22T11:20:00+08:00
- commit: (本提交)
- category: refactor
- auto_approve: false
- chosen_plan: A (vite manualChunks, 函数形式适配 Rolldown)
- attempt: 1
- result: done — 入口 chunk 从 1,190KB→48KB（gzip 378KB→19KB），vendor-vue/antd-charts/element-plus 独立拆分；npm run build 通过，pytest 67 全过

---

## T-004: 前端 vite 依赖 patch 升级 8.0.13 → 8.0.14
- completed_at: 2026-05-22T08:58:00+08:00
- commit: (本提交)
- category: dep-patch
- auto_approve: true
- attempt: 1
- result: done — `cd frontend && npm install vite@8.0.14 --save-dev`。package.json devDependencies.vite 从 `^8.0.12`（实装 8.0.13） → `^8.0.14`；package-lock.json 同步更新：vite 8.0.13→8.0.14 + 随之随增的传递依赖 @oxc-project/types 0.130.0→0.132.0 与 rolldown 1.0.1→1.0.2（都是 vite 自带的 rolldown 内部依赖，仅 vite 一个顶层依赖变动，项目本身不直接引用）。验证：npm ls vite 是一棵 8.0.14、npm outdated 只剩 T-005 vue-router major、npm run build 通过、backend pytest 67 全过。

---

## T-015: 客户列表支持按累计消费金额排序
- completed_at: 2026-05-22T08:55:00+08:00
- commit: (本提交)
- category: feature
- auto_approve: false
- merge_to_main_after: true
- attempt: 1
- result: done — 后端 GET /customers 新增 `sort_by` (pattern `^(total_amount|created_at)$`) 与 `sort_dir` (`^(asc|desc)$`, default desc) Query 参数；crud.list_paginated 增加 correlated scalar subquery 算 total_amount（名下所有宠物累计消费 + COALESCE 默认 0）以面向排序和返回，按金额排序时叠加 Customer.id DESC 作为稳定次序，默认仍 Customer.id DESC（= created_at 倒序代理）； CustomerListItem schema 加 total_amount: Decimal=0。补 1 个用例覆盖：desc/asc/默认顺序、total_amount 计算正确（包括同人多条累加 + 无消费=0）、非法 sort_by 返 422。pytest 66→67。前端 customerStore 加 sortBy/sortDir state 与 setSort/fetchList 传参；CustomerList.vue 顶部加「金额排序」按钮（连击 desc→asc→默认）与标题动态位、表中新增「累计消费」右对齐列（¥ 0.00 格式）；npm run build 通过。

---

## T-014: 消费记录新增支持「最近 5 个客户」快选
- completed_at: 2026-05-22T08:48:00+08:00
- commit: (本提交)
- category: feature
- auto_approve: false
- merge_to_main_after: true
- attempt: 1
- result: done — 后端新增 `GET /api/v1/customers/recent?limit=5`（路由顺序放在 `/{customer_id}` 之前避免 path 冲突），crud.list_recent 用 INNER JOIN Pet/CostRecord + GROUP BY customer_id + ORDER BY max(occurred_on) DESC + LIMIT N，同一客户多条只取最近一次，无消费客户被 JOIN 天然筛掉。补 1 个用例（test_recent_customers_returns_by_last_visit_desc_excludes_no_cost）验证：排序、同人取 max、无消费不返回、limit 参数生效；pytest 65→66。前端 api/customers.js 加 listRecentCustomers；CostFormDialog.vue init() 非编辑模式下额外拉 loadRecentCustomers，displayCustomers computed 合并 [最近, 搜索结果] 并按 id 去重，最近项追加 `最近` el-tag 位于下拉顶部，点击直接赋值 form.customer_id；npm run build 通过。

---

## T-013: 消费记录列表加按客户名筛选
- completed_at: 2026-05-22T08:44:00+08:00
- commit: (本提交)
- category: feature
- auto_approve: false
- merge_to_main_after: true
- attempt: 1
- result: no-op — 验证后发现所有验收点已实现：后端 `GET /api/v1/costs` 已支持 `customer_id` 参数（costs.py:18 声明 + crud/cost.py:28 联表 Pet.customer_id）；前端 BillList.vue 顶部筛选区已含 filterable+remote 客户下拉（loadCustomers 调 customersApi.listCustomers），选中后 fetchList 会带 `params.customer_id`。查询、重置、联动宠物筛选都已在位。本地验：pytest 65 全过，npm run build 通过。不改业务代码，仅归档。

---

## T-012: 宠物档案显示「最近一次到店 / 距今天数」
- completed_at: 2026-05-22T07:46:00+08:00
- commit: (本提交)
- category: feature
- auto_approve: false
- merge_to_main_after: true
- attempt: 1
- result: done — 后端新增 PetListItem schema（继承 PetOut + last_visit_at: Optional[date]）；crud.list_paginated 改为一次 SQL 查询带 correlated scalar subquery (MAX(cost_records.occurred_on))，返回 dict 以似适配 Pydantic 序列化；pets API 路由改用 Page[PetListItem]。补 1 个用例验证三条消费取 max 且无消费 = None（pytest 64→65）。前端 PetList.vue 卡片底部新增「最近到店：YYYY-MM-DD（X 天前）」，formatLastVisit 处理：今天/昨天/X天前/—；pet-footer 改 space-between 布局。npm run build 通过。

---

## T-011: 客户详情页加消费时间线
- completed_at: 2026-05-22T05:43:00+08:00
- commit: 244b80f
- category: feature
- auto_approve: false
- merge_to_main_after: true
- attempt: 1
- result: done — 后端原已支持 customer_id 过滤 + occurred_on DESC 排序（list_paginated），不用改；前端 CustomerDetail.vue 新增「消费时间线」 el-card，el-timeline 展示日期/宠物名/分类 tag/金额/备注；load() 刷新详情同时重置时间线到 page=1，page_size=20。超过 20 条则底部显「加载更多」按钮递增 page 追加。分类 label 复用 categoryStore，备注为空时隐藏行；空状态提示「该客户还没有消费记录」。npm run build 通过，pytest 64 全过。

---

## T-010: Dashboard 新增「3 个月未到店老客」预警列表
- completed_at: 2026-05-22T04:42:00+08:00
- commit: 79b578d
- category: feature
- auto_approve: false
- merge_to_main_after: true
- attempt: 1
- result: done — 后端新增 GET /api/v1/stats/dormant-customers，口径：last_visit_at = 客户名下所有宠物的 max(occurred_on)，阈值 (today - last_visit_at ≥ days)，过滤后按 last_visit_at 升序 + limit 裁切；crud 函数支持 today 参数以便测试确定性；补 2 个用例（CRUD 阈值/排序/limit/起未命中 与 API 默认参数 smoke，pytest 62→64）。Dashboard 加一张预警卡片：可切 30/60/90/180 阈值，表格列：客户名 / 最后到店日期 / 距今天数（180+ danger / 其余 warning）/ 查看（跳 /customers/:id）；空结果提示「暂无久未到店老客 🎉」。npm run build 通过。

---

## T-009: Dashboard 新增「本月新客 vs 回头客」卡片
- completed_at: 2026-05-22T03:58:00+08:00
- commit: 本 commit
- category: feature
- auto_approve: false
- merge_to_main_after: true
- attempt: 1
- result: done — 后端新增 GET /api/v1/stats/customer-acquisition（year/month），口径：本月有消费的去重客户中，首次消费在本月为 new，其余为 returning；补 2 个用例（May 2026 双客户 1+1 / 空月 0+0，pytest 60→62）；Dashboard 在顶部 4 卡片后加一张 acquisition 卡片，三格：新客/回头客/本月活跃总数，含占比（总数 0 时显示 "—"）。

---

## T-008: 客户列表标记「新客/老客」标签
- completed_at: 2026-05-22T03:51:00+08:00
- commit: 本 commit
- category: feature
- auto_approve: false
- merge_to_main_after: true
- attempt: 1
- result: done — 后端 list_paginated 加 EXISTS 子查询计算 has_cost，返回结构改为 dict，response_model 切为 CustomerListItem(extends CustomerOut + has_cost)；不影响 CustomerWithPets/详情/创建/更新；补 1 个用例（pytest 59→60）；CustomerList 列表加 el-tag（老客/新客）；build 通过。

---

## T-007: 客户详情页加聚合卡片（累计消费/上次到店/总订单数）
- completed_at: 2026-05-22T03:45:00+08:00
- commit: 本 commit
- category: feature
- auto_approve: false
- merge_to_main_after: true
- attempt: 1
- result: done — 后端新增 GET /api/v1/customers/{id}/summary（total_amount/last_visit_at/cost_count，pet 联表 sum/max/count），增 CustomerSummary schema；补 2 个用例（happy path 含空状态校验 + 404，pytest 57→59）；前端 CustomerDetail 顶部加 3 个统计卡片（累计消费/上次到店/总订单数），load() 顺势拉 summary，空数据显示 “—”。

---

## T-006: 客户列表加按手机号实时搜索
- completed_at: 2026-05-22T03:40:00+08:00
- commit: 本 commit
- category: feature
- auto_approve: false
- merge_to_main_after: true
- attempt: 1
- result: done — 后端原已用 q 同时 LIKE name/phone，补一个 phone 模糊用例核实；前端去掉手动「搜索」按钮，watch(searchInput) + setTimeout 300ms debounce 实时触发查询，清空（el-input clearable）会令 v-model 变空字符串、watch 同样触发，fetchList 跳过空 q 返回全部。pytest 56→57、npm run build 通过。

---

## T-003: 清理前端 console.log / 调试输出
- completed_at: 2026-05-22T02:25+08:00
- commit: 8f62eb9
- category: lint
- auto_approve: true
- attempt: 1
- result: no-op — grep 发现 frontend/src 本就未包含任何 console.log（查验后），npm run build 通过，pytest 56 全过

---

## T-002: 后端覆盖率巡检并补缺失模块测试
- completed_at: 2026-05-22T02:18+08:00
- commit: 88d56a1
- category: test
- auto_approve: true
- attempt: 1
- result: pytest 37 → 56 全过，覆盖率 89% → 91%，不动业务源码

---

## T-023: app/crud/search.py 模块覆盖率补测试（22% → ≥80%）
- completed_at: 2026-05-22T17:42:00+08:00
- commit: 5534827
- category: test
- auto_approve: true
- attempt: 1
- result: no-op — 前次 tick 已实施并提交（5534827），覆盖率已达 100%，全部 93 个 pytest 通过。本次仅归档清理 todo.md 残留条目。
