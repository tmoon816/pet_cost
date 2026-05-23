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
implemented    ← 已落地到代码（手动或随其他任务一起做掉）
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
- linked_task: "T-026"
- reject_reason: ""
```

---

## Backlog（PM cron 写在这里）

## P-003: 消费新增「保存并继续」——打烊前连续录入提速
- status: accepted
- created_at: 2026-05-22
- vision_anchor: "vision.md §2.2「打烊前：老板花 5 分钟而不是 30 分钟把今天的消费录入系统，不再事后翻小票对账」"
- user_scenario: "打烊前，老板坐在电脑前要把今天 8-12 条服务订单录入系统。现在每录一条流程是：点「新增消费」→ 弹窗打开 → 选客户 → 选宠物 → 选分类 → 填金额 → 点「确定」→ 弹窗关闭 → 再点「新增消费」→ 弹窗又开 → 重复。弹窗的开-关-开动画和重新选客户是最大耗时来源，录 10 条实际花 15+ 分钟（测下来每条约 90 秒）。"
- problem: "CostFormDialog 提交成功后强制关闭弹窗、清空全部表单状态，连续录入场景下反复打开弹窗 + 重新选客户/宠物是最大的操作摩擦。vision §2.2 的 5 分钟目标靠现有交互还不够——T-014 解决了『找到最近客户』的查找时间，但录多条时的录入时间本身仍是瓶颈。"
- mvp: "CostFormDialog 提交按钮右加一个「保存并继续」按钮：点击后提交 API，成功则 toast 提示『已保存』，表单不关闭、客户/宠物保持选中、金额清空并 focus，老板只需改金额再点一下即可连续录入同一客户的多个服务项。最后一个记录点原来的「确定」按钮关闭弹窗。后端零改动，纯前端 Dialog 交互逻辑（handleSubmit 加一个 stayOpen 参数）。"
- why_now: "T-014（最近 5 个客户快选）上周 done，已经把『找到客户』的效率提升了，但只解决了录入链路的前半段。现在补『连续录入』的后半段，vision §2.2 的 5 分钟目标才能真正落地——这是 T-014 的自然延伸和收尾。"
- size: small
- linked_task: ""
- reject_reason: ""

## P-006: 客户列表 & 详情页增加「新客 / 回头客 / VIP」徽标，把「回头客标签」从数字层下沉到行级
- status: proposed
- created_at: 2026-05-23
- vision_anchor: "vision.md §4「围绕『客户回头率不清晰』这个核心痛点，做小增量：客户消费历史聚合、回头客标签、流失预警卡片」——『回头客标签』直接点名"
- user_scenario: "接待时，张三推门进来，老板在系统里搜到档案，当前页面显示电话 / 累计消费 / 上次到店，但老板要扫一眼数字心算『这是不是回头客』。在客户列表浏览时同样希望一眼分辨——尤其在月底想从列表里挑一批 VIP 发问候，目前只能靠累计消费排序倒推。"
- problem: "T-009 已经在 Dashboard 做了『本月新客 vs 回头客数量』统计卡，T-015 也支持按累计消费排序，但**客户级别**的『回头客 / 新客 / VIP』标签从未下沉到客户列表行和详情页头部。vision §4 把『回头客标签』和『流失预警卡片』并列点名，后者已落地（T-010），前者只完成了数字层，没完成行级层——老板每次看到客户名时还要自己心算分类。注：T-008 已实现『新客/老客』二分（基于 has_cost），本提案是把它扩展为『新客/回头客/VIP』三分。"
- mvp: "后端 customer 列表和详情接口的响应里追加 visit_count（消费记录数）和 customer_type 枚举字段（first_visit=0 单 / returning=2-4 单 / vip=≥5 单；阈值在 core/config 里设常量便于以后调）。前端 CustomerList 表格把现有的『新客/老客』tag 列扩展为三色（灰/蓝/金），CustomerDetail 顶部聚合卡区加一枚徽章。零新增接口，仅扩展现有响应字段。"
- why_now: "T-007（客户聚合卡片）和 T-009（Dashboard 新老客统计）已把消费记录数的聚合逻辑铺好，复用即可；vision §4 当前阶段重点列表（聚合 / 标签 / 预警）里，『回头客标签』在 T-008 只做了二分，VIP 这层未做，是 v1 focus 里最后一块未补的拼图。size=small，前后端各 1-2 个文件。"
- size: small
- linked_task: ""
- reject_reason: ""

---

## 已处理（accepted / rejected / deferred 的提案搬到这里）

## P-001: Dashboard 新增「Top 10 高价值客户」卡片
- status: implemented
- created_at: 2026-05-22
- implemented_at: 2026-05-22
- implemented_in: "commit 0164c3b ✨ feat(P-001~P-004): product proposals implementation；后端 /api/v1/stats/top-customers + 前端 Dashboard.vue Top 10 卡片"
- vision_anchor: "vision.md §2.3「月底，老板想看……Top 10 高价值客户」"
- size: small

## P-002: 「久未到店」预警列表直接显示联系方式
- status: implemented
- created_at: 2026-05-22
- implemented_at: 2026-05-22
- implemented_in: "commit 0164c3b；Dashboard.vue 久未到店表格已加 phone-masked 列 + 复制按钮（Dashboard.vue:411-426）"
- vision_anchor: "vision.md §2.4 + §4 流失预警卡片"
- size: small

## P-004: 客户详情页直达新增消费
- status: implemented
- created_at: 2026-05-22
- implemented_at: 2026-05-22
- implemented_in: "CustomerDetail.vue:376 已加「新增服务」按钮，复用 CostFormDialog + 预填 customer_id"
- vision_anchor: "vision.md §2.4 + §2.1"
- size: small

## P-005: 客户 & 宠物档案增加自由备注字段（已 rejected）
- status: rejected
- created_at: 2026-05-23
- rejected_at: 2026-05-24
- reject_reason: "提案前置调研有误。复核后 Customer 模型已有 note TEXT 字段（models/customer.py:18，CustomerList 编辑弹窗已是 textarea），Pet 模型同样已有 note 字段（models/pet.py:25，PetDetail.vue:196/219-220 + PetList.vue:195-196 已展示和编辑）。两端「自由备注」均已落地，本提案无新功能可做，归入误提。"
- vision_anchor: "vision.md §2.4「不用脑子记」——已被现有 note 字段满足"
- size: small
