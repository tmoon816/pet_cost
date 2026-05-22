# T-017 Spec: 全局搜索 — 顶部搜索框接线

- created_at: 2026-05-22
- category: feature
- 状态：spec_drafted，等人审

---

## 背景

`App.vue` 顶部有一个 `<el-input placeholder="搜索账单、宠物、客户..." style="width: 300px;">` —— **但没有任何事件绑定、没有任何 search 方法、没有任何后端接口**。纯摆设。

## 方案设计

### 后端：新增 `GET /api/v1/search?q=`

返回统一格式的混合搜索结果：

```json
{
  "results": [
    { "type": "customer", "id": 1, "title": "张伟", "subtitle": "13800001001", "url": "/customers/1" },
    { "type": "pet", "id": 3, "title": "毛毛", "subtitle": "柯基 · 主人: 张伟", "url": "/pets/3" },
    { "type": "cost", "id": 15, "title": "粮食 ¥120.50", "subtitle": "2026-05-10 · 毛毛", "url": "/bills" }
  ]
}
```

搜索范围：
- customer：LIKE `name` OR `phone`
- pet：LIKE `name`，联表返回主人名
- cost：LIKE `note`，联表返回 pet_name

每组 limit 5，总共最多 15 条返回。

### 前端：App.vue 接线

1. 搜索框 `@input` debounce 300ms 后调 `/api/v1/search?q=xxx`
2. `q` 为空时清空结果面板
3. 结果面板用 `<el-popover>` 或 `<div>` 下拉，分三组展示（客户 / 宠物 / 账单），每组带标题
4. 点击结果 → `router.push(url)` 跳转
5. `@keyup.enter` → 跳第一个结果

## 不涉及

- 不建全文索引 / ElasticSearch（数据量小，LIKE 足够）
- 不改现有 CRUD 接口
- 不搜分类 / 预算（量太少没意义）

## 风险

极低。加一个只读 API + App.vue 绑事件，不碰现有业务逻辑。

## 验收

- `GET /api/v1/search?q=张` 返回含 type/url 的混合结果
- 搜索框输入 → 下拉面板展示客户/宠物/账单分组
- 点击跳详情页，回车跳第一个
- 空输入或清空 → 面板消失
- pytest 全过，npm build 通过