---
pm_enabled: true
---

# 产品提案池

PM cron agent 每次 tick 会读取本文件，往 Backlog 段追加新提案。
**这里的提案不会被自动实施**。要进入开发队列，必须由你手动操作（见下方流程）。

---

## 提案状态机

```
proposed       ← PM cron 新写的，等你看
accepted       ← 你认可，准备转化为开发任务
rejected       ← 你不要，留作记录避免 PM 反复提同一个
deferred       ← 暂时不做，PM 知道这事被你看过了
```

---

## 提案 → 开发任务的流程（只有你能做）

1. 看到 proposed 提案，决定：
   - 想做 → status 改 `accepted`
   - 不想做 → status 改 `rejected`，写一句 `reject_reason`
   - 以后再说 → status 改 `deferred`
2. 对 `accepted` 的提案，**手动**在 `todo.md` Backlog 段创建一条对应的 T-XXX 任务
   （可以借助 Claude 帮你写任务条目，但 PM cron agent 自己不会做这步）
3. todo.md 任务写完后，可以在本文件提案条目里加一行 `linked_task: T-XXX` 方便追溯

---

## 提案模板

```markdown
## P-XXX: 提案标题
- status: proposed
- created_at: 2026-XX-XX
- vision_anchor: "vision.md 第 X 节的哪句话"
- user_scenario: "谁在什么场景下遇到了什么"
- problem: "现在的痛点 / 缺口"
- mvp: "最小可落地版本是什么样"
- why_now: "为什么现在做，而不是以后"
- size: small | medium | large
- linked_task: ""
- reject_reason: ""
```

---

## Backlog（PM cron 写在这里）

(暂无)

---

## 已处理（accepted / rejected / deferred 的提案搬到这里）

(暂无)
