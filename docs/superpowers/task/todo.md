---
enabled: true
auto_merge_main: true
---

# 任务队列

云端 cron agent 每次 tick 读取本文件，按状态机选一条任务执行。
**人类操作**：审完 spec 后把任务状态从 `spec_drafted` 改为 `approved` 即可放行。
暂停整个循环：把上面 frontmatter 的 `enabled` 改 `false`。

任务条目格式见模板。已完成的任务由 agent 自动从这里移到 `done.md`。

---

## 状态机

```
backlog → (auto_approve 命中) → approved
backlog → (写 spec) → spec_drafted → (人审) → approved
approved → (实施) → in_progress → done
                              ↘ blocked （3 次失败）
```

---

## 任务模板（复制改用）

```markdown
## T-XXX: 任务标题
- status: backlog
- category: bug-fix | feature | refactor | docs | test | lint | dep-patch | dead-code
- auto_approve: false
- spec: ""
- acceptance:
  - 后端 pytest 全过
  - 前端 npm run build 通过
  - 具体业务验收点
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0
```

---

## 进行中 / 待审

## T-018: 宠物详情页补消费记录表格
- status: in_progress
- category: feature
- auto_approve: false
- spec: "docs/superpowers/specs/2026-05-22-T018-pet-detail-cost-table.md"
- acceptance:
  - 后端 pytest 全过
  - 前端 npm run build 通过
  - PetDetail.vue 展示该宠物的消费记录分页表格（日期 / 分类 / 金额 / 备注）
  - 支持分页，与客户详情页消费时间线功能对称
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: "2026-05-22T23:25:00+08:00"
- attempt: 1

## T-019: 404 页面 — 通配路由 + 友好提示
- status: approved
- category: feature
- auto_approve: false
- spec: "docs/superpowers/specs/2026-05-22-T019-404-page.md"
- acceptance:
  - 前端 npm run build 通过
  - 访问 /abc /xyz/123 等不存在路径时展示设计统一的 404 页面
  - 含"返回首页"按钮可跳回 /dashboard
  - 侧边栏 / 顶部导航保持正常显示
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

## T-020: 侧边栏移动端响应式折叠
- status: approved
- category: feature
- auto_approve: false
- spec: "docs/superpowers/specs/2026-05-22-T020-mobile-sidebar.md"
- acceptance:
  - 前端 npm run build 通过
  - 视口宽度 < 768px 时侧边栏默认折叠为图标模式或隐藏
  - 顶部显示 hamburger 按钮可切换侧边栏展开/收起
  - 不破坏桌面端 1440px+ 现有布局
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

## T-021: Dashboard 日期范围选择器
- status: approved
- category: feature
- auto_approve: false
- spec: "docs/superpowers/specs/2026-05-22-T021-dashboard-date-range.md"
- acceptance:
  - 后端 pytest 全过
  - 前端 npm run build 通过
  - Dashboard 顶部增加日期范围选择组件，默认当月
  - 选择范围后全部卡片 / 图表联动刷新
  - 后端现有 stats API 已支持 start/end 参数（仅需前端联调，后端不动）
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

## T-022: 数据导出 — 客户 & 账单 CSV 导出
- status: approved
- category: feature
- auto_approve: false
- spec: "docs/superpowers/specs/2026-05-22-T022-csv-export.md"
- acceptance:
  - 后端 pytest 全过
  - 前端 npm run build 通过
  - 客户列表页增加"导出"按钮，下载当前筛选条件下的 CSV
  - 账单列表页增加"导出"按钮，下载当前筛选条件下的 CSV
  - CSV 含中文表头，Excel 打开不乱码（BOM 前缀）
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

---

## blocked（阻塞中）

## T-026: 后端 pydantic-core 依赖 minor 升级 v2.46.4 → v2.47.0
- status: blocked
- category: dep-patch
- auto_approve: false
- spec: "docs/superpowers/specs/2026-05-22-T026-pydantic-core-minor-upgrade.md"
- acceptance:
  - 后端 pytest 全过
  - `uv lock` 后 pydantic-core 版本升至 2.47.0
- blocked_reason: "PyPI 上 pydantic-core v2.47.0 尚未发布，当前最新 2.46.4"
- created_at: 2026-05-22
- last_run: "2026-05-22"
- attempt: 0

---

## backlog（待执行）

## T-027: 后端 app/seed.py 模块补测试（覆盖率 0% → ≥70%）
- status: backlog
- category: test
- auto_approve: true
- spec: ""
- acceptance:
  - 后端 pytest 全过
  - `app/seed.py` 模块覆盖率 ≥ 70%
  - 不修改 seed.py 业务源码
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0

## T-025: 后端 click 依赖 patch 升级 v8.4.0 → v8.4.1
- status: backlog
- category: dep-patch
- auto_approve: true
- spec: ""
- acceptance:
  - 后端 pytest 全过
  - `uv lock` 后 click 版本升至 8.4.1
- blocked_reason: ""
- created_at: 2026-05-22
- last_run: ""
- attempt: 0