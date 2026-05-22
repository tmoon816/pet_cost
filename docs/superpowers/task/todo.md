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

## T-026: 后端 pydantic-core 依赖 minor 升级 v2.46.4 → v2.47.0
- status: blocked
- category: dep-patch
- auto_approve: false
- spec: "docs/superpowers/specs/2026-05-22-T026-pydantic-core-minor-upgrade.md"
- acceptance:
  - 后端 pytest 全过
  - `uv lock` 后 pydantic-core 版本升至 2.47.0
- blocked_reason: "PyPI 上 pydantic-core v2.47.0 尚未发布，当前最新 2.46.4"
- created_at: 2026-05-22
- last_run: "2026-05-22"
- attempt: 0

---

## backlog（待执行）

## T-027: 后端 app/seed.py 模块补测试（覆盖率 0% → ≥70%）
- status: backlog
- category: test
- auto_approve: true
- spec: ""
- acceptance:
  - 后端 pytest 全过
  - `app/seed.py` 模块覆盖率 ≥ 70%
  - 不修改 seed.py 业务源码
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

## T-025: 后端 click 依赖 patch 升级 v8.4.0 → v8.4.1
- status: backlog
- category: dep-patch
- auto_approve: true
- spec: ""
- acceptance:
  - 后端 pytest 全过
  - `uv lock` 后 click 版本升至 8.4.1
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0