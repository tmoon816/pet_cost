---
name: 长任务循环安全策略
purpose: 定义云端 cron agent 在自动批准任务、实施任务时的红线与边界
last_updated: 2026-05-22
---

# 长任务循环安全策略

本文件是云端 agent 行为约束。每次 cron tick 必须读取本文件再决定行动。

---

## 1. 自动批准白名单（status: backlog → approved 不需要人批）

满足下列**所有**条件的任务才能自动批：

- `auto_approve: true` 显式标记
- `category` 在以下集合内：
  - `docs`：仅改 `*.md`、注释、错别字、链接
  - `test`：仅新增测试用例（不改业务源码）
  - `lint`：格式化、ESLint/ruff 自动修
  - `dep-patch`：依赖 patch 版本升级（1.2.3 → 1.2.4）
  - `dead-code`：证据确凿的未引用导出/变量删除
- 任务 `acceptance` 字段非空
- 不涉及红线（见第 3 节）

不满足任一条件 → agent 必须写 spec，状态改 `spec_drafted`，停下来等人批。

---

## 2. 必须人批（status: backlog → spec_drafted → 等用户改 approved）

下列任务一律必须先写 spec：

- 新业务功能 / 新页面 / 新模块
- 数据库迁移（新表、改字段、改索引）
- API schema 变更（新增 / 删除 / 改类型字段）
- 跨多文件的重构
- 依赖 minor / major 版本升级
- 性能优化（涉及架构改动）
- 任何会改变现有 API 行为的改动

---

## 3. 红线（永远不做）

- ❌ 合并到 main 分支（只能 push 到 dev）
- ❌ `git push --force` / `--force-with-lease`
- ❌ `--no-verify` 跳过 hook
- ❌ 修改 `.git/`、CI 配置、`pyproject.toml` 的 build-system、`package.json` 的 scripts 段
- ❌ 删除 `docs/superpowers/specs/`、`docs/superpowers/plans/` 下任何已有文件
- ❌ 提交含密钥、token、`.env`、credentials 的文件
- ❌ 在主分支或 dev 上 `git reset --hard`
- ❌ 跨任务实施（一次 tick 只处理一条任务）

---

## 4. 失败处理

- 实施失败重试上限：3 次
- 3 次仍失败 → 状态改 `blocked`，`blocked_reason` 写清楚根因（不只是错误信息），等人介入
- 不要回滚已 push 的 commit（让人审）
- 不要为了让测试过去而改测试（fix 代码，不 fix 测试，除非测试本身错）

---

## 5. 巡检任务生成规则（第五步）

每次 tick 末尾必须扫一遍仓库，往 todo.md backlog 段追加新任务条目（不实施，只追加）。
信号源：

- `cd frontend && npm outdated`：依赖过期 → 写「升级 X 至 Y」任务
- `cd backend && uv tree --outdated`：同上
- `grep -rn "TODO\|FIXME\|XXX" frontend/src backend/app`：技术债 → 一条 TODO 一个任务（按文件聚合，不要刷屏）
- `cd backend && uv run pytest --cov=app --cov-report=term-missing`：覆盖率 < 70% 的模块 → 写补测试任务
- 重复 commit 后 lint warning 数 → 写清理任务

**去重要求**：追加前必须搜 todo.md 和 done.md 全文，发现相同主题任务（无论状态）就跳过，不要重复写。

---

## 6. Kill switch

todo.md 头部 yaml frontmatter：

- `enabled: false` → agent 立即退出，仅写 log

人类可以随时编辑 todo.md frontmatter 来暂停整个循环，无需删任务。
不设每日上限——资源充足，节流靠 cron 触发频率本身。
