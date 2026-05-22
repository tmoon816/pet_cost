# T-005: vue-router 4.6.4 → 5.0.7（major 升级）spec

## 背景

`cd frontend && npm outdated` 自 5/21 起持续报：
```
vue-router 4.6.4 → 5.0.7（major）
```
当前项目用 vue-router 4.x，配合 Vue 3 + Vite 8 + Pinia + Element Plus 工作正常。本次为 major 跨版本升级，policy.md 第 2 节要求必须人审。

## 当前用法盘点

`grep -rn "vue-router\|useRouter\|useRoute\|router\." frontend/src` 共 26 处。落到 vue-router 提供的 API 仅 4 个：

1. `frontend/src/router/index.js`：
   - `createRouter`、`createWebHashHistory`
   - 路由配置：所有 13 个页面均用懒加载 `component: () => import('@/views/.../X.vue')`
   - `router.beforeEach` 全局守卫：设置 `document.title`
2. `frontend/src/views/customers/CustomerList.vue` 等业务页：`useRouter()` + `router.push('/customers/123')`
3. `frontend/src/views/customers/CustomerDetail.vue` 等详情页：`useRoute()` 取 `route.params.id`
4. `App.vue` / `MainLayout.vue` 模板：`<router-view />`、`<router-link to="...">`

**没有用到**：动态路由 `router.addRoute`、命名视图 `components: { default, sidebar }`、模式自定义 `RouterScrollBehavior`、`navigationGuard` 复杂返回值、`onBeforeRouteUpdate`/`onBeforeRouteLeave` Composition API。

## 升级潜在 breaking change 评估

vue-router 5.x 相对 4.x（基于官方 migration guide 与 release notes，需在实施 PR 时再核实最新版）逐项 check：

| breaking | 是否影响 | 备注 |
|---|---|---|
| 移除 `createWebHashHistory` 别名 / `createMemoryHistory` 改名 | ⚠️ 需核 | 本项目用 `createWebHashHistory`，若 5.x 重命名要改 `router/index.js` |
| 全局守卫返回值 `next()` 调用方式变化 | ⚠️ 需核 | 本项目 `beforeEach` 只 `next()` 无业务返回值，影响小 |
| `<router-link>` 的 `tag` / `event` props 移除 | ✅ 不受影响 | 模板里只用 `to` |
| `useRoute()` / `useRouter()` 返回类型签名 | ✅ 不受影响 | 仅读 `params.id` 和调 `push` |
| TypeScript 类型重构 | ✅ 不受影响 | 项目是 JS 不是 TS |
| 历史 fallback 行为 / hash 模式渲染时机 | ⚠️ 需核 | hash 路由切换无白屏要全量回归 |
| Vue 3 minimum version | ✅ 已满足 | package.json 用 vue@^3.x |
| 移除 `*` 通配符路由，必须用 `/:pathMatch(.*)*` | ⚠️ 需核 | 本项目无 404 路由，但建议加 |
| `Router.options.scrollBehavior` 签名变化 | ✅ 不受影响 | 未配置 |

## 实施步骤（人审批准后由后续 tick 执行）

1. `cd frontend && npm install vue-router@5.0.7 --save`，提交 package.json + package-lock.json
2. 严格按本 spec 上表逐条 check `router/index.js`：
   - 若 `createWebHashHistory` 在 5.x 改名，按官方文档替换
   - `beforeEach` 守卫保持 `(to, from) => { document.title = ... }` 形式
3. 启动 dev server `npm run dev`，浏览器主流程冒烟（参考 CONTRIBUTING.md §2.3）：
   - `/` → `/dashboard` 重定向
   - 客户列表 → 客户详情（参数路由）→ 返回
   - 宠物列表 → 宠物详情
   - 订单列表（含筛选）
   - 统计页 / 服务项目 / 预算页
   - 侧边栏所有菜单切换无白屏
4. 跑 `npm run build` 必须通过
5. 跑 `cd backend && uv run pytest` 67 全过（保险，理论上前端升级不影响）

## 验收

- npm run build 通过
- npm ls vue-router 显示一棵 vue-router@5.0.7
- 浏览器主流程冒烟全过，所有现有路由打开无报错、无白屏、无 console error
- 没有顺手升级其他依赖（package.json diff 应只触 vue-router 一行 + package-lock.json）

## 不做

- 不在本 PR 顺带升级 vite/vue/element-plus/pinia 等其他依赖（按 policy.md：跨依赖升级要单独 spec）
- 不引入 vue-router 5.x 才有的新特性（typed routes、新的 scrollBehavior 等），仅保持现有功能等价

## 风险与回滚

major 升级风险中等。若任一冒烟点失败：
- 退回到当前 4.6.4：`npm install vue-router@4.6.4 --save && npm install`
- 重新提交 revert commit；本任务状态改 blocked 写清楚 breaking 点等人介入
- 不强推、不留半截升级
