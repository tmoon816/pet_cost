# T-020 Spec: 侧边栏移动端响应式折叠

- 日期：2026-05-22
- 分类：feature
- 状态：**待审批**

## 一句话

视口 < 768px 时侧边栏默认折叠，顶部显 hamburger 按钮切换展开/收起。

## 方案

### 前端
- App.vue 新增 `isSidebarCollapsed` ref（默认 = window.innerWidth < 768）
- 监听 `window.resize`（debounce 200ms），同步 collapsed 状态
- 侧边栏：`v-show="!isSidebarCollapsed"` + 展开时加 overlay（移动端点击 overlay 收起）
- 顶部 header 左侧加 hamburger 图标按钮（`@click="toggleSidebar"`）
- Element Plus el-icon 用 `Fold` / `Expand` 图标
- PC 端（≥768px）保持原样，不受影响
- 状态写入 localStorage，刷新保持

### 后端
**不动**。

## 验收
- npm run build 通过
- <768px：侧边栏默认隐藏，hamburger 按钮可见
- 点击 hamburger 展开/收起侧边栏
- 点击内容区 overlay 收起侧边栏
- ≥768px：侧边栏始终展开，hamburger 隐藏
- 桌面端布局无任何变化

## 不做
- 不做侧边栏缩成纯图标模式（本轮目标仅是折叠/展开）