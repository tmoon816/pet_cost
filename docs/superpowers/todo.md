---
enabled: true
max_runs_per_day: 8
runs_today: 1
runs_today_date: 2026-05-22
budget_left_usd: 5.0
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

## T-001: Dashboard 主 chunk 体积超 500KB，做路由级 code-split

## T-001: Dashboard 主 chunk 体积超 500KB，做路由级 code-split
- status: backlog
- category: refactor
- auto_approve: false
- spec: ""
- acceptance:
  - 主 bundle gzip 后 < 200KB
  - npm run build 通过
  - 浏览器主流程页面切换无白屏
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

## T-003: 清理前端 console.log / 调试输出
- status: backlog
- category: lint
- auto_approve: true
- spec: ""
- acceptance:
  - npm run build 通过
  - grep -rn "console\\.log" frontend/src 命中数为 0（保留 console.error 和 console.warn）
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
