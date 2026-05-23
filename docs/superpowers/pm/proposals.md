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

(空)

---

## 已处理（accepted / rejected / deferred 的提案搬到这里）

## P-007: 打烊前 5 分钟录入提速三件套
- status: accepted
- created_at: 2026-05-24
- accepted_at: 2026-05-24
- vision_anchor: "vision.md §2.2「打烊前：老板花 5 分钟而不是 30 分钟把今天的消费录入系统」"
- user_scenario: "晚上 9 点关门，老板要把当天 10~30 笔服务订单录完。最痛三件事：固定价服务每次手输金额、一个客户带多只宠物洗澡得逐条录、Dashboard 默认本月范围要切到「今天」才能核对今日营收"
- problem: "1) 录单每次手输金额，洗澡/美容这种固定价服务也要重复敲；2) 多宠物家庭批量服务时，同金额同分类要录 N 次；3) 打烊对账时 Dashboard 默认本月范围，没有快速看「今日」的视图"
- mvp: |
  三个独立但互补的小动作（可分别落地）：
  A. 服务项目支持 default_amount，选完分类自动填金额（手动改过则不覆盖）
  B. CostFormDialog 宠物字段支持多选，提交时拆 N 条同金额记录（后端加 batch 接口，事务原子）
  C. Dashboard 顶部加固定的「今日营业」小卡（金额/订单数/明细入口），与日期筛选解耦
- why_now: "打烊场景是当前录入摩擦最重的环节，每天都被触发一次、每条订单都被触发；改完直接每天省时间，复合收益高。vision §2.2 是 v1 的核心目标场景之一"
- size: medium
- linked_task: "T-028, T-029, T-030"

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

## P-003: 消费新增「保存并继续」——打烊前连续录入提速
- status: implemented
- created_at: 2026-05-22
- implemented_at: 2026-05-24
- implemented_in: "CostFormDialog.vue:235-265 saveAndContinue + 模板 :351-358「保存并继续」按钮（仅新增态显示）；保留客户/宠物/分类/日期，清空金额和备注，聚焦金额框"
- vision_anchor: "vision.md §2.2 打烊前 5 分钟目标"
- size: small

## P-006: 客户列表 & 详情页增加「新客 / 回头客 / VIP」徽标
- status: implemented
- created_at: 2026-05-23
- implemented_at: 2026-05-24
- implemented_in: "后端 schemas/customer.py CustomerListItem/CustomerSummary 加 visit_count + customer_type；crud/customer.py classify_customer() 阈值在 core/config.VIP_THRESHOLD（默认 5）；前端 CustomerList 类型列升级为新客/回头客/VIP 三色 tag，CustomerDetail 顶部加客户类型徽章卡（4 列布局）"
- vision_anchor: "vision.md §4 回头客标签"
- size: small

## P-005: 客户 & 宠物档案增加自由备注字段（已 rejected）
- status: rejected
- created_at: 2026-05-23
- rejected_at: 2026-05-24
- reject_reason: "提案前置调研有误。复核后 Customer 模型已有 note TEXT 字段（models/customer.py:18，CustomerList 编辑弹窗已是 textarea），Pet 模型同样已有 note 字段（models/pet.py:25，PetDetail.vue:196/219-220 + PetList.vue:195-196 已展示和编辑）。两端「自由备注」均已落地，本提案无新功能可做，归入误提。"
- vision_anchor: "vision.md §2.4「不用脑子记」——已被现有 note 字段满足"
- size: small
