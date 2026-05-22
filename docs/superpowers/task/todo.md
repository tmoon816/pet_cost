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

## T-003: 前端 sass 依赖升级 1.99.0 → 1.100.0
- status: backlog
- category: feature
- auto_approve: false
- spec: ""
- acceptance:
  - npm run build 通过
  - 样式无回归
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0
- signal_source: "cd frontend && npm outdated 显示 sass 1.99.0 → 1.100.0（非 patch，需评估）"

## T-004: 后端 idna 依赖 minor 升级 3.15 → 3.16
- status: backlog
- category: feature
- auto_approve: false
- spec: ""
- acceptance:
  - 后端 pytest 全过
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0
- signal_source: "cd backend && uv tree --outdated 显示 idna 3.15 → 3.16（minor）"

## T-016: 后端 database.py 模块覆盖率补测试（69% → ≥70%）
- status: in_progress
- category: test
- auto_approve: true
- spec: ""
- acceptance:
  - 后端 pytest 全过
  - app/core/database.py 覆盖率 ≥ 70%
  - 不修改业务源码
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: "2026-05-22 13:42:15 CST"
- attempt: 1
- signal_source: "cd backend && uv run pytest --cov=app --cov-report=term-missing 显示 app/core/database.py 69%（miss 行 15, 22-26）"

