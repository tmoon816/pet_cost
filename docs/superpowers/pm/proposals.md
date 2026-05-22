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

## P-001: Dashboard 新增「Top 10 高价值客户」卡片
- status: proposed
- created_at: 2026-05-22
- vision_anchor: "vision.md §2.3「月底，老板想看……Top 10 高价值客户」"
- user_scenario: "月底，小店老板想在 Dashboard 一眼看出本店最值钱的 10 个客户是谁，决定是否专门维护（送个小礼/发条问候），而不用自己去客户列表按金额排序再翻页"
- problem: "vision §2.3 明确列出『Top 10 高价值客户』是月底关键决策场景，但 Dashboard 目前只有新客 vs 回头客（T-009）和久未到店（T-010）两张运营卡片，缺少『谁最值得维护』的正向视角；客户列表虽支持按累计消费排序（T-015）但需要主动点进去翻，不在打开系统的第一屏"
- mvp: "Dashboard 增加一张『高价值客户 Top 10』卡片，后端复用现有客户聚合接口加 order_by=total_spent desc&limit=10，前端列出：排名、客户名、累计消费、订单数；点击行跳转客户详情页。不做时间窗口筛选（v1 直接全周期累计）"
- why_now: "T-007 客户聚合卡片、T-015 按金额排序已经把数据基础铺好了，Dashboard 的『回头客视角』三张卡（新客回头/久未到店/高价值）刚好补齐 vision §2.3 的月底场景，是上一轮 done 的自然延伸"
- size: small
- linked_task: ""
- reject_reason: ""

## P-002: 「久未到店」预警列表直接显示联系方式，让流失预警可行动
- status: proposed
- created_at: 2026-05-22
- vision_anchor: "vision.md §2.4「维护客情：老板能从客户档案点开看完整的消费历史……不用脑子记」+ §4「流失预警卡片」"
- user_scenario: "老板早上打开 Dashboard 看到『3 个月未到店老客』列表里有 8 个名字，想立刻挑 2 个发微信问候『最近来洗澡吗？』。现在他要逐个点进客户详情页才能看到手机号，操作链路 3 步，实际放弃率高"
- problem: "T-010 已经做了流失预警列表，但只显示客户名和距今天数，老板看到名字之后『下一步要联系』的动作没接上；vision §2.4 的核心是『不用脑子记就能维护客情』，少这一步信息就让预警卡变成纯展示"
- mvp: "在已有的『久未到店老客』列表每行追加：手机号（脱敏后 4 位）+ 一个『复制手机号』按钮 / 或显示上次消费的项目名（提示『上次做的是 XX，可以问问要不要再约一次』）。后端接口已经有 customer 表全字段，前端只需要在已有列表组件里加 1-2 列"
- why_now: "T-010 上轮刚 done，列表骨架已存在，加列比新做一张卡成本低 10 倍；同时这是 vision §4 明确点名的『流失预警』功能链路收尾，不补上这一步 T-010 的价值发挥不出来"
- size: small
- linked_task: ""
- reject_reason: ""

---

## 已处理（accepted / rejected / deferred 的提案搬到这里）

(暂无)
