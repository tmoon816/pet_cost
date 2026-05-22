# T-018 Spec: 宠物详情页补消费记录表格

- 日期：2026-05-22
- 分类：feature
- 状态：**待审批**

## 一句话

PetDetail.vue 目前只有宠物基本信息，缺少该宠物的消费记录表格。对标 CustomerDetail 已有的「消费时间线」，补一张分页表格。

## 方案

### 后端
**不动**。现有 `GET /api/v1/costs?pet_id=X` 已支持按宠物筛选（costs.py/crud/cost.py 已实现）。

### 前端
PetDetail.vue 新增「消费记录」el-card：
- 表格列：日期 (occurred_on)、服务项目 (category_code → label via categoryStore)、金额 (amount)、备注 (note)
- 分页：page_size=10，el-pagination
- 空状态：「该宠物暂无消费记录」

## 验收
- pytest 93 全过（不新增）
- npm run build 通过
- PetDetail.vue 展示分页消费表格
- 宠物有消费记录时正常展示，无消费记录时显示空状态

## 不做
- 不加搜索/筛选（保持简单）
- 不改后端任何代码