# 已完成任务归档

由 cron agent 在任务完成后自动追加。最新的在最上面。

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

(暂无)
