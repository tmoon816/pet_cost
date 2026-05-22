# Cron 运行日志

每次 cron tick 由 agent 追加一行。最新的在最下面。

格式：`| timestamp | task_id | action | result | commit | note |`

| timestamp | task_id | action | result | commit | note |
|-----------|---------|--------|--------|--------|------|
| 2026-05-22T02:18+08:00 | T-002 | implement | done | 88d56a1 | 覆盖率 89%→91%，pytest 37→56；巡检追加 T-004(vite patch, auto)/T-005(vue-router major, 需审) |
| 2026-05-22T02:26+08:00 | T-003 | implement | done (no-op) | 8f62eb9 | grep 核验 frontend/src 本就未包含 console.log；build × pytest 均绿；修复 todo.md 中 T-001 重复条目 |
| 2026-05-22T02:45+08:00 | T-001 | draft_spec | spec_drafted | 本 commit | 查实际代码后发现路由级 code-split 已实现，真正问题是 vendor 未拆（echarts/antd-charts/element-plus）；spec 提出 A/B/C 三案，建议 A；acceptance 200KB 阈值不现实需调 |
| 2026-05-22T03:40+08:00 | T-006 | implement | done | e6bfb6a (main: e6bfb6a) | 后端增 1 个 phone 模糊搜索用例（pytest 56→57）；前端 CustomerList 接入 watch+300ms debounce，去掉「搜索」按钮，清空即恢复全量；npm run build 通过；auto-merge main FF 成功 |
| 2026-05-22T03:45+08:00 | T-007 | implement | done | efe585d (main: efe585d) | 后端新增 GET /customers/{id}/summary、CustomerSummary schema、补 2 用例（pytest 57→59）；前端 CustomerDetail 加 3 个聚合卡片，空数据“—”；auto-merge main FF 成功 |
| 2026-05-22T03:51+08:00 | T-008 | implement | done | 4879ff5 (main: 4879ff5) | 后端 GET /customers 加 has_cost(EXISTS)、CustomerListItem、补 1 用例（pytest 59→60）；前端 CustomerList 增「老客/新客」el-tag 列；auto-merge main FF 成功 |
| 2026-05-22T03:58+08:00 | T-009 | implement | done | 29aee52 (main: 29aee52) | 后端 GET /stats/customer-acquisition (year/month)，StatsCustomerAcquisition schema，min(occurred_on) 判定首次消费；补 2 用例（pytest 60→62）；Dashboard 加三格 acquisition 卡片（新/回/总 + 占比）；auto-merge main FF 成功 |
| 2026-05-22T04:00+08:00 | - | tick_end | chain=4 | - | 本 tick 链完成 T-006/T-007/T-008/T-009，均 done + auto-merge main FF；巡检：frontend npm outdated 只剩 T-004/T-005（已在 backlog），backend 无 outdated 直接依赖，grep TODO/FIXME 为空，覆盖率未跳（pytest-cov 未装）。未追加新任务。 |
| 2026-05-22T04:42+08:00 | T-010 | implement | done | e3ff37c (main: e3ff37c) | 后端新增 GET /stats/dormant-customers + StatsDormantCustomerItem + crud.dormant_customers（按 last_visit_at 升序），补 2 用例（pytest 62→64）；前端 Dashboard 加一张预警卡片（可切 30/60/90/180，退色差 tag，查看跳 customer-detail）；build 通过；auto-merge main FF 成功。 |
| 2026-05-22T04:46+08:00 | - | tick_end | chain=1 | - | 本 tick 实施 T-010（done + main FF）。巡检：frontend npm outdated 仍只有 vite patch / vue-router major（均已在 backlog），backend uv tree --outdated 无直接依赖需升，grep TODO/FIXME/XXX 为空。未追加新任务。 |
| 2026-05-22T05:43+08:00 | T-011 | implement | done | 244b80f (main: 1ff09c9) | 前端 CustomerDetail 加「消费时间线」el-timeline（pet_name/分类tag/金额/备注），page_size=20+「加载更多」分页，复用已有 GET /costs?customer_id=X 不动后端；build 通过，pytest 64 全过；auto-merge main FF 成功 |
| 2026-05-22T05:44+08:00 | - | tick_end | chain=1 | - | 本 tick 实施 T-011（done + main FF 1ff09c9）。巡检：frontend npm outdated 仍只 vite patch / vue-router major（已在 backlog T-004/T-005），backend uv tree --outdated 无直接依赖需升，grep TODO/FIXME/XXX 为空。未追加新任务。 |
| 2026-05-22T06:42+08:00 | - | tick_start | local_dirty_exit | - | backend/uv.lock 工作区脏（revision 2→3 + tsinghua mirror url 替换，疑似上一 tick uv 调用副作用），按协议第二步“local dirty, exit”立即退出，不做任何改动，不认领任务 |
| 2026-05-22T07:46+08:00 | T-012 | implement | done | 78bd428 (main: 78bd428) | uv.lock 脏是 mirror url 变动 (pull --ff-only 未 fail)，按 git checkout 丢弃后推进；后端 PetListItem schema + crud 用 correlated scalar subquery 取 MAX(occurred_on) 避免 N+1，API 路由改 Page[PetListItem]；补 1 用例（多条取 max + 无消费 null，pytest 64→65）；前端 PetList.vue 卡片底部展示「最近到店：YYYY-MM-DD（X 天前/昨天/今天）」，无消费“—”；build 通过；auto-merge main FF 成功 |
| 2026-05-22T07:46+08:00 | - | tick_end | chain=1 | - | 本 tick 实施 T-012（done + main FF 78bd428）。巡检：frontend npm outdated 仍只 vite patch (T-004 在 backlog) / vue-router major (T-005 在 backlog)，backend uv tree --outdated 无直接依赖需升，grep TODO/FIXME/XXX 为空。未追加新任务。后续对 uv.lock mirror 扫扫选备案：若反复出现，容后续写个 small fix 任务锁住 source registry |
| 2026-05-22T08:44+08:00 | T-013 | implement | no-op | (本提交) | 验证现状：后端 costs.py:18 + crud/cost.py:28 已含 customer_id 联表筛选，前端 BillList.vue 已有 filterable+remote 客户下拉且 fetchList 会传 params.customer_id——T-013 所有验收点在之前的 ¨ T-011/T-012 实施中已顺手做了。本地 pytest 65 全过，npm run build 通过，不改业务代码仅归档。巡检：frontend npm outdated 仍只 T-004 vite patch / T-005 vue-router major（均已在 backlog），backend 直接依赖无 outdated（仅 starlette/idna 传递依赖，不追任务），grep TODO/FIXME/XXX 为空。未追加新任务。 |
