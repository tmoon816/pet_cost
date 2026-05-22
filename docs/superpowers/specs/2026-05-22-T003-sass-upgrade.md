# T-003 Spec: sass 1.99.0 → 1.100.0 升级

- created_at: 2026-05-22
- category: feature (非 patch，需评估)
- 状态：direct_approved（人审直接批，跳过 spec_drafted）

---

## 背景

`npm outdated` 显示 `sass 1.99.0 → 1.100.0`。sass 是前端 devDependency，仅用于编译 `.scss` 文件（`npm run build` 时调用），不在运行时加载。

## 影响面

sass 在项目中仅作为 Vite 的 CSS 预处理器编译链一环。当前前端使用 scss 文件不多（主要样式在 `index.css` 和 element-plus 自带），sass 版本变更主要是编译器本身的 bugfix 和性能优化。

## 风险评估

- sass 1.100.0 是 1.99 系列的延续，非 major breaking
- 项目 SCSS 用量少，编译行为变化风险极低
- 唯一风险：新版本可能引入新 warning 或被废弃的语法兼容提示

## 实施

```
cd frontend && npm install sass@1.100.0 --save-dev
```

## 验收

- `npm run build` 通过，无新增编译错误或 warning（除已有 rolldown `INVALID_ANNOTATION` 外）
- `npm ls sass` 显示 sass@1.100.0
- package.json diff 仅 sass 一行被改 + package-lock.json 同步