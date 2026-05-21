---
enabled: true
auto_merge_main: true
---

# 任务队列

云端 cron agent 每次 tick 读取本文件，按状态机选一条任务执行。
**人类操作**：审完 spec 后把任务状态从 `spec_drafted` 改为 `approved` 即可放行。
暂停整个循环：把上面 frontmatter 的 `enabled` 改 `false`。

任务条目格式见模板。已完成的任务由 agent 自动从这里移到 `done.md`。

---

## 状态机

```
backlog → (auto_approve 命中) → approved
backlog → (写 spec) → spec_drafted → (人审) → approved
approved → (实施) → in_progress → done
                              ↘ blocked （3 次失败）
```

---

## 任务模板（复制改用）

```markdown
## T-XXX: 任务标题
- status: backlog
- category: bug-fix | feature | refactor | docs | test | lint | dep-patch | dead-code
- auto_approve: false
- spec: ""
- acceptance:
  - 后端 pytest 全过
  - 前端 npm run build 通过
  - 具体业务验收点
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0
```

---

## 进行中 / 待审

(空)

---

## Backlog

## T-011: 客户详情页加消费时间线
- status: approved
- category: feature
- auto_approve: false
- merge_to_main_after: true
- acceptance:
  - GET /api/v1/costs 支持 customer_id 过滤 + 按 occurred_on 倒序（已支持则核实）
  - CustomerDetail.vue 加 el-timeline，显示历次消费：日期 / 宠物名 / 分类 / 金额 / 备注
  - 默认显示最近 20 条，超过显示"加载更多"
  - npm run build 通过
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

## T-012: 宠物档案显示「最近一次到店 / 距今天数」
- status: approved
- category: feature
- auto_approve: false
- merge_to_main_after: true
- acceptance:
  - GET /api/v1/pets 列表返回 last_visit_at 字段
  - 后端补 1 个用例
  - PetList.vue 卡片底部加「最近到店：YYYY-MM-DD（X 天前）」/ 无消费时"—"
  - npm run build 通过
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

## T-013: 消费记录列表加按客户名筛选
- status: approved
- category: feature
- auto_approve: false
- merge_to_main_after: true
- acceptance:
  - GET /api/v1/costs 支持 customer_id 筛选（已支持则核实）
  - BillList.vue 顶部筛选区加客户下拉，远程搜索（沿用 CostFormDialog 的客户检索）
  - 选中客户后列表只显示该客户消费
  - npm run build 通过
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

## T-014: 消费记录新增支持「最近 5 个客户」快选
- status: approved
- category: feature
- auto_approve: false
- merge_to_main_after: true
- acceptance:
  - 新增 GET /api/v1/customers/recent?limit=5，按客户名下最近一次消费时间倒序
  - 无任何消费的客户不返回
  - 后端补 1 个用例
  - CostFormDialog.vue 客户下拉打开时顶部展示最近 5 个，点击直接选中
  - npm run build 通过
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

## T-015: 客户列表支持按累计消费金额排序
- status: approved
- category: feature
- auto_approve: false
- merge_to_main_after: true
- acceptance:
  - GET /api/v1/customers 支持 sort_by=total_amount&sort_dir=desc|asc
  - 默认仍按 created_at 倒序
  - 后端补 1 个用例
  - CustomerList.vue 加表头"累计消费"列 + 切换排序按钮
  - npm run build 通过
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

## T-001: Dashboard 主 chunk 体积超 500KB，做路由级 code-split
- status: spec_drafted
- category: refactor
- auto_approve: false
- spec: "docs/superpowers/specs/2026-05-22-T001-route-code-split.md"
- acceptance:
  - 主 bundle gzip 后 < 200KB
  - npm run build 通过
  - 浏览器主流程页面切换无白屏
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

## T-004: 前端 vite 依赖 patch 升级 8.0.13 → 8.0.14
- status: backlog
- category: dep-patch
- auto_approve: true
- spec: ""
- acceptance:
  - npm run build 通过
  - package-lock.json 同步更新
  - 仅升级 vite，不动其他依赖
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0
- signal_source: "cd frontend && npm outdated 显示 vite 8.0.13 → 8.0.14"

## T-005: 前端 vue-router 依赖 major 升级 4.6.4 → 5.0.7
- status: backlog
- category: feature
- auto_approve: false
- spec: ""
- acceptance:
  - npm run build 通过
  - 所有现有路由打开无报错
  - breaking change 需在 spec 中逐项评估
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0
- signal_source: "cd frontend && npm outdated 显示 vue-router 4.6.4 → 5.0.7（major）"
