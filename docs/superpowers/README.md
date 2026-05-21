# superpowers 目录说明

本目录承载项目的「自驱循环」基础设施，由两条独立的云端 cron 协作。

## 目录结构

```
docs/superpowers/
├── pm/                # 产品提案 cron
│   ├── cron-prompt.md   # 云端定时任务的提示词
│   ├── vision.md        # 产品锚点（不填，PM 不工作）
│   ├── proposals.md     # 提案池，PM 写入；你审完决定 accept/reject
│   └── log.md           # PM 运行日志
├── task/              # 开发执行 cron
│   ├── cron-prompt.md   # 云端定时任务的提示词
│   ├── policy.md        # 安全策略（自动批白名单、红线）
│   ├── todo.md          # 任务队列（含 enabled / auto_merge_main 开关）
│   ├── done.md          # 已完成任务归档
│   └── log.md           # 执行运行日志
├── specs/             # 设计文档（task cron 写入；人审）
└── plans/             # 实施计划（人写为主）
```

## 两个角色

- **PM cron**（频率：每周 1 次推荐）
  扮演产品经理，基于 `pm/vision.md` 提产品提案，写入 `pm/proposals.md`。
  **不写代码、不改 todo**。决策权完全在你。

- **Task cron**（频率：每 3 小时一次推荐）
  扮演执行工程师，从 `task/todo.md` 取任务，写代码 / 测试 / push。
  自动批白名单内的任务（lint/docs/test/dep-patch/dead-code）会一路合到 main；
  其他任务先写 spec 等你审。

## 完整链路

```
PM cron 周期触发
   ↓
读 pm/vision.md → 产出 1-2 条提案 → 写 pm/proposals.md
   ↓
你看 proposals.md：accepted / rejected / deferred
   ↓
accepted 提案 → 你手动转化为 task/todo.md 的 T-XXX
   ↓
Task cron 三小时触发 → 取任务 → 实施 → push dev
   ↓
auto_approve 或 merge_to_main_after 任务 → 自动 ff-only 合并 main
```

## 你随时可以做的

| 操作 | 方法 |
|---|---|
| 暂停 PM 提案 | 改 `pm/proposals.md` frontmatter `pm_enabled: false` |
| 暂停 Task 实施 | 改 `task/todo.md` frontmatter `enabled: false` |
| 暂停自动合 main | 改 `task/todo.md` frontmatter `auto_merge_main: false` |
| 加新任务 | 编辑 `task/todo.md` Backlog 段，按模板追加 |
| 审 spec | 看 `specs/` 下文件，把 `task/todo.md` 对应任务 status 改 approved |
