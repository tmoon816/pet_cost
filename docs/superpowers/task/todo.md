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

## blocked（阻塞中）

(空)

---

## backlog（待执行）

## T-028: 服务项目预设价格 → 录单自动填金额
- status: backlog
- category: feature
- auto_approve: false
- spec: ""
- acceptance:
  - 后端 pytest 全过（含 categories 新字段往返、CategoryOut 包含 default_amount）
  - 前端 npm run build 通过
  - cost_categories 表新增 default_amount NUMERIC(10,2) NULL；alembic 迁移生成并跑通
  - Settings.vue 分类编辑表单可设置 default_amount（el-input-number，最小 0，两位小数；可清空）
  - CostFormDialog：watch category_code，amount 为空时自动填 default_amount；amount 已有值时不覆盖
  - 分类下拉每项展示「label · ¥amount」，无 default_amount 时仅显示 label
- blocked_reason: ""
- created_at: 2026-05-24
- last_run: ""
- attempt: 0
- parent_proposal: P-007

## T-029: CostFormDialog 多宠物一键批量开单
- status: backlog
- category: feature
- auto_approve: false
- spec: ""
- acceptance:
  - 后端 pytest 全过（含 batch 接口 200 / 校验 422 / 事务原子性 3 个用例）
  - 前端 npm run build 通过
  - 后端新增 POST /api/v1/costs/batch，body 含 pet_ids[] + category_code/amount/occurred_on/note，事务内创建 N 条记录，任一条失败整体回滚
  - CostFormDialog 新增态：宠物字段改 multiple；pet_ids.length > 1 走 batch，==1 仍走原 createCost
  - 编辑模式保持单条（不开放多选）
  - 「保存并继续」保留 pet_ids 选择，仅清空金额和备注
- blocked_reason: ""
- created_at: 2026-05-24
- last_run: ""
- attempt: 0
- parent_proposal: P-007

## T-030: Dashboard 顶部固定「今日营业」小卡
- status: backlog
- category: feature
- auto_approve: false
- spec: ""
- acceptance:
  - 前端 npm run build 通过
  - Dashboard 顶部新增独立的今日小卡：今日营业额、今日订单数、查看明细按钮
  - 数据来源 getSummary({start: today, end: today})，与下方日期选择器解耦（其变化不影响今日卡）
  - 查看明细按钮跳 CostList 并自动应用 start=today&end=today 筛选
  - CostList 支持从 route query 解析 start/end 并应用到筛选（无 query 时保持现有默认）
  - CostList 日期快捷按钮加「今天」选项
  - 纯前端改动，不动后端
- blocked_reason: ""
- created_at: 2026-05-24
- last_run: ""
- attempt: 0
- parent_proposal: P-007

