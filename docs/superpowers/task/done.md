# 已完成任务归档

由 cron agent 在任务完成后自动追加。最新的在最上面。

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

(暂无)
