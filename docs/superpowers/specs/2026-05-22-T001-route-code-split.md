# T-001 Spec: Dashboard 主 chunk 体积超 500KB，做路由级 code-split

- created_at: 2026-05-22
- category: refactor
- 状态：spec_drafted，等人审

---

## 背景与问题

`npm run build` 输出报警：

```
dist/assets/index-DIV6atpX.js            1,190.31 kB │ gzip: 378.48 kB
dist/assets/Dashboard-DflVBbQF.js        1,468.86 kB │ gzip: 429.35 kB
[plugin builtin:vite-reporter]
(!) Some chunks are larger than 500 kB after minification.
```

排查发现：

1. **路由已经在做 dynamic import**（`frontend/src/router/index.ts` 每个 route 都是 `() => import(...)`），所以"路由级 code-split"这个任务标题描述的方案其实**已实施**，瓶颈不在这。
2. 真正的体积来自**未拆分的 vendor 库**：
   - `echarts` ^6.1.0（独立约 800KB+）
   - `@ant-design/charts` ^2.6.7（依赖 g6/g2，独立 400KB+）
   - `element-plus` ^2.14.0（独立 600KB+，按需引入未启用）
3. Dashboard 是首屏 + 同时引用了 echarts 和 ant-design charts，所以它的 chunk 最大。`index-DIV6atpX.js` 是 vendor 全部塞进入口造成。

任务原 acceptance「主 bundle gzip 后 < 200KB」在当前依赖体量下做不到 —— echarts 单库 gzip 就接近这个数。需要重新校准目标。

---

## 推荐方案（任选其一，请人审决定）

### 方案 A（推荐，工作量小）：vite manualChunks 切 vendor

修改 `frontend/vite.config.ts`，加 `build.rollupOptions.output.manualChunks`：

```ts
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        'vendor-vue': ['vue', 'vue-router', 'pinia'],
        'vendor-echarts': ['echarts'],
        'vendor-antd-charts': ['@ant-design/charts'],
        'vendor-element-plus': ['element-plus'],
      },
    },
  },
  chunkSizeWarningLimit: 800, // echarts 单库就接近这个数，500 太严
},
```

预期结果：
- 主入口 `index.js` 降到 50-100KB gzip（仅含 router/app 框架）
- 各 vendor 拆成独立 chunk，首次访问按需下载
- Dashboard chunk 降到 < 100KB gzip（仅业务代码）

**风险**：
- 改动 `vite.config.ts`，policy 红线只禁 `pyproject.toml build-system / package.json scripts`，**vite.config.ts 不在红线内** ✓
- 只是构建产物分块策略变化，**不影响运行时行为**

**验收**：
- `npm run build` 通过
- 主入口 chunk gzip < 100KB
- 各 vendor chunk 独立存在
- 浏览器打开 Dashboard、Bills、Settings 等关键页无 404 / 白屏

### 方案 B（彻底，但工作量大）：element-plus 按需引入 + echarts treeshaking

- 引入 `unplugin-vue-components` 和 `unplugin-auto-import`，element-plus 改按需
- echarts 改用核心包 + 按图表类型 register
- 需要逐个改 `.vue` 文件的 import

工作量约 1-2 天，本任务不建议走这条 —— 单开一个 T-XXX 排期。

### 方案 C：放弃严格阈值，只做合理拆分

接受 vendor 不可压缩的现实，把 acceptance 改成"无单 chunk 超 1MB（gzip 300KB）"，只做方案 A 的 manualChunks。

---

## 待人审决策

请回复明确选哪个方案 + 是否同意调整 acceptance（200KB 阈值不现实，建议改 100KB 入口 + 800KB chunk warning）。

审完把 `T-001` 状态从 `spec_drafted` 改 `approved`，并把本 spec 的方案标号写到任务 `chosen_plan: A/B/C` 字段。
