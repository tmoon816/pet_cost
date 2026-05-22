# T-021 Spec: Dashboard 日期范围选择器

- 日期：2026-05-22
- 分类：feature
- 状态：**待审批**

## 一句话

Dashboard 顶部加日期范围选择器，联动所有卡片/图表刷新。

## 方案

### 后端
**不动**。现有 stats API 已支持 start/end query 参数：
- `/stats/summary?start_date=...&end_date=...`
- `/stats/by-category?start_date=...&end_date=...`
- `/stats/by-month?start_date=...&end_date=...`
- `/stats/by-pet?start_date=...&end_date=...`
- `/stats/customer-acquisition?year=...&month=...`（不受日期范围影响）
- `/stats/dormant-customers?days=...`（不受日期范围影响）

### 前端
- Dashboard.vue 顶部加 `el-date-picker`（type="daterange"，默认当月第一天到今天）
- 日期变更后重新拉取 statsApi 全部接口，传入 start_date / end_date
- customer-acquisition 和 dormant-customers 卡片不随日期范围变化（两个独立口径）
- 加 loading 遮罩，数据刷新期间显示骨架

## 验收
- npm run build 通过，pytest 93 全过
- Dashboard 顶部显示日期范围选择器，默认当月
- 切换日期范围后 summary / by-category / by-month / by-pet 四张卡片/图表联动刷新
- customer-acquisition 和 dormant-customers 卡片不随日期变化

## 不做
- 后端不动（stats API 已有日期参数，仅前端联调）
- 不满月、跨月范围别做特殊校验（由后端 SQL 处理）